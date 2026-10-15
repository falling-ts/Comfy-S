#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0016_建模拆图: 每条流(四宫/九宫)在 加载器IMAGE→切图 之间插入一个 FallingTSContinue 继续闸门。

⚠️ 已被取代, 请勿再运行(2026-10-15): 用户明确要求 0016 **不要用「继续」按钮**, 改为在每条流末尾
放一个「分组运行」节点(`FallingTSRunGroup`)汇聚该流全部 AutoSaveImage, 点它的「▶ 运行本组」
只跑本组。新方案见 `custom_nodes/ComfyUI-FallingTS/dev/_build-0016-modeling-split.py`(幂等生成整图),
本脚本仅作旧方案回溯保留。脚本已内置护栏: 图里存在 FallingTSRunGroup 时直接拒绝执行 ——
否则它会把 Continue 闸门重新插回去, 静默推翻新设计。


效果: Run 全图时两条流都只跑到各自 Continue(加载完成、缓存+阻塞, 不切图不保存);
点四宫 Continue 的「▶ 继续」→ partial 执行目标 = 其下游全部输出节点 = 四宫 4 个 AutoSave;
点九宫 Continue → 九宫 9 个 AutoSave。一条流一次点击, 互不影响。

接线: 加载器.IMAGE 原直连切图; 改为 加载器.IMAGE → Continue.any, Continue.any → 切图.images。
prefix 输出(MASK/prefix)不动 —— Continue 只闸住图像链路即可, prefix 是字符串无执行代价。

布局: 插入后各列右移重排(加载器 | Continue | 切图 | 取块 | 保存), 落盘后跑 wf_layout_all.py 校验。
幂等: 已存在对应 Continue 则跳过。
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
WF = os.path.join(_REPO, "workflows", "0016_建模拆图.json")

X_CONT4, X_CONT9 = 540, 840  # Continue 列 x: 四宫(加载器右缘460+80) / 九宫(右缘750+90)

# (新节点id, 加载器id, 切图id, x, 标题, y)
SPECS = [
    (1100, 1, 10, X_CONT4, "闸门 · 四宫流(点继续=只保存四宫)", 40),
    (1200, 2, 30, X_CONT9, "闸门 · 九宫流(点继续=只保存九宫)", 660),
]

d = json.load(open(WF, encoding="utf-8"))
nodes = {n["id"]: n for n in d["nodes"]}
links = {l[0]: l for l in d["links"]}
existing = {n["type"] for n in d["nodes"]}

# 护栏: 图已改用「分组运行」节点则拒绝执行, 避免把 Continue 闸门重新插回去推翻新设计
if "FallingTSRunGroup" in existing:
    raise SystemExit(
        "[拒绝] 0016 已改用 FallingTSRunGroup 分组运行节点, 本脚本(Continue 闸门方案)已废弃。\n"
        "       如需重建整图请跑 custom_nodes/ComfyUI-FallingTS/dev/_build-0016-modeling-split.py"
    )

for nid, loader_id, split_id, x, title, y in SPECS:
    if nid in nodes:
        print(f"跳过: Continue id{nid} 已存在")
        continue
    loader, split = nodes[loader_id], nodes[split_id]
    # 1) 找 加载器.IMAGE → 切图 的那条 link
    img_out = loader["outputs"][0]  # IMAGE
    lid = None
    for l in img_out["links"]:
        if links[l][3] == split_id:
            lid = l
            break
    assert lid is not None, f"加载器{loader_id}→切图{split_id} 连线未找到"
    # 2) 断开, 改接 Continue
    img_out["links"].remove(lid)
    links.pop(lid)
    old = next(i for i in split["inputs"] if i.get("link") == lid)
    new_link_id = d["last_link_id"] + 1
    d["last_link_id"] = new_link_id
    # Continue 节点
    cont = {
        "id": nid, "type": "FallingTSContinue", "pos": [x, y], "size": [270, 80],
        "flags": {}, "order": loader["order"] + 1, "mode": 0,
        "inputs": [{"localized_name": "any", "name": "any", "type": "*", "link": new_link_id}],
        "outputs": [{"localized_name": "any", "name": "any", "type": "*", "links": [new_link_id + 1]}],
        "properties": {"Node name for S&R": "FallingTSContinue"},
        "widgets_values": [], "widgets_values_named": {}, "title": title,
    }
    d["nodes"].append(cont)
    d["links"].append([new_link_id, loader_id, 0, nid, 0, "IMAGE"])
    d["links"].append([new_link_id + 1, nid, 0, split_id, old.get("slot_index", 0), "IMAGE"])
    d["last_node_id"] = max(d["last_node_id"], nid)
    old["link"] = new_link_id + 1
    print(f"[接] 加载器{loader_id} → Continue{nid} → 切图{split_id}")

json.dump(d, open(WF, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("完成, 请重跑 wf_layout_all.py 重排校验")
