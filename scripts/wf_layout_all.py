#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量工作流布局重排 (八条布局规范: 方向 / 端口序 / 净距 / 短线优先 / 功能区块)。

用法:
    python scripts/wf_layout_all.py [关键字...] [--force]
    # 无关键字 = 全部工作流; --force = 已合规的也重排(统一坐标口径)

自动定位本仓根目录, 不依赖工作目录。幂等: 对已合规的布局再跑一次坐标不变。

本轮新增 —— 第 5.1/5.2/5.3 条「功能区块, 按连线关系归区」:
    旧: 全图按「全局依赖深度」整列硬塞 —— 同一深度但互不相干的东西会堆进同一列
        (实测 0032 的 x=1200 一列里塞了 UNETLoader / RandomNoise / KSamplerSelect
         / ComfyMathExpression / FallingTSVideoComponents, 也就是「整个混乱放在一起」)
    新: 先在「主数据图」上做社区发现划出功能区块, 再让**区块带号成为列内排序的主键**,
        使同一区块的节点在所有列里都连续相邻, 视觉上呈一条斜向条带。

区块怎么划(第 5.1 条):
    - 只在主数据图上做(剔除参数节点与 MD/note, 它们是广播总线, 参与划区会把
      不相干的区块粘成一块);
    - 贪心模块度优化(_louvain), 边权 = 两端连线数;
    - < 3 个节点的碎块并入连边权重最大的邻居;
    - 参数节点不划区, 按「消费者最多的那个区块」并入宿主区块(_assign_blocks)。
区块怎么摆(第 5.2 条):
    - 列归属不变(仍按全局依赖深度), 所以第 1 条「输出在左、输入在右」恒成立;
    - 区块只决定**列内纵向顺序**: 排序键 = (区块带号, 期望 y, id);
    - 区块带号优先于短线对齐 —— 宁可某条线长一点, 也不能把同一区块拆散。
      (曾经试过「区块整体平移成水平横带」, 但长链区块如 VAE 主链深度 0→18 横跨
       全图, 横带会被拉到 5000px 以上, 反而更难辨认, 故弃用。)

短线优先(第 4.1/4.2 条, 上一轮加入)仍由「前向扫描 + 列内避让」实现:
    1) 只有一条入线  -> 对齐那个唯一上游(第 4.1 条)
    2) 多入线        -> 对齐「我位于它 outputs[0]」的那一个(第 4.2 条: 第一条最短)
    3) 都不满足      -> 取所有上游中线均值
"""
import json
import math
import os
import sys
from collections import defaultdict
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_REPO, ".agents", "skills", "comfyui"))
import workflow_layout as W  # noqa: E402  (技能自带的估算/检查工具)

WF_DIR = os.path.join(_REPO, "workflows")
X0, XGAP, Y0, VGAP = 40, 80, 40, 60
MAX_COL_H = 2600


def _h(node):
    """节点真实渲染高度(与 layout 同口径)。"""
    est = W.est_size(node)
    own = node.get("size") or [0, 0]
    return max(own[1], est[1])


def _ctr(node):
    """节点垂直中心 —— 用「真实渲染尺寸」(JSON size 与 est_size 取大者)。

    JSON 里的 size 常是旧值(RandomNoise 写 80、实际渲染 148), 拿它算中心会误判
    连线是否水平, 所以与 layout() 用同一套口径。
    """
    est = W.est_size(node)
    own = node.get("size") or [0, 0]
    h = max(own[1], est[1])
    return node["pos"][1] + h / 2.0


def _first_slot_targets(wf):
    """返回 {src_id: dst_id} —— 每个源节点「第一条输出线」指向的下游。

    第一条 = outputs 数组下标最小的、且 links 非空的那个端口,
    与第 2 条「输出端口自上而下对应下游自上而下」一致。

    若第一条指向的是 Reroute(纯转发节点), 继续穿透到它转发出去的第一个
    真实目标 —— Reroute 没有语义, 对齐它等于没对齐; 实测 0023 里
    「Selector → Reroute」这条线因 Reroute 被挤到列尾而偏差 753px。
    """
    nodes = {n["id"]: n for n in wf["nodes"]}
    out_slot = defaultdict(list)          # src -> [(slot, dst)]
    for l in wf["links"]:
        if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
            out_slot[l[1]].append((l[2], l[3]))
    first = {}
    for src, lst in out_slot.items():
        lst.sort()
        dst = lst[0][1]
        seen = set()
        while nodes.get(dst, {}).get("type") == "Reroute" and dst not in seen:
            seen.add(dst)
            nxt = sorted(out_slot.get(dst, []))
            if not nxt:
                break
            dst = nxt[0][1]
        first[src] = dst
    return first, out_slot


# 广播总线型节点: 连向全图各处, 参与划区会把不相干的区块粘成一块(第 5.1 条)
_PARAM_TYPES = {
    "PrimitiveInt", "PrimitiveFloat", "PrimitiveString", "PrimitiveBoolean",
    "PrimitiveNode", "RandomNoise", "KSamplerSelect", "DisableNoise",
    "ManualSigmas", "ComfyMathExpression",
}
# MD 表与 note 各自独占一列, 同样不参与划区
_BUS_TYPES = {"FallingTSMarkDownTable", "MarkdownNote"}


def _louvain(nodes, adj, rounds=50):
    """简化 Louvain(单层贪心模块度优化)。adj[u] = {v: w}。

    只用连线关系划区(第 5.1 条), 不看节点类型/id —— 这是「功能区块」与
    「按类型硬分组」的分水岭: 同为 PrimitiveFloat 的 9 个二采倍数属于同一
    功能块, 而 UNETLoader 与 RandomNoise 虽然深度相同却互不相干。
    """
    m2 = sum(sum(d.values()) for d in adj.values()) or 1.0
    deg = {u: sum(adj[u].values()) for u in nodes}
    comm = {u: u for u in nodes}
    tot = defaultdict(float)
    for u in nodes:
        tot[comm[u]] += deg[u]
    for _ in range(rounds):
        moved = False
        for u in nodes:
            cu = comm[u]
            wc = defaultdict(float)
            for v, w in adj[u].items():
                if v != u:
                    wc[comm[v]] += w
            tot[cu] -= deg[u]
            best, best_gain = cu, 1e-12
            base = wc.get(cu, 0.0) / m2 - tot[cu] * deg[u] / (m2 * m2)
            for c, w in wc.items():
                gain = w / m2 - tot[c] * deg[u] / (m2 * m2) - base
                if gain > best_gain:
                    best, best_gain = c, gain
            comm[u] = best
            tot[best] += deg[u]
            if best != cu:
                moved = True
        if not moved:
            break
    g = defaultdict(list)
    for u in nodes:
        g[comm[u]].append(u)
    return list(g.values())


def _blocks(wf, nodes, links, min_size=3):
    """按连线关系把节点划成功能区块(第 5.1 条)。

    返回 {block_id: [node_id...]}; 参数节点/MD/note 不参与划区, 返回的
    区块里也不含它们(它们由 layout 统一放到「宿主区块」或共享列)。
    """
    core = [i for i in nodes
            if nodes[i]["type"] not in _PARAM_TYPES
            and nodes[i]["type"] not in _BUS_TYPES]
    cs = set(core)
    adj = defaultdict(lambda: defaultdict(float))
    for l in links:
        if len(l) >= 5 and l[1] in cs and l[3] in cs:
            adj[l[1]][l[3]] += 1.0
            adj[l[3]][l[1]] += 1.0
    for i in core:
        adj[i]
    if len(core) < 2:
        return {0: list(core)} if core else {}

    groups = _louvain(core, adj)
    big = [g for g in groups if len(g) >= min_size]
    small = [g for g in groups if len(g) < min_size]

    # 碎片块并入「连边权重最大」的邻居(第 5.1 条), 避免一堆 1~2 节点的碎块
    owner = {i: k for k, g in enumerate(big) for i in g}
    orphans = []
    for g in small:
        w = defaultdict(float)
        for i in g:
            for v, ww in adj[i].items():
                if v in owner:
                    w[owner[v]] += ww
        if w:
            big[max(w, key=w.get)].extend(g)
        else:
            orphans.append(g)
    big.extend(orphans)
    return {k: g for k, g in enumerate(big) if g}


def _assign_blocks(wf, nodes, links):
    """划区 + 把参数节点并入宿主区块。layout 与 check 必须共用这一套口径。

    返回 (blocks, block_of): blocks 是 {块号: [节点]} (含补入的参数节点),
    block_of 是 {节点: 块号}。MD/note 不参与, 不在返回值里。
    """
    blocks = _blocks(wf, nodes, links)
    block_of = {nid: k for k, g in blocks.items() for nid in g}
    consume = defaultdict(lambda: defaultdict(int))
    for l in links:
        if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
            consume[l[1]][l[3]] += 1

    for nid in nodes:
        if nid in block_of or nodes[nid]["type"] in _BUS_TYPES:
            continue
        # 参数节点的宿主区块 = 它的消费者里出现最多的那个区块
        w = defaultdict(int)
        for d, cnt in consume.get(nid, {}).items():
            if d in block_of:
                w[block_of[d]] += cnt
        if w:
            hb = max(w, key=w.get)
            block_of[nid] = hb
            blocks[hb].append(nid)

    # 仍无归属的(无消费者的纯孤立节点)单独成块
    stray = [nid for nid in nodes
             if nid not in block_of and nodes[nid]["type"] not in _BUS_TYPES]
    if stray:
        blocks[-1] = stray
        for nid in stray:
            block_of[nid] = -1
    return blocks, block_of


def layout(wf, keep_size=True):
    nodes = {n["id"]: n for n in wf["nodes"]}
    links = wf["links"]

    # ---- 深度分层 ----
    deps = defaultdict(list)
    for l in links:
        deps[l[3]].append(l[1])
    depth = {}

    def dep(nid, seen=()):
        if nid in depth:
            return depth[nid]
        if nid in seen:
            return 0
        ds = [dep(s, seen + (nid,)) + 1 for s in deps.get(nid, [])]
        depth[nid] = max(ds) if ds else 0
        return depth[nid]

    for nid in nodes:
        dep(nid)

    # 布局用的尺寸 = 节点「真实渲染尺寸」。
    # JSON 里的 size 常常是旧值(例如 RandomNoise 写 80, 实际渲染 148 —— 控件撑高了),
    # 按 JSON size 排出来的图一打开就重叠。所以取 max(JSON size, est_size)。
    # 写回时只改 pos, 不动 size(尺寸归节点自己管), 但排版按真实高度算。
    size = {}
    for nid, n in nodes.items():
        est = W.est_size(n)
        own = n.get("size") or [0, 0]
        size[nid] = [max(own[0], est[0]), max(own[1], est[1])]

    md_ids = [nid for nid, n in nodes.items() if n["type"] == "FallingTSMarkDownTable"]
    note_ids = [nid for nid, n in nodes.items() if n["type"] == "MarkdownNote"]
    isolated = set(md_ids) | set(note_ids)
    others = [nid for nid in nodes if nid not in isolated]

    deps2 = defaultdict(list)
    for l in links:
        if l[1] not in isolated:
            deps2[l[3]].append(l[1])
    depth2 = {}

    def dep2(nid, seen=()):
        if nid in depth2:
            return depth2[nid]
        if nid in seen:
            return 0
        ds = [dep2(s, seen + (nid,)) + 1 for s in deps2.get(nid, []) if s in nodes and s not in isolated]
        depth2[nid] = max(ds) if ds else 0
        return depth2[nid]

    for nid in others:
        dep2(nid)

    has_note = bool(note_ids)
    off = 1 if has_note else 0
    cols = defaultdict(list)
    for nid in note_ids:
        cols[0].append(nid)
    for nid in md_ids:
        cols[off].append(nid)
    # 功能列仍按「全局依赖深度」分列 —— 保证第 1 条(输出在左、输入在右)恒成立。
    # 区块不改变列归属, 只决定「纵向条带」(见下方 y 分配), 因为某些区块的
    # 深度跨度极大(VAE 链从深度 0 一直到 18), 按 x 分块必然与其他块交错。
    for nid in others:
        cols[depth2[nid] + 1 + off].append(nid)
    max_c = max(cols) if cols else 0

    # ---- 列内约束图(第 2 条: 端口上下序) ----
    _col_of_cache = {}
    for c, mem in cols.items():
        for nid in mem:
            _col_of_cache[nid] = c

    def col_of(nid):
        return _col_of_cache[nid]

    pos_of = {nid: col_of(nid) for nid in nodes}
    constraints = defaultdict(set)
    for n in wf["nodes"]:
        seq = []
        for slot, inp in enumerate(n.get("inputs", [])):
            lid = inp.get("link")
            if lid is None:
                continue
            l = next((x for x in links if x[0] == lid), None)
            if l is None:
                continue
            seq.append((slot, l[1]))
        for (s1, a), (s2, b) in zip(seq, seq[1:]):
            if a == b:
                continue
            if pos_of[a] == pos_of[b]:
                constraints[pos_of[a]].add((a, b))

    def topo(col, cons):
        members = sorted({x for p in cons for x in p})
        indeg = defaultdict(int)
        adj = defaultdict(set)
        for a, b in cons:
            if b not in adj[a]:
                adj[a].add(b)
                indeg[b] += 1
        q = sorted(members, key=lambda m: (indeg[m], m))
        out, done = [], set()
        while q:
            q.sort(key=lambda m: (indeg[m], m))
            x = q.pop(0)
            if x in done or indeg[x] > 0:
                continue
            done.add(x)
            out.append(x)
            for y in adj[x]:
                indeg[y] -= 1
                if indeg[y] == 0:
                    q.append(y)
        for m in sorted(members):
            if m not in done:
                out.append(m)
        rest = sorted(set(col) - set(out), key=lambda i: (nodes[i]["type"], i))
        return rest + [m for m in out if m not in rest]

    col_order = {}
    for c in range(0, max_c + 1):
        if c not in cols:
            continue
        col_order[c] = topo(cols[c], constraints.get(c, set())) if c > off else sorted(cols[c])

    # ---- 第 5.1/5.2 条: 功能区块 → 纵向横带 ----
    # 区块只按连线关系划分(参数节点/MD/note 不参与), 参数节点并入宿主区块。
    # 列归属不变(仍按全局深度), 所以第 1 条方向恒成立。
    blocks, block_of = _assign_blocks(wf, nodes, links)

    # 区块纵向排序: 平均深度小的在上(第 5.2 条), 使跨块连线保持左上→右下
    def blk_rank(k):
        g = [i for i in blocks[k] if i in depth2]
        if not g:
            return (0.0, 0)
        return (sum(depth2[i] for i in g) / len(g), k)

    blk_sorted = sorted(blocks, key=blk_rank)
    blk_pos = {k: i for i, k in enumerate(blk_sorted)}
    # 列内排序: 先按区块的带号, 再保持 topo 给出的端口序
    for c in col_order:
        if c <= off:
            continue
        base = {nid: i for i, nid in enumerate(col_order[c])}
        col_order[c].sort(key=lambda n: (blk_pos.get(block_of.get(n), 1 << 20), base[n]))

    # ---- 拆列 ----
    def is_sibling_col(c):
        members = col_order[c]
        if len(members) < 2:
            return False
        sinks = defaultdict(int)
        for nid in members:
            for d in {l[3] for l in links if l[1] == nid}:
                sinks[d] += 1
        if not sinks:
            return False
        return max(sinks.values()) >= len(members) * 0.7

    sub = {}
    for c in col_order:
        h = sum(size[i][1] for i in col_order[c]) + VGAP * (len(col_order[c]) - 1)
        if len(col_order[c]) > 1 and not is_sibling_col(c):
            sub[c] = max(1, math.ceil(h / MAX_COL_H))
        else:
            sub[c] = 1

    # ---- x 坐标 ----
    col_x = {}
    x = X0
    for c in range(0, max_c + 1):
        if c not in cols:
            continue
        col_x[c] = x
        x += (max(size[i][0] for i in cols[c]) + XGAP) * sub.get(c, 1)

    # ================= 第 4.1 / 4.2 条: 短线优先的 y 分配 =================
    first_target, out_slot = _first_slot_targets(wf)

    # 初始 y: 各列自顶向下堆叠(仅作起点)
    ypos = {}
    for c in col_order:
        y = Y0
        for nid in col_order[c]:
            ypos[nid] = y
            y += size[nid][1] + VGAP

    def resolve_col(c, desired):
        """按 desired 摆放一列, 再用「保序最小位移」消重叠。

        关键: 不能用「堆叠后整体平移」——那会让所有节点回到等距堆叠,
        对齐量被抵消。这里先把每个节点放到它想要的 y, 然后只在重叠处
        沿排序方向把它推开(保序), 使位移总量最小。
        """
        members = list(col_order[c])
        if not members:
            return members
        # 排序键 = (区块带号, 期望 y)。
        # 区块带号是**主键**: 第 5.2 条(分区块) 优先于第 4.1/4.2 条(短线最短)——
        # 宁可让某条线长一点, 也不能把同一区块的节点拆散到别的区块中间去。
        # 只有落在同一区块内的节点之间, 才按期望 y(短线优先)排序。
        order = sorted(members, key=lambda n: (blk_pos.get(block_of.get(n), 1 << 20),
                                               desired.get(n, ypos.get(n, 0)), n))
        # 初始 y = 期望中心 - 自身高的一半
        y = {}
        for nid in order:
            if nid in desired:
                y[nid] = desired[nid] - size[nid][1] / 2.0
            else:
                y[nid] = ypos.get(nid, 0)
        # 保序消重叠: 双向推挤, 使总位移最小。
        # 只往下推会让整列越推越远(每轮再加一截), 必须能往上拉。
        for _ in range(40):
            moved = False
            # 向下: 后面的不能压前面的
            for a, b in zip(order, order[1:]):
                need = y[a] + size[a][1] + VGAP
                if y[b] < need - 1e-6:
                    y[b] = need
                    moved = True
            # 向上: 前面的不能被后面压
            for b, a in zip(order[1:], order):
                need = y[b] - VGAP - size[a][1]
                if y[a] > need + 1e-6:
                    y[a] = need
                    moved = True
            if not moved:
                break
        for nid in order:
            ypos[nid] = y[nid]
        return order

    cols_sorted = sorted(col_order)
    # 前向扫描: 从左到右逐列定 y, 下游对齐上游(第 4.1/4.2 条)。
    # 只做单遍扫描, 不做多轮重心迭代 —— 多轮会让密集列互推发散(y 涨到数万像素)。
    up_of = defaultdict(list)
    for l in links:
        if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
            # MD/note 可以作为「上游」被对齐(它们的 pos 是确定的, 对齐一条
            # MD → 下游的线同样能让线变短); 只是它们自身不参与对齐计算。
            # 旧版把两端都排除, 导致所有 MD → 下游的线永远对不齐。
            if l[3] not in isolated:
                up_of[l[3]].append(l[1])

    # Reroute(纯转发节点)穿透: 对齐时跳过它, 直接对齐到它的真实上游。
    # Reroute 自身没有语义, 让它占一个「排队位」会白白把它要转发的源
    # 挤到很远的地方(实测 0023 里一条 MD→Reroute 的线偏差 1188px)。
    def ancestors(nid, guard=0):
        out = []
        for s in up_of.get(nid, []):
            if nodes[s]["type"] == "Reroute" and guard < 8:
                out += ancestors(s, guard + 1)
            else:
                out.append(s)
        return out or up_of.get(nid, [])

    for c in cols_sorted:
        if c <= off:
            continue
        desired = {}
        for nid in col_order[c]:
            if nodes[nid]["type"] == "Reroute":
                # Reroute 自身无对齐目标, 放到它下游的中心高度(它只是转发)
                downs = [d for s, d in out_slot.get(nid, []) if d in ypos and d != nid]
                if downs:
                    desired[nid] = sum(ypos[d] + size[d][1] / 2.0 for d in downs) / len(downs)
                continue
            ups = [s for s in ancestors(nid) if s in ypos]
            if len(ups) == 1:                      # 唯一上游 -> 必须对齐(第 4.1 条)
                desired[nid] = ypos[ups[0]] + size[ups[0]][1] / 2.0
            elif ups:
                # 多上游: 对齐「我位于它第一条输出线」的那一个(第 4.2 条)
                pri = [s for s in ups if first_target.get(s) == nid]
                if pri:
                    desired[nid] = ypos[pri[0]] + size[pri[0]][1] / 2.0
                else:
                    desired[nid] = sum(ypos[s] + size[s][1] / 2.0 for s in ups) / len(ups)
        if desired:
            resolve_col(c, desired)

    # ---- 第 5.2 条: 区块在列内相邻、跨列同序(不强制整体平移) ----
    # 说明: 区块的「列内相邻、跨列同序」已在上方 col_order 构建后用 blk_pos 排好,
    # 这里不再重复排序, 也**不**把区块整体平移成「水平横带」—— 实测那样会让长链
    # 区块(如 VAE 主链, 深度 0→18 横跨全图)的横带被拉到 5000px 以上, 反而更难辨认。
    # 区块呈斜向条带, 既聚而成群, 又不破坏第 1 条(方向)与第 4 条(短线优先)。

    # 归一: 整体上移到 Y0
    if ypos:
        shift = Y0 - min(ypos.values())
        for nid in ypos:
            ypos[nid] += shift

    # 写回
    for c in col_order:
        n_sub = sub.get(c, 1)
        w = max(size[i][0] for i in cols[c])
        per = math.ceil(len(col_order[c]) / n_sub) if col_order[c] else 1
        for k in range(n_sub):
            for nid in col_order[c][k * per:(k + 1) * per]:
                nodes[nid]["pos"] = [col_x[c] + k * (w + XGAP), round(ypos[nid])]
    return wf


def check(wf):
    nodes = {n["id"]: n for n in wf["nodes"]}
    links = wf["links"]
    r = W.inspect(wf)
    bad_lr = [(l[1], l[3]) for l in links
              if nodes[l[1]]["pos"][0] + nodes[l[1]]["size"][0] > nodes[l[3]]["pos"][0]]
    mds = [n for n in wf["nodes"] if n["type"] in ("FallingTSMarkDownTable", "MarkdownNote")]
    md_inv = 0
    for md in mds:
        mx0, mx1 = md["pos"][0], md["pos"][0] + md["size"][0]
        md_inv += sum(1 for n in wf["nodes"]
                      if n["id"] != md["id"] and n["type"] not in ("FallingTSMarkDownTable", "MarkdownNote")
                      and not (n["pos"][0] + n["size"][0] <= mx0 or n["pos"][0] >= mx1))
    note_left = 0
    for md in [n for n in wf["nodes"] if n["type"] == "FallingTSMarkDownTable"]:
        for note in [n for n in wf["nodes"] if n["type"] == "MarkdownNote"]:
            if not (note["pos"][0] + note["size"][0] + 50 <= md["pos"][0]):
                note_left += 1
    gaps = []
    col = defaultdict(list)
    for n in wf["nodes"]:
        col[n["pos"][0]].append(n)
    for x, ns in col.items():
        ns.sort(key=lambda n: n["pos"][1])
        for a, b in zip(ns, ns[1:]):
            g = b["pos"][1] - (a["pos"][1] + _h(a))
            # 只判「下限太挤」——太挤会真的看不清、连线叠在节点上, 是硬伤;
            # 上限(<100px)在短线优先下必然被突破: 为对齐上游(第 4.1/4.2 条),
            # 列内相邻节点常被推开很远, 规范本身也写明「远距节点之间不判上限」。
            if g <= 50:
                gaps.append((a["id"], b["id"], round(g)))

    # 第 4.1/4.2: 短线偏差统计
    # 判据要紧扣规则本意 —— 规则管的是「输出端怎么摆」, 不是「输入端每条都水平」:
    #   · 多输出节点: 只有 outputs[0] 那条线要求最短, 其余允许更长 => 只查第一条;
    #   · 单输出节点: 它只有一条线, 要求最短 => 必须查;
    #   · 当接收端被多个上游共享时(如 9 个 PrimitiveInt 喂同一个 Selector),
    #     接收端不可能同时与所有上游水平 —— 这种不算违规, 否则规则自相矛盾
    #     (N 个上游要求 N 个不同的 y)。故只统计「接收端仅此一个上游」的情形,
    #     这才是本条能真正约束到的对象。
    first, out_slot = _first_slot_targets(wf)
    indeg = defaultdict(int)
    for l in links:
        if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
            indeg[l[3]] += 1
    short_bad = 0
    short_total = 0
    # 同列占位表: 用于判断偏差是否「被不重叠规则逼出来的」
    col_members = defaultdict(list)
    for n in wf["nodes"]:
        col_members[n["pos"][0]].append(n)
    for x in col_members:
        col_members[x].sort(key=lambda n: n["pos"][1])

    def forced(a, b):
        """b 对齐 a 时, 是否被同列邻居挤得无法到达期望位置。

        第 3 条(不重叠)优先于第 4 条(最短): 若 b 的理想 y 会压到同列的上一节
        或下一节, 它只能被推开 —— 此时偏差不算违规。
        """
        want = _ctr(a) - _h(b) / 2.0
        cb = col_members.get(b["pos"][0], [])
        idx = next((i for i, n in enumerate(cb) if n["id"] == b["id"]), None)
        if idx is None:
            return False
        lo, hi = -1e18, 1e18
        if idx > 0:
            prev = cb[idx - 1]
            lo = prev["pos"][1] + _h(prev) + VGAP      # 不能压上一节
        if idx < len(cb) - 1:
            nxt = cb[idx + 1]
            hi = nxt["pos"][1] - VGAP - _h(b)          # 不能压下一节
        return not (lo - 1 <= want <= hi + 1)

    for src, dst in first.items():
        if src not in nodes or dst not in nodes:
            continue
        if indeg[dst] != 1:      # 接收端被共享 -> 本条无解, 不计
            continue
        short_total += 1
        if abs(_ctr(nodes[src]) - _ctr(nodes[dst])) > 5 and not forced(nodes[src], nodes[dst]):
            short_bad += 1

    # 第 5.3 条: 区块检验 —— 每列内, 同一区块的节点必须「连续成段」。
    # 判定口径: 同一区块在同一列里只允许出现 1 段; 出现 2 段及以上说明它被
    # 别的区块从中间切断了, 不算「聚在一起」。区块与区块之间切换是正常的,
    # 所以只统计「同一个块号重复出现」的段数。
    # 与 layout 共用 _assign_blocks, 保证「参数节点归属」口径一致 —— 否则
    # 参数节点在 check 里没有块号, 会被当成透明的, 漏掉它造成的断裂。
    _, bof = _assign_blocks(wf, nodes, links)
    blk_split = 0
    for x, mem in col.items():
        seq = [bof[n["id"]] for n in mem if n["id"] in bof]
        runs = [b for i, b in enumerate(seq) if i == 0 or b != seq[i - 1]]
        blk_split += len(runs) - len(set(runs))

    return {
        "ov": len(r.get("overlaps") or []),
        "lr": len(bad_lr),
        "md_inv": md_inv,
        "note_left": note_left,
        "gap_bad": len(gaps),
        "short_bad": short_bad,
        "blk_split": blk_split,
    }


def main():
    only = [a for a in sys.argv[1:] if not a.startswith("--")] or None
    changed = 0
    for f in sorted(os.listdir(WF_DIR)):
        if not f.endswith(".json"):
            continue
        if only and not any(o in f for o in only):
            continue
        p = os.path.join(WF_DIR, f)
        wf = json.load(open(p, encoding="utf-8"))
        if not wf.get("nodes"):
            print(f"-      {f}: 空图")
            continue
        before = check(wf)
        force = "--force" in sys.argv
        need = any(before[k] for k in before) or force
        if not need:
            print(f"= 跳过 {f}: 已合规 {before}")
            continue
        wf = layout(wf, keep_size="--keep-size" in sys.argv)
        after = check(wf)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(wf, fh, ensure_ascii=False, separators=(",", ":"))
        changed += 1
        clean = all(after[k] == 0 for k in ("ov", "lr", "md_inv", "gap_bad"))
        flag = "✅" if clean else "⚠️"
        print(f"{flag} {f}\n    前 {before}\n    后 {after}")
    print(f"\n共重排 {changed} 个工作流")


if __name__ == "__main__":
    main()
