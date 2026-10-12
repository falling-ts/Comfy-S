# Qwen-Image 2.1 提示词规范调研 —— 以及「抹平手部血管凸起」为什么失败

> 调研日期 2026-09-24。全部结论来自**官方源码/官方规范原文**与**本库实测数据**,不采信二手教程。
> 本地已拉取的权威源见文末「本地已拉取的权威源」。

## 0. 一句话结论

**失败不是「提示词写得不够狠」,而是规范用反了。** 官方 Qwen-Image-2.1 编辑提示词规范的核心原则是
**「只改被点名的那一个属性,把它推到极强;其余一切靠一句笼统的保留声明兜住」**,而本库 `0012_万物变化`
的写法恰好踩了官方明确点名的三个坑:**逐帧描写要保留的东西**(反而诱导模型重画)、**用否定式下指令**、
**在手部条目里堆了 40 条负词**把编辑强度整体压平。叠加 **2.1 的遮罩并不保证严格贴边界**(官方 issue #137 未解决),
「抹平血管」这种**要求把细节变少**的编辑,在本库当前写法下几乎必然退化成「几乎没变」。

---

## 1. 官方权威源(本次实际拉取,均已入库为子模块)

| 源 | 内容 | 价值 |
|---|---|---|
| [QwenLM/Qwen-Image-2.1](https://github.com/QwenLM/Qwen-Image-2.1) | **官方仓库**。含 `prompt_rewrite/prompts/system_prompt_edit.txt`(18.3 KB)与 `system_prompt_t2i.txt`(10.0 KB)—— **阿里官方的提示词改写系统提示词全文**;另有 `pe_core.py`、`run_vllm.py`、`edit_example.jsonl` | ★★★ 唯一的**规范原文**,不是教程转述 |
| [iamyoki/qwen-image-2.1-skill](https://github.com/iamyoki/qwen-image-2.1-skill) | 专为 2.1 写的 **Agent Skill**:`SKILL.md` + `references/{edit_rules,t2i_rules,cheat_sheet}.md` + `scripts/validate_prompt.py` | ★★ 与上者同源但**已工程化**,可直接当校验器 |
| [QwenLM/Qwen-Image issue #137](https://github.com/QwenLM/Qwen-Image/issues/137) | 「**inpaint cannot be conditioned to fit inside a masked area**」 | ★★★ 官方仓库里**至今 open、0 回复**的 inpainting 缺陷报告 |

已注册为 git 子模块:`refs/Qwen-Image-2.1`、`refs/qwen-image-2.1-skill`(见根 `.gitmodules`)。

### 1.1 官方编辑示例有多短(关键对照)

`prompt_rewrite/data/edit_example.jsonl` 全文只有 4 条,**这是官方认定的「合格编辑指令」**:

| task_type | 提示词全文 | 字符数 |
|---|---|---|
| `single_scene_complex` | `Depict this symbol as a flag waving in the sky` | **46** |
| `text_edit` | `Translate into Hindi.` | **21** |
| `basic_edit` | `can u this image so that the head twist to the left while the body and arms not moved` | **85** |
| `multi_portrait` | `将<image1>中的人物和<image2>中的人物置入一个现代抖音直播间的场景中…保持两位人物的面部特征、发型和服装外观完全不变。` | **96** |

本库 `0012` 的对照实测:

| 行 | 变化-正词 | 变化-负词 |
|---|---|---|
| `00001_陈落出门装` | 312 字符 / 5 段 | 97 字符 |
| `00002_陈落手部修改全景` | **385 字符 / 5 段** | **227 字符 / 40 条** |
| `00003_陈落手部修改特写` | **373 字符 / 5 段** | **227 字符 / 40 条** |

→ 正词比官方最长示例**长约 4 倍**;负词 40 条更是官方示例里根本不存在的东西。

---

## 2. 官方规范原文(逐条摘录,`system_prompt_edit.txt`)

### 2.1 总原则 —— 属性解耦

> **Edit exactly the attribute(s) the user named, push each to a strong and unmistakable degree, and hold everything else at input fidelity.**
> (L28)

两种对称的失败模式(L31-33):

- **Leakage** —— 动了用户没点名的地方;
- **Under-editing** —— **输出看起来像没编辑过的原图,因为改动被施加得太轻**。

> **Preservation locks content, never edit strength.** Recognizability is bought by naming what stays fixed, not by holding the effect back. (L35)

### 2.2 ⚠️ 最致命的一条:不要具体描写你要保留的东西

> **Say what stays, without repainting it.** Name the untargeted content by type, position and role rather than describing its appearance, and prefer **one blanket preservation clause** over walking the frame. **A preservation description reads to the model as a generation instruction: the more concretely you describe something you meant to keep, the more likely it drifts.** (L41)

本库 `0012` 新增两行的**保身份段**正是「walking the frame」的反面教材:

> `保持图1原有的英俊面部、清爽黑发、身材比例、正面站姿与服装完全一致，五官、发型、身高与衣物不得改变，手部改后与全身风格完全统一`

官方要求「一句笼统保留声明」,本库写了**逐项枚举**。按 L41,这些字**会被模型当成生成指令**,于是模型把算力花在重新生成脸/头发/衣服上,「手部细腻化」这件真正想做的事被稀释。

### 2.3 ⚠️ 必须用肯定式,不能用否定式

> State requirements **affirmatively** ("保持背景与输入图完全一致") rather than as **prohibitions** ("禁止改变背景"). (L190)

本库新增两行的正词里否定句密集:

- `不引入任何环境、地面、阴影与场景元素`
- `不得改变`
- `弱化到不易察觉`(≈否定式的程度副词)

负词 40 条(`血管暴起, 青筋凸起, …`)整体是**否定式堆叠**。规范要求把「不要 X」改写成「要 Y」。

### 2.4 身份来自参考图时,要用图号指,不要用文字描述

> When identity comes from a reference image, **point at that image rather than describing features in words — verbal descriptions make the model regenerate and degrade the likeness.** (L43)

### 2.5 多图输入必须用 `<image1>`/`<image2>`,严禁「图1」

> For Multi-Image Input (N >= 2), the rewritten instruction **MUST** use `<image1>`, `<image2>`, ... **Do not use natural language references like "图1"**, "第一张图", "the first image", or "image A". This tagging format is **mandatory and non-negotiable**. (L59)

实测:**本库三行的正词全部使用「图1」**,零处 `<image1>`。

### 2.6 输出必须是**单段无换行**

> The entire rewritten prompt must be a **single continuous paragraph with NO line breaks**. (L186)

本库用 `<br>` 分 5 段 —— 这与官方的「单段」要求**直接冲突**。注意:这一条与 `stories-resource-tables`
技能的 `<br>` 分段规范冲突,**属于两套规范的正面撞车**,见 §4 的建议处置。

### 2.7 禁止「质量助推词」

官方 skill 的 `validate_prompt.py` 内置 `FORBIDDEN_BOOSTERS = ['8k','4k','masterpiece','award-winning','photorealistic masterpiece']`,命中即报错,理由原文:**Describe observable visual elements instead.**(要写可观察的视觉属性,而不是打质量标签)

本库新增两行含 `超写实角色资产质感，次世代三维渲染，立体体积感与真实材质表现` —— 同属「质量标签」而非可观察属性。

---

## 3. 为什么「抹平血管凸起」特别难 —— 三重叠加

### 3.1 编辑方向与模型先验相反

「血管暴起」在真实摄影/写实渲染里是**细节**,而 2.1 是**以增加细节为默认倾向**的生成模型。要求「抹平血管、弱化肌腱轮廓、恢复皮下脂肪饱满」=
**要求模型做减法并保持解剖可信**。这正是 §2.1 所说的 under-editing 高发区:模型倾向保守,给你一张「看起来几乎没变」的图。

**本库写法加剧了它**:40 条负词里有 13 条是手部解剖类(`血管暴起, 青筋凸起, …, 指甲畸形`),负词整体在**压细节**,
而正词又要求「保留清晰可辨的真实毛孔、细微绒毛与次表面散射通透感」——**正负词互相拉锯**,净效果是两者都弱。

### 3.2 `整体是…` 段把「手部」重新说成了「整个人」

新增两行第 4 段:

> `整体是年轻帅气的小说作者出门时的模样，双手干净细腻，符合日常健康手部的自然外观`

这段**沿用了 `00001` 换衣条的句式**,但 `00001` 改的是**全身服装**,说「整体是出门模样」合理;
`00002/00003` 只改**手**,再写「整体是…出门时的模样」会把语义重心从局部拉回**全身重新生成**。
更严重的是它提到「小说作者出门时的模样」,而该条底图是**雨夜书房坐姿**——**描述与底图不符**,等于给模型一个矛盾的生成指令。
(该矛盾源于本轮早期我的错误:先按建模图语境写,改引用后**未清理第 4 段**。)

### 3.3 2.1 的遮罩不保证严格贴边界(官方未解决)

官方 README 明确 2.1 支持 **"specify local edits via circles, painted annotations, or separate masks"** ——
遮罩是**官方支持的控制通道**,不是问题所在。但官方仓库 issue #137 记录:

> generated content frequently does not fit inside the provided mask… the result gets clipped at the mask edge.

该 issue **至今 open、0 回复**。含义:遮罩能**引导**局部,但**不能保证**「遮罩外逐像素不变」。
所以对「只改手、别的全不许动」这种严苛要求,**必须**配合 `ComfyUI-Inpaint-CropAndStitch` 式的
「裁出遮罩区域 → 单独重绘 → 贴回」流程,而不能指望单次全图编辑 + 遮罩。

---

## 4. 处置建议(按性价比排序)

### P0 —— 立刻可做,不改工作流

1. **删掉 `00002/00003` 的 `整体是…` 段**(或改写为只讲手部的一句话)。它既与底图矛盾,又把局部编辑拉成全身编辑。
2. **保身份段从「逐项枚举」压成一句笼统保留**:官方 L41 + L43 要求「point at that image」。
   例:`保持<image1>的人物身份、画面内容与构图完全不变` —— 不再逐个数五官/头发/衣服。
3. **负词从 40 条砍到 ~10 条以内**,只保留**本次真正要压的**那几项(`血管暴起, 青筋凸起, 手部浮肿, 手指粗短`),
   去掉所有「质量标签」与手部无关项。官方示例里负词几乎不用。
4. **否定式改正肯定式**:`不引入任何环境` → `画面内容与<image1>完全一致`;`不得改变` → `保持…不变`(后者官方认可)。

### P1 —— 需要改规范/工作流

5. **多图引用改用 `<image1>`**:官方 L59 是 mandatory & non-negotiable。
   ✅ **已实测确认可直接改**:`00120_万物变化_QI2.1` 节点 10(mdtable)的 8 个输出槽全部连线,
   槽位与 `0012` 表列**严格一一对应**——`图1`=槽3→`images.image_1`、`图2`=槽4→`images.image_2`、
   `图3`=槽5→`images.image_3`、`变化-正词`=槽6→`prompt`、`变化-负词`=槽7→`negative_prompt`。
   故**表里的「图1」在模型端就是 `<image1>`**,改写成 `<image1>` 是**纯文本改动,无需重接工作流**。
6. **`<br>` 分段 vs 官方「单段无换行」的冲突要拍板**:
   - `stories-resource-tables` 要求 `<br>` 分段(为了 md 单元格不断表);
   - 官方要求单段无换行。
   - **建议**:保留 `<br>` 作为**表结构**的分段手段(否则 md 表破),
     但在**送进模型的最后一步**把 `<br>` 换成 `。` 或空格合成单段 —— 即「表里分段、送模型前合并」。
     这需要改 `00120_万物变化_QI2.1` 工作流或 mdtable 节点。
7. **手部此类「局部精修」不要走全图编辑**:接 `ComfyUI-Inpaint-CropAndStitch`,按遮罩裁切 → 局部重绘 → 贴回,
   绕开 issue #137 的边界不保证问题。本机已装该插件。

### P2 —— 可选

8. 把官方 `system_prompt_edit.txt` / `system_prompt_t2i.txt` 接进本库的提示词生成流程
   (官方给了 `run_transformers.py` / `run_vllm.py` / `serve.sh`,可用 Qwen3-VL 8B 本地跑,本机已有该权重)。

---

## 5. 本地已拉取的权威源(子模块)

| 路径 | 远程 | 用途 |
|---|---|---|
| `refs/Qwen-Image-2.1` | https://github.com/QwenLM/Qwen-Image-2.1.git | 官方仓库 + 规范原文 |
| `refs/qwen-image-2.1-skill` | https://github.com/iamyoki/qwen-image-2.1-skill.git | 2.1 提示词 Skill(含校验器) |

**校验器用法**(实测可用,注意签名是**单个 payload dict**):

```python
spec = importlib.util.spec_from_file_location(
    "vp", r"D:\AI\Comfy-S\refs\qwen-image-2.1-skill\skills\qwen-image-2-1-prompter\scripts\validate_prompt.py")
vp = importlib.util.module_from_spec(spec); spec.loader.exec_module(vp)
ok, errors = vp.validate_qwen_prompt(
    {"rewritten_prompt": p, "wh_ratio": "", "ratio_follow": "<image1>"})
```

⚠️ **本校验器是浅层格式 lint**(查换行/引号平衡/禁用词/尺寸字段互斥),**不判语义有效性**。
实测本库三行**全部 `pass=True`** —— 说明失败**不是格式问题**,不能靠它兜底。

## 6. 本次未采信的源

- 二手教程(`qwe.edu.pl`、`apidog.com`、`cnblogs` 等)仅作线索,结论一律回到官方原文核对。
- 未找到**官方**针对「去除血管/皮肤瑕疵」的专门 prompt 配方;官方规范是**通用编辑方法论**,不提供分场景配方。
