#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补回 Selector input5(8步采样器 euler) 的端口 link 字段(链已在 links 数组, 只缺端口回填)。幂等。"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
WF_DIR = os.path.join(_REPO, "workflows")
TARGETS = {
    "0013_首图建模": None, "0014_参考建模": None, "0030_文生场景": None, "0032_参考场景": None,
    "0040_文生视频": None, "0041_首帧视频": None, "0042_首尾视频": None,
    "0043_关键帧视频": None, "0044_参考视频": None,
}

for name in TARGETS:
    p = os.path.join(WF_DIR, f"{name}.json")
    d = json.load(open(p, encoding="utf-8"))
    sel = next((n for n in d["nodes"]
                if n["type"] == "FallingTSSelector"
                and n.get("widgets_values", [""])[0] == "默认,8步,4步"), None)
    if sel is None:
        print(f"[跳过] {name}: 无三选 Selector")
        continue
    inp5 = sel["inputs"][7]  # slot7 = input5
    if inp5.get("link") is not None:
        print(f"[跳过] {name}: input5 已连")
        continue
    # 在 links 里找 -> 本节点 input5 的链 (dslot == 7)
    hit = next((l for l in d["links"] if l[3] == sel["id"] and l[4] == 7), None)
    assert hit, (name, "links 里没有指向 input5 的链")
    inp5["link"] = hit[0]
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[补] {name}: input5.link = 链{hit[0]} (源 id{hit[1]})")
