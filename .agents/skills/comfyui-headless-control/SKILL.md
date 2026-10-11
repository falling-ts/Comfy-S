---
name: comfyui-headless-control
description: |
  无头(纯 HTTP)驱动本地 ComfyUI + FallingTS 插件流水线: 跑工作流, 然后操作节点按钮 ——
  保存图片/视频/音频、截帧、完成、放行「继续」分段闸门 —— 以及读写参数化它们的 Markdown 数据表。
  当一个脚本或 agent 需要把 ComfyUI 界面按钮的动作在代码里复现时使用, 包括: 保存产物到 output、
  从视频里抓帧、标记截帧完成、放行继续节点跑下一段、刷新 mdtable 状态、排查「无头运行静默用了
  过期或缺失的输入」。英文触发词: save artifact, extract frame, finish/done, continue gate,
  partial_execution_targets, md table refresh, silent None, stale snapshot。
  与 comfyui-workflow-runner(负责工作流 JSON → API prompt 转换与提交)互补: 那个管「跑起来」,
  本技能管「跑起来之后怎么操作它」。
---

# 无头驱动本地 ComfyUI + FallingTS 流水线

> 本文件全部结论来自 **2026-09-23 对本机源码与端点的实测**(ComfyUI 0.37.0, `127.0.0.1:8188`),
> 不是推测。实测方式:先真提交工作流把媒体缓存进节点,再逐个打按钮端点、回读状态、检查落盘产物。
> 复现方法见文末「实测记录」。

## 0. 一句话结论

这套插件的**所有功能性按钮都有对应 HTTP 端点**,而且**都不重跑工作流** —— 它们复用 `execute` 时
缓存的媒体(模块级 `_last_output[node_id]`)。所以「跑一次 → 反复操作」是它的设计语义,不是绕过。
唯一真正的例外是 `select_file`(弹原生文件对话框,**会阻塞服务端线程**,无头绝对不要调)。

## 1. 状态模型(先理解这个,否则必然静默出错)

| 事实 | 依据 |
|---|---|
| `FallingTSMarkDownTable.execute(data, id)` **从不读 md 文件**,只用序列化进工作流 JSON 的控件状态 `data` | `mdtable/nodes.py:643-675`;`parse_md_file` 全插件只在 `/read` 路由被调用(`nodes.py:492`) |
| `data = {md_path, fields, selected:{id, values}}`;同时存在于工作流 JSON 的 `widgets_values[0]` 与 `widgets_values_named.data`,两者**逐字节等价** | 实测对 `0044_参考视频.json` 节点 1 压缩比较,长度与内容一致 |
| 前端「🔄 刷新」= `GET /fallingts_mdtable/read` → 覆盖**前端内存**里的 state → 要靠前端保存工作流才落盘。**它不是持久化 API** | `web/js/md_table.js:1152-1190` |
| `IS_CHANGED` 签名 = `data` 的 JSON 全量 + 已解析到的媒体文件 mtime;**不含 md 的 mtime/哈希** ⇒ **只改 md 不会重跑** | `mdtable/nodes.py:621-641` |
| `data is None` 时 **sticky 回退上一次输出** | `mdtable/nodes.py:659-661` |
| 媒体引用解析失败 → **静默 `None`**,无日志、无异常、无告警 | `mdtable/nodes.py:665-671` |
| 所有按钮状态(`_last_output` / `_released` / `_data_cache` / `_done`)都是**模块级内存**,按 `str(node_id)` 索引 ⇒ **服务重启即失** | 各 `nodes.py` 模块级字典 |
| 端点 URL 里的 `{node_id}` **必须等于工作流里的节点 id**(如 `901`/`952`) | 各 `_handle_*` 用 `request.match_info["node_id"]` |

**mdtable 槽位约定(位置式,不是固定语义)**:`0` = ID;`1..9` = `<Picture 1..9>`;`10..12` = `<Video 1..3>`;
`13..15` = `<Audio 1..3>`;`16` = 提示词;`17` = 宽;`18` = 高;`19` = 秒数;末槽 = 整行 JSON。

**产物落盘**:ID 槽接到各保存/预览节点的 `filename_prefix` ⇒ 产物 = `output/<当前工作流名>/<ID>.<ext>`
(即 `media/七纹刻印/<工作流名>/`)。这正是 `@{表名/ID}` 严格趟能命中的原因。

**`@{表名/ID}` 解析**(`mdtable/nodes.py:175-228`):严格趟(按目录段精确找,`stem == ref or stem.startswith(ref+"_")`)
→ 兜底趟(在 output/input 下全区递归,**只下探 `^\d+[-_]` 子目录**,同族目录优先)。**两趟都没命中就 `return None`**。

## 2. 节点按钮 → HTTP 端点(全表)

✅ = 本机实测通过;○ = 源码确认(同模式,未单独实跑)。

| 节点 | 按钮 / 动作 | 端点 | 请求体要点 | |
|---|---|---|---|---|
| PreviewImageSave | 保存 | `POST /preview-image/save/{id}` | `filename_prefix`,`filename_prefix_linked`,`filename_suffix`,`format`,`bit_depth`,`input_color_space`,`workflow_name` | ✅ |
| PreviewImageSave | (回读) | `GET /preview-image/image-url/{id}` | — | ✅ |
| **AutoSaveImage** | **无按钮(执行到即保存)** | 无自己的端点;预览回读复用 `GET /preview-image/image-url/{id}` | 落盘在 execute 内完成:`{前缀}{后缀}.{格式}` 直接写 output(同名覆盖、无序号);**无头提交要自带工作流名**(`extra_pnginfo` 顶层 `workflow_name`,或 `workflow.extra.fallingts_workflow_name`),否则子目录退回 output 根;widget 列表与 `PreviewImageSave` 完全相同 | ✅ |
| PreviewVideo | 保存 | `POST /preview-video/save/{id}` | `filename_prefix`,`filename_prefix_linked`,`filename_suffix`,`workflow_name` | ✅ |
| PreviewVideo | **截帧** | `POST /preview-video/frame/{id}` | `mode`(`time`/`frame`)、`append`、`frame_index` 或 `position_seconds` | ✅ |
| PreviewVideo | 帧列表 ✕ | `POST /preview-video/frame-remove/{id}` | **`frame_index`** 或 `{"clear":true}` | ✅ |
| PreviewVideo | **完成** | `POST /preview-video/done/{id}` | `{}` | ✅ |
| PreviewVideo | (回读) | `GET /preview-video/state/{id}`、`/video-url/{id}` | — | ✅ |
| PreviewVideo | (Run 前) | `POST /preview-video/reset` | `{}` | ✅ |
| PreviewAudioSave | 保存 | `POST /preview-audio/save/{id}` | 同图片 + `quality` | ○ |
| PreviewAudioSave | (回读) | `GET /preview-audio/audio-url/{id}` | — | ○ |
| PreviewAudioSave | (Run 前) | `POST /preview-audio/reset` | `{}` | ○ |
| FallingTSAudioTrim | 保存 | `POST /audio-trim/save/{id}` | 同音频 + `segment_index` | ○ |
| FallingTSAudioTrim | **截段** | `POST /audio-trim/segment/{id}` | **`start`,`duration`** | ○ |
| FallingTSAudioTrim | 段列表 ✕ | `POST /audio-trim/segment-remove/{id}` | `index` | ○ |
| FallingTSAudioTrim | **完成** | `POST /audio-trim/done/{id}` | `segments` 可选 | ○ |
| FallingTSAudioTrim | (回读) | `GET /audio-trim/waveform/{id}`、`/audio-url/{id}` | — | ○ |
| FallingTSContinue | **▶ 继续** | `POST /proceed/continue/{id}` | `{}`;**须先跑到该节点**,否则 400 | ✅ |
| FallingTSContinue | (Run 前) | `POST /proceed/reset` | `{}` | ✅ |
| FallingTSMarkDownTable | 打开数据 | 无端点(UI 弹窗;数据用 `GET /read` 拿) | — | — |
| FallingTSMarkDownTable | 🔄 刷新 | `GET /fallingts_mdtable/read?path=` | 仅改前端内存,见 §4-④ | ✅ |
| FallingTSMarkDownTable | 选文件 | `POST /fallingts_mdtable/select_file` | ❌ **阻塞** | ✅(超时) |
| (通用) | 浏览/解析/预览 | `GET /fallingts_mdtable/{browse,resolve,preview}` | query:`path`,`kind` | ✅(前二) |
| 遮罩编辑器 | 保存 | `POST /fallingts_mask/rename` | `node_id`,`image_ref`,`base`,`force`,`name`,`workflow_id` | ○ |
| 灯箱/中键/通知/布局类 | — | 无服务端状态,与自动化无关 | — | — |
> **`AutoSaveImage`(执行即保存)**:`0035_场景截帧` 的十个图片保存节点与 `0050_视频截帧` 的三个(首帧/关键帧/尾帧)都是它 —— **没有「保存」按钮、也没有自己的端点**, 执行到该节点就把产物写进 output(同名覆盖、无序号)。无头路径**不要把 `/preview-image/save/{id}` 用在这些节点上**(那是 `PreviewImageSave` 的), 并记得在提交时带工作流名, 否则产物落回 output 根而不是 `<工作流名>/` 子目录。

> 遮罩编辑器保存时, 若带 `name`(来自「加载图像」节点 `FallingTSLoadImage` 的「名称」输入框), 成品按
> `output/0010_灰度遮罩/` 里已有 5 位编号的最大值 +1 命名, 即 `<5位编号>_<name>.png`(撞号顺延); 不带 `name` 仍走 `base`/预览缓存/`mask-{ts}` 旧口径。

## 3. 必须由调用方自己复刻的三段前端逻辑

这是「能不能」的真门槛 —— 端点本身都可用,但这三件事**只存在于前端 JS 里**:

1. **Run 之前 POST 各 reset**:`/preview-image/reset`、`/preview-video/reset`、`/preview-audio/reset`、`/audio-trim/reset`。
   前端是包装 `app.queuePrompt`、在**默认 Run**(`queueNodeIds` 为空)时发的。无头不做的话
   `_reset_generation` 不递增 → ComfyUI 执行缓存会把节点**跳过**(插件 AGENTS.md 记录过这个翻车)。
2. **`partial_execution_targets`**:前端的 `collectOutputsAfter(anchor)` 从锚点下游 BFS 收集**输出节点**,
   **遇到下一个 `FallingTSContinue` 就停**(`web/js/proceed.js:92-118`)。无头必须自己在 workflow JSON 上算这个集合。
3. **点「继续」前 POST `/free`**:`{"unload_models":true,"free_memory":true}`,释放显存,避免上下两段模型互挤。

## 4. 实测踩到的坑(每条都真实发生过)

1. **`POST /fallingts_mdtable/select_file` 会卡住** —— 它弹原生文件对话框并阻塞等待,实测请求超时、
   占住服务端线程。要换表请直接写 `md_path`,不要调它。
2. **`frame-remove` 的字段名是 `frame_index`** —— 传 `{"index":0}` 会**静默 no-op 但返回 HTTP 200**。
   凡是「字段名错也返 200」的端点,自动化**必须回读 state 校验**。
3. **`/preview-video/frame/{id}` 返回原始 PNG 字节**(前端用 `resp.blob()`),不是 JSON。
4. **「🔄 刷新」不是 API 动作** —— 它只改前端内存,落盘靠前端保存工作流。无头路径必须自己把
   `/read` 结果写进工作流 JSON,或直接放进 API 载荷的 `data`。⚠️ 曾有脚本只替换提示词字符串、
   漏写其它字段(如 `<Picture 4>` 参考图),导致表与快照静默不一致。
5. **状态纯内存** —— 服务一重启 `_last_output` 就空,`save`/`frame`/`done` 全部 400。**跑完立刻操作**是硬约束。
6. **`/preview-*/clear` 与 `/audio-trim/clear` 是保留的 no-op**,别指望它清状态。
7. **`COMFY_DYNAMICCOMBO_V3`(核心节点 `BlockSparseAttention` 的 `selection`)会让「按位置对齐控件」的
   转换器整体错位一格** —— 前端把动态组合展开成 `selection` + `selection.tau` 两个控件,`widgets_values`
   比 `/object_info` 多一个。**必须按名字对齐**,且 API 载荷里是**扁平点号**形式:
   `"selection":"sol-attn"` + `"selection.tau":1.3`(框架按 `build_nested_inputs` 组装成 `execute` 收到的 dict)。
   按位置对齐会得到 `min_tokens=''` / `start_percent=1.3` 之类的校验失败。
8. **`Reroute` 在 API 图里不存在** —— 转换时必须穿透到真实源;`0044_参考视频` 的 ID 槽正是经 `Reroute 900`
   才扇出到 7 个保存节点的 `filename_prefix`,不穿透就全部丢链。

## 5. 一次完整的无头流程(骨架)

```python
# ① 取状态并把 md 最新值灌进状态(等价于前端点「刷新」,但真落盘)
state = wf["nodes"][mdtable_id]["widgets_values"][0]
r = GET(f"/fallingts_mdtable/read?path={quote(state['md_path'])}")
row = next(x for x in r["rows"] if x["id"] == want_id)
state["fields"], state["selected"] = r["fields"], {"id": want_id, "values": row["values"]}
#    写回工作流 JSON 时: 同时更新 widgets_values[0] 与 widgets_values_named.data

# ② 建 API prompt(按名字对齐控件, 见 §4-⑦), 注入 state

# ③ 强校验(见 §6): 任一 @{...} 解析失败 / 快照与 md 不一致 => 拒绝提交

# ④ Run 前 reset(见 §3-1)
for ep in ("/preview-image/reset", "/preview-video/reset", "/preview-audio/reset", "/audio-trim/reset"):
    POST(ep)

# ⑤ 提交(全量; 或分段: partial_execution_targets=[本段输出节点 id])
pid = POST("/prompt", {"prompt": prompt, "partial_execution_targets": [...]})["prompt_id"]
while pid not in GET(f"/history/{pid}"): sleep(5)

# ⑥ 操作按钮
POST(f"/preview-video/frame/{vid_id}", {"mode": "time", "append": True, "position_seconds": 1.0})
POST(f"/preview-video/done/{vid_id}", {})
POST(f"/preview-video/save/{vid_id}", {"filename_prefix": "0021_场景拉镜",
     "filename_prefix_linked": False, "filename_suffix": "", "workflow_name": "0044_参考视频"})
# ⑦ 回读校验(防 §4-②)
assert GET(f"/preview-video/state/{vid_id}")["done"] is True

# ⑧ 放行下一段
POST("/free", {"unload_models": True, "free_memory": True})
POST(f"/proceed/continue/{continue_id}")        # 未跑到该节点 => 400 "没有上游数据"
# ⑨ 再以 partial_execution_targets=[下游输出节点] 提交
```

## 6. 提交前的强校验(本机已知的数据健康问题)

无头自动化会把静默错误放大,提交前至少查这几项(均已在本机实测确认存在):

| 检查 | 本机现状(2026-09-24 重构后) |
|---|---|
| 每个 `@{...}` 必须能解析 | 去重后 10 条引用里 **2 条静默失败**:`@{0031_首帧场景/00002_书房旋镜四图}`(文件其实叫 `00001_书房旋镜四图`)、`@{0044_参考视频/00001_书房开场四镜尾帧}`(从未存在) |
| 兜底趟是否「串版」 | 2026-09-24 起保存类节点**优先用工作流的 md 表文件名**作产物子目录(`custom_nodes/ComfyUI-FallingTS/output_subdir.py`),`@{表名/ID}` 因此走**严格命中**、不再靠同族兜底。代价:`0011_万物建模` 与 `00110_万物建模_QI2.1` 现在**落同一个目录**,同一行 ID 的产物互相覆盖 |
| 工作流里的快照 id 是否还在 md 里 | **5 张空壳表**(0060~0064)的工作流存的是**绝对路径 + 已不存在的 id**(死快照);`0061_环境音效.md` 因分隔行写成 `:--`(需 `-{3,}`)**整表解析失败**(2026-10-05 复核: 分隔行已修为 `| :--- | :---------- | :------ |`, `-{3,}` 条件满足, 解析正常)。⚠️ 0050/0051/0070 已于 2026-10-02 **去掉 md 表节点**(三张表也一并删除): 它们不再刷新任何表, 源文件直接由加载节点的下拉(或 `video_in`/`audio_in`)给出 |
| 是否有保存节点同名覆盖 | `00110_万物建模_QI2.1` 的 ID 同时接两个 `PreviewImageSave`(42/62),两者 `filename_suffix` 皆空 ⇒ 都算成 `<ID>.png`,**互相覆盖** |
| 重复 id | `parse_md_file` 用 `seen` 集合**静默丢弃**重复行,不告警 |
| 只解析第一张表 | 找到表头+分隔行后 `break`,文件里第二张表及其后内容**一律忽略** |

## 7. 运行账本(无头自动化必须补的一环)

本机目前**没有任何持久化运行记录**:`ComfyUI/user/comfyui.db` 只有 `alembic_version` 一张表;
唯一记录是工作流 JSON 里「下次会跑什么」的快照 + 内存态 `/history`(重启即失)。
**参考图会消失**(实测发生过:参考图被删后 `@{...}` 静默变 None,系统毫无察觉),所以账本必须记
**路径 + 内容哈希**,只记路径等于没记。每次运行追加一条(JSONL 或一 run 一文件):

```json
{"run_id":"...","ts":"...","table":"0044_参考视频","row":"00001_书房开场四镜",
 "prompt_sha256":"...","prompt":"<实际提交的全文>",
 "refs":[{"slot":"<Picture 4>","ref":"@{...}","path":"...","sha256":"..."}],
 "width":832,"height":480,"length_frames":345,"seed":...,
 "workflow":"0044_参考视频.json","workflow_sha256":"...",
 "actions":[{"endpoint":"/preview-video/save/901","body":{...},"http":200,"artifact":"..."}],
 "status":"success"}
```

**纪律**:跑完**追加**账本,不要「清空」。覆盖式清空会直接销毁可复现性。

## 附:实测记录(2026-09-23,可复现)

| 动作 | 结果 |
|---|---|
| `GET /fallingts_mdtable/read`(`0011_万物建模.md`) | `ok=True`,返回该表全部行与字段 |
| `GET /fallingts_mdtable/browse`(`stories/七纹刻印`) | `ok=True`,33 条目 |
| `GET /fallingts_mdtable/resolve`(`@{0011_万物建模/00001_陈落}`) | `ok=True` → `output\0011_万物建模\00001_陈落.png`(2026-09-23 实测时写的是 `_QI2.1` 目录;2026-09-24 该目录已改名并入表名目录) |
| `POST /fallingts_mdtable/select_file` | **读取超时**(阻塞) |
| 提交一个便宜工作流 → `POST /preview-image/save/<预览节点 id>` | **200** `已保存 N 张: <dir>/...`,盘上确认 |
| 构造 48 帧图 → `POST /preview-video/frame/952` | **200**,返回体 PNG 头合法 |
| `GET /preview-video/state/952` | `{selected_frames:[25], done:false, total_frames:48, has_video:true}` |
| `POST /preview-video/frame-remove/952` | **200**(但传错字段名会静默 no-op) |
| `POST /preview-video/save/952` | **200** `已保存: <dir>/probe.mp4`,盘上确认 |
| `POST /preview-video/done/952` | **200** `{done:true}`,state 随之变 `done:true` |
| `POST /proceed/reset` | **200** `{status:"ok"}` |
| `POST /proceed/continue/43`(无缓存) | **400** `没有上游数据, 请先运行到该节点` |

复现脚本范式(先跑一个便宜工作流把媒体缓存进节点,再打按钮端点):用一次性脚本经 stdin 就地执行(`.venv\Scripts\python.exe - <<'PY' ... PY`),不落盘。
