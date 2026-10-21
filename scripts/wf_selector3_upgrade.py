#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 10 个 H3 工作流的采样 Switch 升级为 Selector 三选: 默认/8步/4步。

以 0031_首帧场景 已改造结构为模板:
- FallingTSSwitch(组3: 默认EasyCache|4步LoRA) -> FallingTSSelector(items="默认,8步,4步", total=3);
- 4步优化链保持不变(Sage6 -> LowVRAM24 -> 4步LoRA -> SigmaShift23 -> euler10 -> 步数4);
- 新建 8步链: LowVRAM24 -> 8步LoRA -> SigmaShift(6,3) -> euler(复用) -> 步数8;
- 默认链 EasyCache/res_multistep/20 不动;
- Selector 端口(3组x3名): 组1 model -> BasicScheduler.model + BasicGuider.model;
  组2 sampler -> SamplerCustomAdvanced.sampler; 组3 steps -> BasicScheduler.steps;
- FL2VA 系用 fl2v 8step, Ref2VA 系用 ref2v 8step。
幂等: 检测目标 Switch 已是 Selector 则跳过。
"""
import json
import os
import sys
import shutil

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
WF_DIR = os.path.join(_REPO, "workflows")

# 工作流 -> (采样Switch id, 4步LoRA节点id, 8步LoRA文件)
LORA_8_FL2V = "minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"
LORA_8_REF2V = "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"
TARGETS = {
    "0013_首图建模":        (130, LORA_8_FL2V),
    "0014_参考建模":        (130, LORA_8_REF2V),
    "0030_文生场景":        (113, LORA_8_FL2V),
    "0032_参考场景":        (130, LORA_8_REF2V),
    "0040_文生视频":        (63,  LORA_8_FL2V),
    "0041_首帧视频":        (910, LORA_8_FL2V),
    "0042_首尾视频":        (910, LORA_8_FL2V),
    "0043_关键帧视频":      (908, LORA_8_REF2V),
    "0044_参考视频":        (910, LORA_8_REF2V),
}


def main():
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    for name, (sw_id, lora8) in TARGETS.items():
        if only and not any(o in name for o in only):
            continue
        p = os.path.join(WF_DIR, f"{name}.json")
        d = json.load(open(p, encoding="utf-8"))
        nodes = {n["id"]: n for n in d["nodes"]}
        sw = nodes.get(sw_id)
        if sw is None:
            print(f"[跳过] {name}: 无 Switch id{sw_id}")
            continue
        if sw["type"] == "FallingTSSelector":
            print(f"[跳过] {name}: id{sw_id} 已是 Selector")
            continue

        links = d["links"]  # [id, src, sslot, dst, dslot, type]
        max_node = max(n["id"] for n in d["nodes"])
        max_link = max(l[0] for l in links)

        # ── 1. 收集 Switch 现有输入 (组: 1=model, 2=sampler, 3=steps) ──
        sw_inputs = {i["name"]: i.get("link") for i in sw["inputs"]}
        lora4_lid = sw_inputs.get("true_1")      # 组1 true = 4步 SigmaShift 输出
        ecs_lid   = sw_inputs.get("false_1")     # 组1 false = EasyCache 输出
        ks4_lid   = sw_inputs.get("true_2")      # euler (4步采样器)
        ks20_lid  = sw_inputs.get("false_2")     # res_multistep
        st4_lid   = sw_inputs.get("true_3")      # 步数4
        st20_lid  = sw_inputs.get("false_3")     # 步数20
        assert all(x is not None for x in (lora4_lid, ecs_lid, ks4_lid, ks20_lid, st4_lid, st20_lid)), name

        src_of = {l[0]: l[1] for l in links}
        lora4_id = src_of[lora4_lid]             # 4步 SigmaShift 节点
        ecs_id   = src_of[ecs_lid]               # EasyCache
        ks4_id   = src_of[ks4_lid]               # euler KSamplerSelect
        ks20_id  = src_of[ks20_lid]              # res_multistep KSamplerSelect
        st4_id   = src_of[st4_lid]               # PrimitiveInt 4
        st20_id  = src_of[st20_lid]              # PrimitiveInt 20

        # 4步 LoRA 节点 = 4步 SigmaShift 的上游
        lora4_node = nodes[lora4_id]
        lora4_up = lora4_node["inputs"][0].get("link")
        lora4_src = src_of[lora4_up]             # 应为 LowVRAMAttention(id24 同构)
        # 8步 LoRA 的上游 = 与 4步 LoRA 同源 (Sage -> LowVRAM 优化链)
        lora8_up_src = lora4_src

        # ── 2. 新节点: 8步LoRA / 8步SigmaShift / 步数8 ──
        n_lora8, n_shift8, n_step8 = max_node + 1, max_node + 2, max_node + 3
        L8 = lora8_up_src  # LowVRAMAttention
        lora8_node = {
            "id": n_lora8, "type": "LoraLoaderModelOnly", "pos": [0, 0], "size": [270, 140],
            "flags": {}, "order": 0, "mode": 0,
            "inputs": [{"name": "model", "type": "MODEL", "link": max_link + 1}],
            "outputs": [{"name": "MODEL", "type": "MODEL", "links": [max_link + 2], "slot_index": 0}],
            "properties": {"Node name for S&R": "LoraLoaderModelOnly"},
            "widgets_values": [lora8, 1],
        }
        shift8_node = {
            "id": n_shift8, "type": "MiniMaxH3SigmaShift", "pos": [0, 0], "size": [270, 120],
            "flags": {}, "order": 0, "mode": 0,
            "inputs": [{"name": "model", "type": "MODEL", "link": max_link + 2}],
            "outputs": [{"name": "MODEL", "type": "MODEL", "links": [max_link + 3], "slot_index": 0}],
            "properties": {"Node name for S&R": "MiniMaxH3SigmaShift"},
            "widgets_values": [6, 3],
        }
        step8_node = {
            "id": n_step8, "type": "PrimitiveInt", "pos": [0, 0], "size": [240, 90],
            "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [{"name": "INT", "type": "INT", "links": [max_link + 6], "slot_index": 0}],
            "properties": {"Node name for S&R": "PrimitiveInt"},
            "widgets_values": [8, "fixed"],
        }
        d["nodes"] += [lora8_node, shift8_node, step8_node]

        # ── 3. Switch -> Selector 改造 ──
        MT, ST, IT = "MODEL", "SAMPLER", "INT"
        new_inputs = [
            {"name": "input1", "type": "*", "link": ecs_lid},     # 组1 默认 = EasyCache
            {"name": "input2", "type": "*", "link": max_link + 3},  # 组1 8步 = 新SigmaShift
            {"name": "input3", "type": "*", "link": lora4_lid},   # 组1 4步 = 4步SigmaShift
            {"name": "input4", "type": "*", "link": ks20_lid},    # 组2 默认 = res_multistep
            {"name": "input5", "type": "*", "link": None},        # 组2 8步 = euler(新建连线)
            {"name": "input6", "type": "*", "link": ks4_lid},     # 组2 4步 = euler
            {"name": "input7", "type": "*", "link": st20_lid},    # 组3 默认 = 20
            {"name": "input8", "type": "*", "link": max_link + 6},  # 组3 8步 = 8
            {"name": "input9", "type": "*", "link": st4_lid},     # 组3 4步 = 4
        ]
        sw["type"] = "FallingTSSelector"
        sw["inputs"] = [
            {"name": "items", "type": "STRING", "link": None},
            {"name": "total", "type": "INT", "link": None},
            {"name": "selection", "type": "COMBO", "link": None},
        ] + new_inputs
        sw["properties"] = {"Node name for S&R": "FallingTSSelector"}
        # outputs: selected/index + selected_value_1/2/3 (保留原 outputs 槽 0-2 的下游)
        old_outs = sw.get("outputs", [])
        # 原 Switch outputs: output_1/2/3 三个, 分别连到 Scheduler.model+Guider.model / Sampler / Scheduler.steps
        # Selector: slot0=selected, slot1=index, slot2=selected_value_1(model), slot3=selected_value_2(sampler), slot4=selected_value_3(steps)
        for o in old_outs:
            o["links"] = o.get("links") or []
        # 重排: 把原 output_1(模型) links 移到 slot2, output_2(sampler) 移到 slot3, output_3(steps) 移到 slot4
        def links_of(i):
            return old_outs[i].get("links") or [] if i < len(old_outs) else []
        model_links, sampler_links, steps_links = links_of(0), links_of(1), links_of(2)
        # 修正每条链的 origin_slot
        for l in links:
            if l[0] in model_links: l[2] = 2
            elif l[0] in sampler_links: l[2] = 3
            elif l[0] in steps_links: l[2] = 4
        sw["outputs"] = [
            {"name": "selected", "type": "STRING", "links": [], "slot_index": 0},
            {"name": "index", "type": "INT", "links": None, "slot_index": 1},
            {"name": "selected_value_1", "type": "*", "links": model_links, "slot_index": 2},
            {"name": "selected_value_2", "type": "*", "links": sampler_links, "slot_index": 3},
            {"name": "selected_value_3", "type": "*", "links": steps_links, "slot_index": 4},
        ]
        sw["widgets_values"] = ["默认,8步,4步", 3, "4步"]

        # ── 4. 新链路 ──
        # 8步模型链: L8 -> lora8 -> shift8 -> selector(input2)
        # 8步采样器: ks4(euler) -> selector(input5)
        links += [
            [max_link + 1, L8, 0, n_lora8, 0, MT],
            [max_link + 2, n_lora8, 0, n_shift8, 0, MT],
            [max_link + 3, n_shift8, 0, sw_id, 4, MT],   # selector input2 (inputs 数组下标 3+1=4)
            [max_link + 5, ks4_id, 0, sw_id, 7, ST],     # selector input5 (下标 3+4=7)
            [max_link + 6, n_step8, 0, sw_id, 10, IT],   # selector input8 (下标 3+7=10)
        ]
        # 源输出口 fan-out 补记
        for nid, lid in ((L8, max_link + 1), (ks4_id, max_link + 5)):
            for o in nodes[nid]["outputs"]:
                if o["links"] is not None and lid not in o["links"]:
                    o["links"].append(lid)
                    break

        # ── 5. 布局: 新节点摆到 Switch 左下空白 (暂置 Switch 下方偏左, 后续统一排布) ──
        sx, sy = sw["pos"]
        lora8_node["pos"] = [sx - 700, sy + 700]
        shift8_node["pos"] = [sx - 350, sy + 700]
        step8_node["pos"] = [sx - 700, sy + 900]

        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"[改] {name}: Switch{sw_id}->Selector, +8步链(LoRA{n_lora8}/Shift{n_shift8}/Step{n_step8}, 上游={L8})")


if __name__ == "__main__":
    main()
