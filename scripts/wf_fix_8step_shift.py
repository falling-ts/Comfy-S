#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把所有 H3 工作流中 8步链上的 MiniMaxH3SigmaShift 从 6/3 改为 12/3。

判据: SigmaShift 的 model 上游是 LoraLoaderModelOnly 且 LoRA 文件名含 8step。
LightX2V 官方推荐( discussion#51 ): 8-step v1.0 768p -> video shift 12, audio shift 3。
4步链(LoRA 为 4step)保持 6/3 不动。幂等: 已是 12/3 则跳过。
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
WF_DIR = os.path.join(_REPO, "workflows")

for f in sorted(os.listdir(WF_DIR)):
    if not f.endswith(".json"):
        continue
    p = os.path.join(WF_DIR, f)
    d = json.load(open(p, encoding="utf-8"))
    nodes = {n["id"]: n for n in d["nodes"]}
    links = {l[0]: l for l in d["links"]}
    changed = False
    for n in d["nodes"]:
        if n["type"] != "MiniMaxH3SigmaShift":
            continue
        lid = n["inputs"][0].get("link")
        if lid is None or lid not in links:
            continue
        src = links[lid][1]
        if src not in nodes or nodes[src]["type"] != "LoraLoaderModelOnly":
            continue
        w = nodes[src].get("widgets_values") or [""]
        if "8step" not in str(w[0]):
            continue
        if n.get("widgets_values") == [12, 3]:
            continue
        n["widgets_values"] = [12, 3]
        if "widgets_values_named" in n:
            n["widgets_values_named"] = {"shift_video": 12, "shift_audio": 3}
        changed = True
        print(f"[修] {f}: SigmaShift id{n['id']} 6/3 -> 12/3 (8步LoRA)")
    if changed:
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
