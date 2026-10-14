#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量工作流布局重排 (六条布局规范, 含 note/MD 双独占列)。

用法:
    python scripts/wf_layout_all.py [关键字...] [--force]
    # 无关键字 = 全部工作流; --force = 已合规的也重排(统一坐标口径)

自动定位本仓根目录, 不依赖工作目录。幂等: 对已合规的布局再跑一次坐标不变。
"""
import json
import os
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_REPO, ".agents", "skills", "comfyui"))
import workflow_layout as W  # noqa: E402  (技能自带的估算/检查工具)

WF_DIR = os.path.join(_REPO, "workflows")
X0, XGAP, Y0, VGAP = 40, 80, 40, 60


def layout(wf):
    nodes = {n["id"]: n for n in wf["nodes"]}
    links = wf["links"]
    # 上游依赖
    deps = defaultdict(list)
    for l in links:
        deps[l[3]].append(l[1])
    # 深度
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

    size = {nid: W.est_size(nodes[nid]) for nid in nodes}

    # MD 表独占列 + note 记事本独占列(note 在 MD 左侧): 其它节点深度+1
    md_ids = [nid for nid, n in nodes.items() if n["type"] == "FallingTSMarkDownTable"]
    note_ids = [nid for nid, n in nodes.items() if n["type"] == "MarkdownNote"]
    isolated = set(md_ids) | set(note_ids)
    others = [nid for nid in nodes if nid not in isolated]
    # MD 无上游(深度0), 其它节点深度以"去掉MD后的依赖"为准(被MD引用不算深度)
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

    # 列: 0=note, 1=MD, 2..n=深度 (无 note 时 0=MD)
    has_note = bool(note_ids)
    off = 1 if has_note else 0
    cols = defaultdict(list)
    for nid in note_ids:
        cols[0].append(nid)
    for nid in md_ids:
        cols[off].append(nid)
    for nid in others:
        cols[depth2[nid] + 1 + off].append(nid)
    max_c = max(cols)

    # 列内约束图: 每个 sink 的已连输入按 slot 序 → 同列上游对 (a 在 b 上)
    def col_of(nid):
        if nid in note_ids:
            return 0
        if nid in md_ids:
            return off
        return depth2[nid] + 1 + off
    pos_of = {nid: col_of(nid) for nid in nodes}
    constraints = defaultdict(set)
    for n in wf["nodes"]:
        seq = []
        for slot, inp in enumerate(n.get("inputs", [])):
            lid = inp.get("link")
            if lid is None:
                continue
            l = next(x for x in links if x[0] == lid)
            seq.append((slot, l[1]))
        for (s1, a), (s2, b) in zip(seq, seq[1:]):
            if a == b:
                continue
            if pos_of[a] == pos_of[b]:
                constraints[pos_of[a]].add((a, b))

    # 拓扑去环: 环内节点保持任意序(打破一条边)
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
        # 环残余: 按原序补齐
        for m in sorted(members):
            if m not in done:
                out.append(m)
        # 未出现在约束中的列内节点按 id 排在前
        rest = sorted(set(col) - set(out), key=lambda i: (nodes[i]["type"], i))
        return rest + [m for m in out if m not in rest]

    col_order = {}
    for c in range(0, max_c + 1):
        if c not in cols:
            continue
        col_order[c] = topo(cols[c], constraints.get(c, set())) if c > off else sorted(cols[c])

    # 坐标
    col_x = {}
    x = X0
    for c in range(0, max_c + 1):
        if c not in cols:
            continue
        col_x[c] = x
        x += max(size[i][0] for i in cols[c]) + XGAP
    for c in col_order:
        y = Y0
        for nid in col_order[c]:
            n = nodes[nid]
            n["pos"] = [col_x[c], y]
            n["size"] = [size[nid][0], size[nid][1]]
            y += size[nid][1] + VGAP
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
    # note 必须在 MD 左侧
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
            g = b["pos"][1] - (a["pos"][1] + a["size"][1])
            if not (50 < g < 100):
                gaps.append((a["id"], b["id"], round(g)))
    return {
        "ov": len(r.get("overlaps") or []),
        "lr": len(bad_lr),
        "md_inv": md_inv,
        "note_left": note_left,
        "gap_bad": len(gaps),
    }


def main():
    only = sys.argv[1:] if len(sys.argv) > 1 else None
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
        need = any(before[k] for k in before) or "--force" in sys.argv
        if not need and "--force" not in sys.argv:
            print(f"= 跳过 {f}: 已合规 {before}")
            continue
        wf = layout(wf)
        after = check(wf)
        json.dump(wf, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        flag = "✅" if (after["ov"] == 0 and after["lr"] == 0 and after["md_inv"] == 0 and after["gap_bad"] == 0) else "⚠️"
        print(f"{flag} {f}: {before} -> {after}")


if __name__ == "__main__":
    main()
