#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复三选升级脚本的上游 bug: 8步LoRA 误接在 4步LoRA 之后(会双LoRA叠加)。

正确: 8步LoRA 上游 = 4步LoRA 的上游(MiniMaxLowVRAMAttention), 与4步链共享 Sage->LowVRAM 段。
幂等: 检测 8步LoRA 上游已是 LowVRAMAttention 则跳过。
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
WF_DIR = os.path.join(_REPO, "workflows")
TARGETS = {
    "0013_首图建模": 139,
    "0014_参考建模": 141,
    "0030_文生场景": 138,
    "0032_参考场景": 141,
    "0040_文生视频": 72,
    "0041_首帧视频": 919,
    "0042_首尾视频": 919,
    "0043_关键帧视频": 917,
    "0044_参考视频": 929,
}

for name, lora8_id in TARGETS.items():
    p = os.path.join(WF_DIR, f"{name}.json")
    d = json.load(open(p, encoding="utf-8"))
    nodes = {n["id"]: n for n in d["nodes"]}
    links = {l[0]: l for l in d["links"]}

    lora8 = nodes[lora8_id]
    up_lid = lora8["inputs"][0]["link"]
    up_id = links[up_lid][1]
    if nodes[up_id]["type"] == "MiniMaxLowVRAMAttention":
        print(f"[跳过] {name}: 8步LoRA 上游已是 LowVRAM(id{up_id})")
        continue

    # 4步LoRA = Selector input3(id=links[slot5][1]) 的上游
    sel = next(n for n in d["nodes"]
               if n["type"] == "FallingTSSelector"
               and n.get("widgets_values", [""])[0] == "默认,8步,4步")
    # 沿 input3 链向上穿透 Switch/嵌套层, 找第一个 LoraLoaderModelOnly
    nid = links[sel["inputs"][5]["link"]][1]
    lora4_id = None
    seen = set()
    while nid is not None and nid not in seen:
        seen.add(nid)
        n = nodes[nid]
        if n["type"] == "LoraLoaderModelOnly":
            lora4_id = nid
            break
        lid = n["inputs"][0].get("link") if n.get("inputs") else None
        nid = links[lid][1] if lid is not None and links[lid][1] in nodes else None
    assert lora4_id is not None, (name, "未找到 4步LoRA")
    lora4 = nodes[lora4_id]
    lowvram_id = links[lora4["inputs"][0]["link"]][1]  # 4步LoRA 上游(Sage 或 LowVRAM, 与 4步链共享同段)
    assert nodes[lowvram_id]["type"] in ("MiniMaxLowVRAMAttention", "MiniMaxH3MemoryEfficientSageAttentionPatch"), (name, nodes[lowvram_id]["type"])

    # 重接: 链 (up_lid): 源端改为 lowvram_id
    for l in d["links"]:
        if l[0] == up_lid:
            old_src = l[1]
            l[1] = lowvram_id
            break
    # 源输出 fan-out: 旧源移除该 link, 新源追加
    for o in nodes[old_src]["outputs"]:
        if o.get("links") and up_lid in o["links"]:
            o["links"].remove(up_lid)
            break
    for o in nodes[lowvram_id]["outputs"]:
        if o.get("links") is not None and up_lid not in o["links"]:
            o["links"].append(up_lid)
            break

    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[修] {name}: 8步LoRA id{lora8_id} 上游 {old_src}({nodes[old_src]['type']}) -> {lowvram_id}(MiniMaxLowVRAMAttention)")
