#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量工作流布局重排(八条布局规范: 方向 / 端口序 / 净距 / 短线优先 / 功能区块 / 阶梯)。

用法:
    python scripts/wf_layout_all.py [关键字...] [--force]
    # 无关键字 = 全部工作流; --force = 已合规的也重排(统一坐标口径)

自动定位本仓根目录, 不依赖工作目录。幂等: 对已合规的布局再跑一次坐标不变。

════ 核心算法(真正生效的三层结构, 按执行顺序) ════

一、列归属 = 【采样段 + 段内局部深度】(第 1 条: 输出在左输入在右)
    旧实现用「全局依赖深度」分列, 而全局深度只数数据上游, 于是二段采样用的
    UNETLoader/VAELoader/CLIPLoader 深度也是 0, 被推到整张图最左边, 与它
    服务的二段采样隔了大半张图(实测 11 个工作流、上百个节点越界)。
    _stages() 按采样器的上游闭包把节点分堆, 每段的列区间从上一段末尾之后
    开始, 于是「二段所有节点(含加载器/参数)都在一段结果节点右侧」恒成立。
    ⚠️ KSamplerSelect 不是采样器(它只是选采样器类型的参数节点), 误当采样器
    会把段号彻底搅乱。

二、区块 = 社区发现划区 + 区块段跟随上游(第 5.1/5.2/5.3 条)
    在主数据图(剔除参数节点/MD/note 这些广播总线)上做贪心模块度优化,
    得到功能区块; 参数节点按「消费者最多的区块」并入宿主块。
    列内: 同一区块必须连续成段(否则 blk_split > 0, 功能块被打散);
    区块段在列内的上下位置不看全局固定带号, 而看「该块在本列上游列里的
    平均 y」—— 段跟着上游走, 于是「同区块聚在一起」与「逐条对齐」同时成立。

三、列内 = 紧凑堆叠 + 上游 y 排序(第 3 条净距 / 第 4.1·4.2 条短线)
    每列从顶部开始紧凑堆叠, 净距恒为 VGAP(60px), 排序先按区块段、
    段内再按「上游中心 y」。绝不能把单个节点放到它「想对齐」的理想位置
    再推挤 —— 那样同一列各节点想对齐不同上游, 推挤会让净距雪崩到
    4000~7000px(实测 0032 最大 7075px), 画布高度轻松过万。

四、列间阶梯(第 7 条)
    从左往右每列抬高「左邻列首节点高度」的 30%, 避免相邻列顶端等高
    导致多条连线完全水平重叠、人眼分不清谁连谁; 抬高累积超过本列自身
    高度时回绕归零, 形成锯齿台阶而不是一路升到天上。

════ 校验指标(check) ════
ov(重叠) / lr(方向) / md_inv(MD 独占列) / note_left(note 在左) /
gap_bad(列内过挤) / blk_split(区块被切断) 这六项必须全为 0;
short_bad(短线偏差) 与 flat(顶端齐平的跨列对数) 是观测值, 不作为失败判据。
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
# 结果/预览类节点(一段的这类节点不得被继续节点屏障推走)
_RESULT_TYPES = (
    "PreviewVideo", "PreviewAudio", "PreviewImageSave", "PreviewAudioSave",
    "PreviewImage", "PreviewAny", "SaveImage", "SaveVideo", "SaveAudio",
    "AutoSaveImage", "VHS_VideoCombine",
)

# 采样器节点类型(用于切分「段」)
# ⚠️ 注意: KSamplerSelect **不是**采样器 —— 它是一个「选哪个采样器」的参数节点
# (类型也在 _PARAM_TYPES 里)。若把它当采样器, 每段的 RandomNoise/KSamplerSelect
# 会被拆成单独的段, 段号彻底乱掉(实测段0里全是 KSamplerSelect, 而真正的
# 采样器反而落到段1~3)。
_SAMPLER_TYPES = {
    "KSampler", "KSamplerAdvanced", "SamplerCustom", "SamplerCustomAdvanced",
}


def _stages(wf, nodes, links):
    """按「采样阶段」给节点分堆(二段采样/多段流水线)。

    背景(用户要求): 二段采样所需的所有节点(包括它自己的 UNETLoader/VAELoader/
    CLIPLoader/参数节点)必须放在**一段的结果节点(PreviewVideo/PreviewImage 等)
    的右侧**。而旧实现用「全局依赖深度」分列, 全局深度只数数据上游, 于是二段
    采样用的加载器深度也是 0, 被推到整张图最左边 —— 与它服务的二段采样隔了
    大半张图(实测 11 个工作流、上百个节点越界)。

    做法:
      1. 找出所有采样器, 算每个采样器的「上游闭包」;
      2. 采样器分层: 依赖其他采样器的层级 = 1 + 那些采样器的最大层级(拓扑);
      3. 每个节点归属于「需要它的采样器的最小层级」—— 一段采样器不用的
         加载器/参数自然归到二段。
    返回 (stage_of, n_stages): stage_of = {节点id: 段号}。
    无采样器的图返回 (全部 0, 1)。
    """
    ups = defaultdict(list)
    for l in links:
        if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
            ups[l[3]].append(l[1])
    samp = [nid for nid, n in nodes.items() if n["type"] in _SAMPLER_TYPES]
    if not samp:
        return {nid: 0 for nid in nodes}, 1

    def anc(nid):
        seen: set = set()
        st = [nid]
        while st:
            x = st.pop()
            for u in ups.get(x, []):
                if u not in seen:
                    seen.add(u)
                    st.append(u)
        return seen

    closures = {s: anc(s) | {s} for s in samp}
    lvl = {}

    def _lvl(s, guard=0):
        if s in lvl:
            return lvl[s]
        if guard > 60:
            return 0
        deps = [t for t in samp if t != s and t in closures[s]]
        lvl[s] = 1 + max((_lvl(t, guard + 1) for t in deps), default=-1)
        return lvl[s]

    for s in samp:
        _lvl(s)
    stage_of = {}
    for nid in nodes:
        cand = [lvl[s] for s in samp if nid in closures[s]]
        stage_of[nid] = min(cand) if cand else None

    # ⚠️ 采样器**之后**的下游节点(VAEDecode/CreateVideo/PreviewVideo 等)不在
    # 任何采样器的上游闭包里, 上面会得到 None。若不处理, 它们会被当成「段0」
    # 推回最左边 —— 实测 0030 出现 6 条「上游在右、下游在左」的方向违规。
    # 故按拓扑顺序让无归属节点继承「上游里最大的段号」: 下游永远在下游段的
    # 右侧, 也符合「二段处理后仍属二段」的直觉。
    indeg = {nid: 0 for nid in nodes}
    for l in links:
        if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
            indeg[l[3]] = indeg.get(l[3], 0) + 1
    down = defaultdict(list)
    for l in links:
        if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
            down[l[1]].append(l[3])
    queue = [nid for nid in nodes if indeg.get(nid, 0) == 0]
    while queue:
        nid = queue.pop()
        cur = stage_of.get(nid)
        for d in down.get(nid, []):
            cands = [x for x in (cur,) if x is not None]
            if stage_of.get(d) is None:
                if cands:
                    stage_of[d] = max(cands)
            else:
                # 已有归属(在某采样器的上游闭包里): 取较大值, 保证下游不倒退
                if cands and cur is not None:
                    stage_of[d] = max(stage_of[d], cur)
            indeg[d] -= 1
            if indeg[d] <= 0:
                queue.append(d)
    for nid in nodes:
        if stage_of.get(nid) is None:
            stage_of[nid] = 0
    return stage_of, (max(stage_of.values()) + 1 if stage_of else 1)


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

    # 仍无归属的(无消费者的纯孤立节点): 优先当成参数节点并入最近邻区块,
    # 否则单独成块。
    # ⚠️ 旧实现一律放进 `blocks[-1]`, 结果这些孤块(实测 0032 的 RandomNoise)
    # 按区块带号排位后会插在主区块中间, 造成「同一区块在同一列被切断」
    # (`blk_split` > 0), 视觉上就是把功能块打散了 —— 正是第 5.1/5.2 条要禁止的。
    # 修法: 有入边/出边邻居的孤块直接并入「与它连边权重最大」的邻居区块。
    stray = [nid for nid in nodes
             if nid not in block_of and nodes[nid]["type"] not in _BUS_TYPES]
    leftover = []
    for nid in stray:
        w = defaultdict(int)
        for l in links:
            if len(l) < 5:
                continue
            if l[1] == nid and l[3] in block_of:
                w[block_of[l[3]]] += 1
            elif l[3] == nid and l[1] in block_of:
                w[block_of[l[1]]] += 1
        if w:
            hb = max(w, key=w.get)
            block_of[nid] = hb
            blocks[hb].append(nid)
        else:
            leftover.append(nid)
    if leftover:
        blocks[-1] = leftover
        for nid in leftover:
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

    # 列归属: 按【段内局部深度】而非全局深度 —— 这是让「二段采样所需的所有节点
    # 都在一段结果节点右侧」真正成立的关键。
    # 旧实现分三步都失败过, 记录如下以免重蹈:
    #   ① 全局深度分列: 只数数据上游, 二段用的加载器/参数深度也是 0,
    #      被推到最左 —— 实测 11 个工作流、上百个节点越界;
    #   ② 参数节点贴消费者: 只修了参数节点, 二段的 UNETLoader/VAELoader/
    #      CLIPLoader 依旧在最左, 依然越界;
    #   ③ 正确做法(本版): 先用 _stages 算出「每个节点属于第几段」, 然后
    #      **列号从小段到大段递增排布**: 第 k 段的列区间 = [该段起点, ...),
    #      而段起点 = 上一段已用的最大列号 + 1。于是无论某节点是加载器、
    #      参数还是后处理, 只要它属于二段, 它的列就一定在一段全部节点
    #      (含 PreviewVideo/PreviewImage 等结果节点)的右边。
    _consumers = defaultdict(list)
    for l in links:
        if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
            _consumers[l[1]].append(l[3])

    has_note = bool(note_ids)
    off = 1 if has_note else 0
    cols = defaultdict(list)
    for nid in note_ids:
        cols[0].append(nid)
    for nid in md_ids:
        cols[off].append(nid)
    first_fn_col = 1 + off

    stage_of, n_stage = _stages(wf, nodes, links)
    # 每段内再按局部深度分层(只在本段节点上算深度)
    stage_members = defaultdict(list)
    for nid in others:
        stage_members[stage_of.get(nid, 0)].append(nid)
    # 段起点累加: 第 k 段从上一个段的末尾之后开始
    stage_base = {}
    base = first_fn_col
    for st in range(n_stage):
        mem = stage_members.get(st, [])
        if not mem:
            continue
        # 本段内部的局部深度(上游只在本段内算)
        loc = {}
        mem_set = set(mem)

        def _loc(nid, seen=()):
            if nid in loc:
                return loc[nid]
            if nid in seen:
                return 0
            ds = [_loc(s, seen + (nid,)) + 1 for s in deps2.get(nid, []) if s in mem_set]
            loc[nid] = max(ds) if ds else 0
            return loc[nid]

        span = 0
        for nid in mem:
            _loc(nid)
            span = max(span, loc[nid])
        stage_base[st] = (base, loc)
        base += span + 1

    _param_pending: dict = {}
    for nid in others:
        st = stage_of.get(nid, 0)
        if st in stage_base:
            b, loc = stage_base[st]
            col = b + loc.get(nid, 0)
        else:
            col = first_fn_col + depth2[nid]
        # 参数节点的贴列延到屏障之后 —— 屏障会把纯二段节点整体右移,
        # 参数原本按旧列贴会在右移后落到消费者右侧。
        if nodes[nid]["type"] in _PARAM_TYPES:
            _param_pending[nid] = col
            continue
        cols[col].append(nid)

    # ---- 「继续节点」屏障: 纯二段节点必须落在继续节点右侧 ----
    #
    # 用户指定的权威口径(严格版):
    #   ① 以**二段采样核心节点**(末段采样器)为起点, **往前(往左)溯源**,
    #      取它的上游闭包 —— 沿途所有节点都是候选;
    #   ② 若候选节点与**一段采样节点毫无关系**, 就必须在继续节点右侧。
    #
    # 「与一段采样毫无关系」的严格定义: 该节点的**上游闭包**里不含任何一段
    # 采样器。这比「它自身不在一段闭包里」严得多 ——
    # 一个节点可能自己不被一段用到, 但它的上游是某个一段采样器的下游
    # (典型的跨段汇流节点, 如 0030 的 LTXVCropGuides(199): 它上游同时有
    # 一段采样器 204 和纯二段链)。把这类节点右移, 它的一段侧上游仍在左,
    # 立即产生 lr(上游在右、下游在左)。
    #
    # 一段侧排除集(三者都不动):
    #   · 一段采样器自身及其上游闭包
    #   · 继续节点自身及其上游闭包(闸门左侧属一段展示区)
    #   · 广播总线(MD/note)与参数节点(无上游、恒贴消费者, 不参与数据流)
    #   · 非末段的结果/预览节点(常被二段采样器当作素材源引用)
    cont_ids = [nid for nid, n in nodes.items() if "Continue" in n["type"]]
    if cont_ids:
        _dn = defaultdict(list)
        for l in links:
            if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
                _dn[l[1]].append(l[3])

        def _down(nid):
            seen: set = set()
            st_k = [nid]
            while st_k:
                x = st_k.pop()
                for d in _dn.get(x, []):
                    if d not in seen:
                        seen.add(d)
                        st_k.append(d)
            return seen

        _up = defaultdict(list)
        for l in links:
            if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
                _up[l[3]].append(l[1])

        def _anc(nid):
            seen: set = set()
            st_k = [nid]
            while st_k:
                x = st_k.pop()
                for u in _up.get(x, []):
                    if u not in seen:
                        seen.add(u)
                        st_k.append(u)
            return seen

        _samp_all = [nid for nid, n in nodes.items()
                     if n["type"] in _SAMPLER_TYPES]
        _bus = {nid for nid, n in nodes.items()
                if n["type"] in _BUS_TYPES or n["type"] in _PARAM_TYPES}
        _LAST = n_stage - 1
        _s2 = [s for s in _samp_all if stage_of.get(s) == _LAST]
        _s1 = [s for s in _samp_all if stage_of.get(s) != _LAST]

        # 严格口径的「纯二段」集合
        _pure2: set = set()
        if _s2 and _s1 and n_stage >= 2:
            _samp1 = set(_s1)
            _cont_up = set(cont_ids)
            for c in cont_ids:
                _cont_up |= _anc(c)

            # 「与一段采样无关」的正确判据: 从该节点往外溯源, 遇到**任何
            # 采样器就停**(不越过它)。只要这段「准备链路」不共用一段采样器
            # 的上游产出, 它就是二段专用。
            #
            # 为何不能直接取完整上游闭包: 二段采样器**必然**消费一段采样器
            # 的结果(这是分段流程的定义!), 其完整上游闭包必然含一段采样器。
            # 若按完整闭包判, 纯二段集永远是空集 —— 实测确实如此。
            # 我们要判的是「它的**准备节点**(加载器/编码器/参数等)有没有跟
            # 一段共用」, 这才是用户在说「与一段采样没有关系」时的意思。
            def _prep(nid):
                """往上游找准备节点, 遇采样器即停。"""
                _s: set = set()
                _q = list(_up.get(nid, []))
                while _q:
                    _x = _q.pop()
                    if _x in _s or _x not in nodes:
                        continue
                    _s.add(_x)
                    if nodes[_x]["type"] in _SAMPLER_TYPES:
                        continue        # 采样器不越过
                    _q.extend(_up.get(_x, []))
                return _s

            _prep1 = set()
            for s in _s1:
                _prep1 |= _prep(s)
            _anc2 = set(_s2)
            for s in _s2:
                _anc2 |= _anc(s)
            for x in _anc2:
                if x in _bus or x in _cont_up:
                    continue
                # ⚠️ 判据必须两次都查:
                #   ① x **自身**是否已在一段的准备链里 —— 共享加载器实测
                #      0030 的 CLIPLoader(189) 同时喂一段与二段; 但它无上游,
                #      所以只看 _prep(x) 会把它当成「纯二段」而拉走,
                #      而它的下游 CLIPTextEncode(190/191) 留在左边 ⇒ lr;
                #   ② x 的上游里是否有一段准备节点。
                if x in _prep1:
                    continue
                if (_prep(x) & _prep1):
                    continue
                # 非末段的结果/预览节点不动(一段产物常被二段引用)
                if (any(t in nodes[x]["type"] for t in _RESULT_TYPES)
                        and stage_of.get(x, 0) < _LAST):
                    continue
                _pure2.add(x)
            # ⚠️ 不做下游补全 —— 用户口径是「从二采核心**往前**溯源」,
            # 纯二段集只包含上游准备链。下游节点(VAEDecode/PreviewImageSave)
            # 由段系统自然排在采样器之后, 不需要、也不应该被拎到这里。
            # 实测 00110: 下游补全把 VAEDecode(103) 拉进纯二段集, 而纯二段
            # 集的定位是「屏障基准 + 块内深度」, 于是 103 被放到列 13;
            # 而二段采样器 102 在 x=8860 —— 下游跑到上游左侧, 1 条 lr。
            # ⚠️ 不要再做「反向剪枝(看上游)」—— 该规则本身是错的。
            # 第 1 条只要求 `A.x+A.宽 ≤ B.x`, 即上游在左、下游在右。
            # 若某节点右移而它的上游留在左边, 这**完全合法**;
            # 只有当它的**下游**留在左边时才是 lr。
            # 实测 00110: VAEDecode(103) 的上游是共享的 VAELoader(106),
            # 按得上游剪枝就会把 103 剔出去, 而它是二段采样器 102 的
            # 直接下游 —— 102 右移到 8860、103 留在 5940, 立即 1 条 lr。
            # 纯二段集只由「二采核心采样器的上游闭包」构成，**不做上下游补全**。
            # 用户口径就是「往前溯源」: 候选集 = 二采核心的上游闭包减去一方
            # 准备链。补全上下游会引入两个 bug(均已实测):
            #   · 补下游把 VAEDecode(103) 拉进来, 它被按块内深度放到列 13,
            #     而二段采样器 102 在 x=8860 —— 下游跑到上游左侧;
            #   · 补上游把 CLIPLoader(189) 拉进来, 它的下游 CLIPTextEncode
            #     与一段共用准备链不能动 ⇒ 上游越过下游。
            # 下游节点(VAEDecode/PreviewImageSave 等)由段系统自然排在
            # 采样器之后, 不需要被拎进纯二段集。

        # 继续节点所在列: 从 cols 反查, 右限 = 该列 +1
        _col_of_now = {}
        for _c, _mem in cols.items():
            for _nid in _mem:
                _col_of_now[_nid] = _c
        cont_cols = [_col_of_now[nid] for nid in cont_ids if nid in _col_of_now]
        if cont_cols:
            barrier = max(cont_cols) + 1
            # ══ 整体右移障法(正确解法) ══
            # 关键认识: 纯二段准备链的目标位置(继续节点右侧)**通常已被占满**。
            # 实测 0011: 链 5503→5504→5507→5601→5708→5710→5602→6024 中
            # 前四个在继续节点左侧, 后四个已在右侧。直接把前四个「塞到"]
            # barrier 右侧会撞上后四个, 无论怎么逐个搬都会出 lr。
            #
            # 故做法: ①先把右侧【整体】右移 W 列腾出空位; ②再把纯二段块
            # 放进刚腾出的位置。右移是整体平移 —— 右侧各节点的相对顺序
            # 完全不变, 因此不会产生任何新的 lr。
            if _pure2 and cont_cols:
                barrier = max(cont_cols) + 1
                # 块内拓扑深度(只算块内上游)
                _p2dep: dict = {}

                def _pd(nid, guard=0):
                    if nid in _p2dep:
                        return _p2dep[nid]
                    if guard > 80:
                        return 0
                    _u = [u for u in _up.get(nid, []) if u in _pure2]
                    _p2dep[nid] = 1 + max((_pd(u, guard + 1) for u in _u),
                                          default=-1)
                    return _p2dep[nid]

                for x in _pure2:
                    _pd(x)
                _w = max(_p2dep.values()) + 1        # 块所需列宽
                # 只处理「确实需要右移」的: 块内有节点在屏障左侧
                if any(_col_of_now.get(x) is not None
                       and _col_of_now[x] < barrier for x in _pure2):
                    # ① 把 cols 中 >= barrier 的列整体右移 _w
                    _shifted = {}
                    for _c in sorted(cols):
                        if _c >= barrier and cols[_c]:
                            _shifted[_c] = cols.pop(_c)
                    for _c, _mem in _shifted.items():
                        cols[_c + _w] = _mem
                        for _x in _mem:
                            _col_of_now[_x] = _c + _w
                    # ② 从原位置摧除纯二段块, 再放进腾出的区间
                    for x in _pure2:
                        _c0 = _col_of_now.get(x)
                        if _c0 is not None and x in cols.get(_c0, []):
                            cols[_c0].remove(x)
                    for x in _pure2:
                        _nc = barrier + _p2dep[x]
                        cols[_nc].append(x)
                        _col_of_now[x] = _nc
                    print(f"      ↳ 继续节点屏障: {len(_pure2)} 个纯二段节点"
                          f"移至继续节点右侧(右侧让位 {_w} 列)")
    # ---- 参数节点贴列(屏障之后) ----
    # 参数节点无上游、局深度恒 0, 不贴就会与消费者同列(违反第 1 条)。
    # 必须在屏障之后算 —— 屏障会把纯二段节点整体右移, 参数若按旧列贴, 就会
    # 落到消费者右侧(实测 0021/00200: FallingTSSwitch 右移后, 它的
    # PrimitiveInt/PrimitiveFloat 参数留在原列, 产生 6 条 lr)。
    _col_after = {}
    for _c, _mem in cols.items():
        for _x in _mem:
            _col_after[_x] = _c
    for nid, col in _param_pending.items():
        st = stage_of.get(nid, 0)
        cons = [d for d in _consumers.get(nid, []) if d in nodes]
        if cons:
            _cc = [_col_after.get(d) for d in cons if _col_after.get(d) is not None]
            if _cc:
                # 不得回遇到本段起点之前 —— 否则二段的参数会被拉回一段里,
                # 造成「上游落在下游右侧」的方向违规(lr>0)。
                col = max(stage_base[st][0] if st in stage_base else first_fn_col,
                          min(_cc) - 1)
        cols[col].append(nid)

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

    # ---- x 坐标: 逐(子)列顺序推进, 横向净距恒为 XGAP -------
    # 旧版用 (列最大宽 + XGAP) * sub 一次性跳过整列, 但子列里节点的实际宽度
    # 往往小于该列最大宽, 于是子列之间净距被拉大到 140~200px, 列与列之间还
    # 出现 9000px 量级的空白(实测 0032 横距达 9600px)。改为按每个子列的
    # 实际最大宽度逐个推进, 使相邻(子)列净距严格等于 XGAP(落在规范 (50,100) 区间)。
    col_per = {}
    for c in col_order:
        n_sub = sub.get(c, 1)
        col_per[c] = math.ceil(len(col_order[c]) / n_sub) if col_order[c] else 1

    col_x = {}          # (列号, 子列号) -> x
    cursor = X0
    for c in range(0, max_c + 1):
        if c not in cols:
            continue
        per = col_per[c]
        for k in range(sub.get(c, 1)):
            chunk = col_order[c][k * per:(k + 1) * per]
            if not chunk:
                continue
            col_x[(c, k)] = cursor
            cursor += max(size[i][0] for i in chunk) + XGAP

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
        """按 desired 摆一列: 紧凑堆叠 + 整列锚点平移。

        历史教训(务必保留): 旧版把每个节点先放到“它自己想要的 y”(对齐上游的
        理想位置), 再在重叠处来回推挤。同一列里各节点想对齐不同上游, 理想位置
        互相重叠后推挤会把它们一路推开, 净距雪崩到 4000~7000px
        (实测 0032 纵距最大 7075px、0031 6602px), 画布高度轻松过万。
        故本函数把第 3 条(净距)当硬约束:
          1) 整列紧凑堆叠, 净距恒为 VGAP;
          2) 对齐只在「整列平移」这 1 个自由度上取舍 —— 永远不可能局部位移出空隙。
        注: 本函数写下的 y 会被后面的「第 4.1 条收口」以更优的区块分段方式重算,
        但它决定了「列内顺序」与拆列切分, 所以不能删(实测去掉调用有 2/35 图变化)。
        """
        members = list(col_order[c])
        if not members:
            return members
        # 排序键 = (区块带号, 期望 y)。
        # 区块带号是**主键**: 第 5.2 条(分区块) 优先于第 4.1/4.2 条(短线最短)——
        # 宁可让某条线长一点, 也不能把同一区块的节点拆散到别的区块中间去。
        order = sorted(members, key=lambda n: (blk_pos.get(block_of.get(n), 1 << 20),
                                               desired.get(n, ypos.get(n, 0)), n))
        # 1) 相对堆叠(净距严格 VGAP)
        rel = {}
        acc = 0.0
        for nid in order:
            rel[nid] = acc
            acc += size[nid][1] + VGAP
        # 2) 列锚点: 让整列平移量最小化对齐残差
        deltas = [desired[nid] - size[nid][1] / 2.0 - rel[nid]
                  for nid in order if nid in desired]
        anchor = rel[order[0]] + ypos.get(order[0], Y0)     # 先验: 保持原位置
        if deltas:
            # 最小二乘平移量; 与旧位置各占一半, 避免长链整体飘走
            best = sum(deltas) / len(deltas)
            best = 0.5 * best + 0.5 * anchor
        else:
            best = anchor
        for nid in order:
            ypos[nid] = rel[nid] + best
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

    # ---- x 落位: 把节点分配到最终列 x ----
    final_x = {}
    for c in col_order:
        n_sub = sub.get(c, 1)
        per = col_per[c]
        seq = sorted(col_order[c], key=lambda n: (ypos.get(n, 0), n))
        for k in range(n_sub):
            cx = col_x.get((c, k))
            if cx is None:
                continue
            for nid in seq[k * per:(k + 1) * per]:
                final_x[nid] = cx
    by_x = defaultdict(list)
    for nid, x in final_x.items():
        by_x[x].append(nid)

    # ---- 第 4.1 条收口: 各列按「上游中心 y」重排 + 紧凑堆叠 ----
    # ⚠️ 这是本轮修的第 4.1 条失效病根。旧版列内排序的主键是**区块带号**,
    # 同一区块内的节点被按区块顺序硬堆在一起, 完全遮住了「每个节点想对齐哪个
    # 上游」—— 于是大量单出线无法对齐(实测 0032 单出线偏差均 517px、最大
    # 1304px), 人眼看到的就是「没分区块、连线乱」, 即用户反馈的问题。
    # 也不能反过来完全无视区块(那就回到第 5 条之前「整个混乱堆一列」的老毛病),
    # 且不能按节点 id 堆叠。
    # 正确做法: 反复「按上游中心 y 排序 → 紧凑堆叠」若干轮, 让每列的上下顺序
    # 向「上游的上下顺序」收敛。这样单出线自然水平(第 4.1), 多出线/多入线
    # 也自然不交叉(第 2 条), 同时因为仍是紧凑堆叠, 净距恒为 VGAP(第 3 条)。
    # 区块只当 tie-break, 兼顾第 5.1/5.2 条的「同区块聚在一起」。
    ups_map = defaultdict(list)
    for l in links:
        if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
            ups_map[l[3]].append(l[1])
    xs_all = sorted(by_x)
    # 区块在每列里要排成连续段(第 5.1/5.2), 但**段的上下位置不能再按全局固定的
    # 区块带号(blk_pos)** —— 那样跨列时区块段与它的上游完全脱钉, 单出线没法对齐
    # (实测 0032 均偏差 517px)。正确做法: 逐列从左往右扫, 每列的区块段按
    # 「该区块在已确定列里的上游平均 y」排序 —— 区块段跟着它的上游走, 于是
    # 同区块连续(blk_split=0) 与逐条对齐(第 4.1) 同时成立。
    for x in xs_all:
        ids = by_x[x]
        if not ids:
            continue
        # 1) 按区块分组
        groups = defaultdict(list)
        for nid in ids:
            groups[blk_pos.get(block_of.get(nid), 1 << 20)].append(nid)
        # 2) 区块段排序键: 上游平均 y(取自已确定列); 没有可用上游时退回全局带号
        def _blk_key(b):
            ups_y = []
            for nid in groups[b]:
                for s in ups_map.get(nid, []):
                    if s in ypos:
                        ups_y.append(ypos[s] + size[s][1] / 2.0)
            if ups_y:
                return (0, sum(ups_y) / len(ups_y), b)
            return (1, 0.0, b)
        # 3) 段内按上游平均 y 排序, 使单出线尽量水平
        order = []
        for b in sorted(groups, key=_blk_key):
            seg = groups[b]

            def _key(nid):
                ss = [s for s in ups_map.get(nid, []) if s in ypos]
                if ss:
                    return (sum(ypos[s] + size[s][1] / 2.0 for s in ss) / len(ss), nid)
                return (1e18, nid)

            order.extend(sorted(seg, key=_key))
        # 4) 紧凑堆叠(净距恒为 VGAP, 第 3 条不受影响)
        y = Y0
        for nid in order:
            ypos[nid] = y
            y += size[nid][1] + VGAP
        by_x[x] = order
    # 重排后各列顺序变了, 列内高度也要跟着更新(供台阶回绕判定用)
    for x in xs_all:
        by_x[x] = sorted(by_x[x], key=lambda n: (ypos.get(n, 0), n))

    # ---- 第 7 条台阶(只作用于功能列) ----
    # 用户明确要求: **台阶仅对功能节点生效; note 节点与左侧第一个功能节点
    # 保持完美横向并行**(同一 y), 不被台阶抬高。
    # 理由: note/MD 是说明文档与数据表, 它们是参照物而不是数据流的一环,
    # 跟着台阶上下浮动只会让人更难对照阅读。
    #
    # 实测台阶与「单出线对齐」天然矛盾:
    #   · 台阶幅度 100%: 对齐均偏差升到 237~558px;
    #   · 不做台阶: 对齐最优(均 121~144px)但相邻列顶端等高, 多条连线完全
    #     水平重叠, 人眼分不清谁连谁。
    # 故台阶只取「一个节点高度」的 30%: 既能错开列首(>20px), 又把对齐恶化压到最小。
    STEP_RATIO = 0.3
    # 先算各功能列的堆叠高度(不含 note/MD 列)
    col_ids = {}
    col_h = {}
    for x in sorted(by_x):
        ids = sorted(by_x[x], key=lambda n: (ypos.get(n, 0), n))
        # note/MD 独占列不参与台阶
        if all(nodes[i]["type"] in _BUS_TYPES for i in ids):
            continue
        col_ids[x] = ids
        col_h[x] = sum(size[i][1] for i in ids) + VGAP * (len(ids) - 1)
    # 台阶偏移: 向右逐级抬高(offset 递减); 低于 -本列高度 时回绕归零。
    # 第一个功能列固定 offset=0, 后面的列才开始叠台阶。
    offset = 0.0
    prev_first = None
    for x in sorted(col_ids):
        ids = col_ids[x]
        if prev_first is not None:
            offset -= size[prev_first][1] * STEP_RATIO   # 左邻列首节点高度的 30%
            if offset < -col_h[x]:                        # 回绕: 不累积成无底深渊
                offset = 0.0
        y = Y0 + offset
        for nid in ids:
            ypos[nid] = y
            y += size[nid][1] + VGAP
        prev_first = ids[0]
    # note/MD: 与左侧第一个功能列完美横向并行(同 y = Y0 + 0)
    for x in sorted(by_x):
        ids = by_x[x]
        if not ids or not all(nodes[i]["type"] in _BUS_TYPES for i in ids):
            continue
        y = Y0
        for nid in sorted(ids, key=lambda n: (ypos.get(n, 0), n)):
            ypos[nid] = y
            y += size[nid][1] + VGAP
    # 若整体出现了负 y(向上冲出画布), 统一平移回 Y0
    if ypos:
        shift = Y0 - min(ypos.values())
        for nid in ypos:
            ypos[nid] += shift

    # 写回
    for nid, x in final_x.items():
        nodes[nid]["pos"] = [x, round(ypos[nid])]
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

    # 第 7 条: 斜向瀑布 —— 相邻列首节点必须错开(否则多条连线挤成水平带)
    # 判据: 相邻两列中存在上下游连线的列对, 其列首 y 不应相等(误差>20px 算有错位),
    # 但允许瀑布回绕(offset 归零), 故不追求每对都错位, 只要多数列对有错位即可。
    x_col = defaultdict(list)
    for n in wf["nodes"]:
        x_col[n["pos"][0]].append(n)
    xs = sorted(x_col)
    first_y = {x: min(n["pos"][1] for n in x_col[x]) for x in xs}
    linked = set()
    for l in links:
        if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
            ax, bx = nodes[l[1]]["pos"][0], nodes[l[3]]["pos"][0]
            if ax != bx:
                linked.add((min(ax, bx), max(ax, bx)))
    cascade_pairs = 0
    cascade_ok = 0
    for a, b in zip(xs, xs[1:]):
        if (a, b) not in linked:
            continue
        cascade_pairs += 1
        if abs(first_y[b] - first_y[a]) > 20:
            cascade_ok += 1

    # 第 7 条补充: note/MD 的**列首节点**必须与「左侧第一个功能列」的列首 y 相等。
    # 注意两件事:
    #   1. 不能拿 Y0 硬套 —— 收官的全图归位会把首功能列一起推走;
    #   2. 只看**列首那个** —— 同列若有多个 note/MD, 它们内部按紧凑堆叠依次向下,
    #      不可能都等于同一个 y(那样会重叠), 所以只校验最上方那个。
    bus_cols = [x for x in xs
                if all(n["type"] in _BUS_TYPES for n in x_col[x])]
    fn_cols = [x for x in xs if x not in bus_cols]
    note_par = 0
    if bus_cols and fn_cols:
        fn_y = min(n["pos"][1] for n in x_col[fn_cols[0]])
        for x in bus_cols:
            head_y = min(n["pos"][1] for n in x_col[x])   # 只取列首
            if head_y != fn_y:
                note_par += 1

    # 第 9.1 条: 「纯二段」节点不得落在继续节点左侧。
    # 判据与 layout 一致: 消费者全部落在继续节点下游闭包内, 且自身不是非末段结果节点。
    _dn = defaultdict(list)
    for l in links:
        if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
            _dn[l[1]].append(l[3])

    def _closure(start, adj):
        seen: set = set()
        stack = [start]
        while stack:
            cur = stack.pop()
            for nxt in adj.get(cur, []):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    cont_ids = [nid for nid, n in nodes.items() if "Continue" in n["type"]]
    cont_left = 0
    if cont_ids:
        # 与 layout() 完全一致的严格口径: 以末段采样器为起点往上游溯源,
        # 凡上游闭包不碰一段采样器、也不属总线/继续上游/非末段结果的节点,
        # 都必须在继续节点右侧。
        cx = min(nodes[cid]["pos"][0] for cid in cont_ids)
        st_of, n_st = _stages(wf, nodes, links)
        _upd = defaultdict(list)
        for l in links:
            if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
                _upd[l[3]].append(l[1])

        def _ancx(x):
            s: set = set()
            q = [x]
            while q:
                v = q.pop()
                for u in _upd.get(v, []):
                    if u not in s:
                        s.add(u)
                        q.append(u)
            return s

        _samp_all = [nid for nid, n in nodes.items()
                     if n["type"] in _SAMPLER_TYPES]
        _bus = {nid for nid, n in nodes.items()
                if n["type"] in _BUS_TYPES or n["type"] in _PARAM_TYPES}
        if n_st >= 2 and _samp_all:
            _LAST = n_st - 1
            _s2 = [s for s in _samp_all if st_of.get(s) == _LAST]
            _s1 = [s for s in _samp_all if st_of.get(s) != _LAST]
            if _s2 and _s1:
                _anc2 = set(_s2)
                for s in _s2:
                    _anc2 |= _ancx(s)
                _samp1 = set(_s1)
                _cont_up = set(cont_ids)
                for c in cont_ids:
                    _cont_up |= _ancx(c)
                _pure2c: set = set()
                for n in wf["nodes"]:
                    nid = n["id"]
                    if nid not in _anc2 or nid in _bus or nid in _cont_up:
                        continue
                    if _ancx(nid) & _samp1:
                        continue
                    if (any(t in n["type"] for t in _RESULT_TYPES)
                            and st_of.get(nid, 0) < _LAST):
                        continue
                    _pure2c.add(nid)
                # 与 layout() 同一收缩规则: 下游还连着「与一段有关」的节点时,
                # 该节点不能算纯二段(否则右移会制造 lr)
                _dn_check = defaultdict(list)
                for l in links:
                    if len(l) >= 5 and l[1] in nodes and l[3] in nodes:
                        _dn_check[l[1]].append(l[3])
                _chgc = True
                while _chgc:
                    _chgc = False
                    for x in list(_pure2c):
                        for d in _dn_check.get(x, []):
                            if d not in nodes or d in _pure2c:
                                continue
                            if d in _bus or d in _cont_up:
                                continue
                            if (any(t in nodes[d]["type"] for t in _RESULT_TYPES)
                                    and st_of.get(d, 0) < _LAST):
                                continue
                            _pure2c.discard(x)
                            _chgc = True
                            break
                for n in wf["nodes"]:
                    if n["id"] in _pure2c and n["pos"][0] < cx:
                        cont_left += 1

    return {
        "ov": len(r.get("overlaps") or []),
        "lr": len(bad_lr),
        "md_inv": md_inv,
        "note_left": note_left,
        "gap_bad": len(gaps),
        "short_bad": short_bad,
        "blk_split": blk_split,
        "note_par": note_par,        # 第 7 条: note/MD 未与首功能列并行
        "cont_left": cont_left,      # 第 9.1 条: 纯二段节点留在继续节点左侧
        "flat": cascade_pairs - cascade_ok,      # 相邻列顶平的列对数(越少越好)
    }


# 必须归零的硬指标(与 workflow-layout.md 的「验收总表」一一对应):
#   ov/lr/md_inv/note_left/gap_bad/blk_split  —— 第 1、3、5.2 条
#   note_par                                  —— 第 7 条 note/MD 与首功能列并行
#   cont_left                                 —— 第 9.1 条 继续节点屏障
# 观测指标(不作为失败判据):
#   short_bad: 第 4.1 条要求单出线居中, 但一列里多个节点各想对齐不同上游时
#     物理上无解(节点高度与 60px 节距是刚性约束), 只能尽量小;
#   flat:      第 7 条台阶回绕时必然产生少量顶端齐平, 是预期行为。
_HARD_KEYS = ("ov", "lr", "md_inv", "note_left", "gap_bad", "blk_split",
              "note_par", "cont_left")


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
        # 是否需要重排: 任一硬指标不过就需要重排(观测指标不作为触发条件)
        need = any(before[k] for k in _HARD_KEYS) or force
        if not need:
            print(f"= 跳过 {f}: 已合规 {before}")
            continue
        wf = layout(wf, keep_size="--keep-size" in sys.argv)
        after = check(wf)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(wf, fh, ensure_ascii=False, separators=(",", ":"))
        changed += 1
        clean = all(after[k] == 0 for k in _HARD_KEYS)
        flag = "✅" if clean else "⚠️"
        print(f"{flag} {f}\n    前 {before}\n    后 {after}")
    print(f"\n共重排 {changed} 个工作流")


if __name__ == "__main__":
    main()
