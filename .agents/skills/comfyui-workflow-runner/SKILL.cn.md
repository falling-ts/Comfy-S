---
name: comfyui-workflow-runner
description: |
  通过 HTTP API 无头运行本地 ComfyUI 工作流，无需触碰浏览器：把保存的工作流 JSON 转成 API prompt 格式、
  按 md 文件刷新 FallingTS 数据表状态（等价于点击该节点的刷新按钮）、提交 /prompt、轮询 /history 至完成，
  并对产出做探测与抽帧校验。适用于需要自主执行或重跑工作流、md 数据表里改过的提示词必须真正生效、
  或需要对成片做客观检查（时长、帧率、有无音轨、运动与连贯性）的场合。另附 H3 的两组多轮实测结论：
  场景视频（各方案性能对比、单图锚点为何反超多图参考、提示词四条硬经验、旋转速率上限）
  与镜头顺序／时长（散文为何定不住 ref2video 的镜头位置、硬锚点接线配方及其布局例外；另记：非必要不加硬锚点，效果更好）。
  不适用于撰写提示词文本或开发自定义节点。
---

# ComfyUI 工作流无头运行器

用脚本驱动本地 ComfyUI（`http://127.0.0.1:8188`）：**改源数据 → 刷新数据表节点 → 提交 → 检查产出**。
不需要浏览器、不需要人点 Run、也不需要手工同步前端状态。

## 何时使用

- 工作流需要被执行并检查产出，而用户不会替你点 Run。
- `stories/**/*.md` 数据表里的提示词刚改过 —— 工作流 JSON 里仍是**旧文本**，除非有东西去刷新它。
- 需要真实渲染来做 A/B 对比或回归检查。
- 成片里某个镜头的**顺序／位置／时长**不对，而提示词里的时间码被无视了 —— 见
  `references/h3-shot-order-anchoring.md`。

## 核心原理（为什么什么都不用点）

`FallingTSMarkDownTable.execute(data, id)` 只消费前端序列化进工作流的**控件状态** `data`
（`{md_path, fields, selected}`），**它自己从不读 md 文件**。前端的"刷新"按钮只是调用
`GET /fallingts_mdtable/read?path=...`，把返回的行写回该状态。因此调同一个接口、自己构造 `data`
与之等价 —— 而且完全不需要浏览器。

## 操作步骤

1. **转换并刷新**
   `python scripts/workflow-to-prompt.py "<glob>" --refresh-md --dump prompt.json`
   确认节点数，以及 mdtable 的提示词长度已变成新值（长度没变说明没刷新，等于在静默重跑上一版提示词）。
2. **干跑检查** —— 在消耗 GPU 之前抽查几个关键节点（加载器、采样器、SigmaShift、数据表）。
3. **提交** —— 加 `--submit`。脚本会 POST `/prompt`、轮询 `/history/<id>`，并打印产出的文件名。
4. **校验产出** —— 不要只看"成功"，要探测并**看**它：
   - `ffmpeg -i file.mp4` → 时长、分辨率、帧率、**以及是否存在音轨**
   - 抽帧拼板：`ffmpeg -y -i f.mp4 -vf "fps=1/N,scale=640:-1,tile=4x2" -frames:v 1 grid.png`
   - 读 `grid.png`，据此判断内容、连贯性与一致性
   - 运动量：`python scripts/motion-profile.py f.mp4 [--crop w:h:x:y]` —— 去噪后逐帧差分的**每秒中位数**。
     **不要只靠 `pblack` 判断"被摄体动没动"**：H3 颗粒极重时它会饱和（见
     `references/output-verification.md` §3）。
   - 工作流里有帧锚点时，把锚点帧抽出来与参考图**逐格比对**（`references/h3-shot-order-anchoring.md` §4.4）。
5. **把预览存成 output/** —— 预览节点只写 `temp/`，要用插件的保存端点才落成正式文件
   （端点表见技能 `comfyui-headless-control`）。

## 陷阱（每一条都花过一轮真实调试）

- **`widgets_values` 包含"已被转成输入"的 widget**。被连线的 widget 仍占数组里的位置，所以必须先按
  **完整** widget 列表 zip、**再**跳过被连线的；先过滤会整体错位 —— `PreviewImageSave.format` 会静默
  拿到 `filename_suffix` 的值。**这类错误不报错**，因为错的值仍是合法值。
- **优先用 `widgets_values_named` 按名字取，不要只靠位置 zip；注意动态子控件。**
  `COMFY_DYNAMICCOMBO_V3` 展开出的子控件（如 `BlockSparseAttention` 的 `selection.tau`、
  `SaveVideo` 的 `format.codec`）在 `/object_info` 里查不到，却仍占 `widgets_values` 的一格 ——
  按位置 zip 会让其后控件全体前移（`start_percent` 收到 1.3、`min_tokens` 收到 ""）；
  而它的 API 键是 `<父>.<子>`，是**必填输入**，整条丢掉就报 `Required input is missing: tau`。
  两个方向都真踩过。做法：按名字映射，并补注入「父名在控件表内」的动态子控件。
- **`Reroute` 在 API 图里不存在**。必须把下游引用解析到真实源节点，否则那些输入会丢失连接。
- **`MarkdownNote` / `Note` 是纯前端节点** —— 跳过。
- **`mode: 4`（bypass）与 `mode: 2`（mute）** 需要显式处理；脚本目前跳过并报告。
- **执行缓存**：字节完全相同的工作流会秒回缓存。做 A/B 时改 seed 或提示词，否则你会"测"到一次
  5 秒的假渲染。
- **`--refresh-md` 只注入本次 API 载荷，不回写工作流文件**。磁盘上的 mdtable 快照仍是旧的，下次
  F5（或前端任何一次保存）会看到旧提示词。要让文件与 md 一致，必须自己
  `GET /fallingts_mdtable/read`，并把结果写回 **`widgets_values[0]` 与 `widgets_values_named.data`
  两个镜像**（二者必须逐字节一致）。
- **新增自定义节点需要重启 ComfyUI** 才会出现在 `/object_info`。
- 被杀掉的运行不会留下产出；应查 `/history` 的 `execution_error` 消息，而不是断定脚本失败。

## 文件

- `scripts/workflow-to-prompt.py` —— 工作流 JSON → API prompt、md 刷新、提交与轮询。
- `scripts/list-recent-outputs.py` —— 把最近的任务映射到其产出文件（temp 预览 vs 已保存）。
- `scripts/motion-profile.py` —— 每秒运动量曲线（高斯去噪后逐帧差分的 avg/中位/max，可裁剪 ROI），
  判断"被摄体到底动没动"的可靠口径。
- `scripts/motion-frame-profile.py` —— 某一时间窗的**逐帧**剖面（全幅 + 各 ROI + 静态控制区）：
  用来定位切点、挑出"两片都还没切"的窗口，并把跨 take 的比较换成 `ROI ÷ 控制区` 而不是裸值。
- `scripts/set-md-selected-id.py` / `scripts/show-md-cell.py` —— 对齐工作流的选中行、打印某一行的单元格。
- `references/workflow-to-prompt.md` —— 转换规则与完整陷阱清单。
- `references/mdtable-refresh.md` —— FallingTS mdtable 的状态结构、接口与刷新机制。
- `references/output-verification.md` —— 探测、抽帧拼板、运动与音频分析配方，含"为什么 `pblack`
  看不出被摄体运动"。
- `references/h3-scene-generation.md` —— **H3 场景视频的多轮实测结论**：各方案性能对比表、
  为什么单图锚点反超多图参考、五条提示词硬经验（正面陈述／固定机位／一镜一事／不描述参考图自身版式／
  物件名词不得有歧义 —— `notebook` 会被画成第二台笔记本）、
  旋转速率上限，以及改参数与抽帧的陷阱清单。
- `references/h3-shot-order-anchoring.md` —— **H3 镜头顺序与时长的多轮实测结论**：4 轮只改提示词
  全部把镜头挪错位置、为什么 Ref2VA 的参考图没有时间位置、硬锚点接线配方（帧号换算、同图双锚点定义区间），
  以及坑（`vae` 必需、否定式仍不可靠、一条无法满足的布局规则、帧号写死、快照不被 `--refresh-md` 回写）。
