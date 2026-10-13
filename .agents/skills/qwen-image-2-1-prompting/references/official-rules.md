# 官方规范原文摘录(带行号)

> 出处:`refs\Qwen-Image-2.1\prompt_rewrite\prompts\system_prompt_edit.txt`(205 行,18344 B)
> 与 `system_prompt_t2i.txt`(10045 B)。行号对应当前 checkout(`fb7ae1d`)。
> 引用官方原文时一律以本文件为准;**不要凭记忆转述**。

## 1. 总原则与两种失败模式(L28-35)

```
L28  Edit exactly the attribute(s) the user named, push each to a strong and
     unmistakable degree, and hold everything else at input fidelity.
L32  - Leakage — touching what the user did not name
L33  - Under-editing — an output a viewer could mistake for the unedited input,
     because the requested change was applied faintly.
L35  Preservation locks content, never edit strength. Recognizability is bought
     by naming what stays fixed, not by holding the effect back.
```

## 2. 保留描述的写法(L41、L43)—— 最容易被忽略的一条

```
L41  Say what stays, without repainting it. Name the untargeted content by type,
     position and role rather than describing its appearance, and prefer one
     blanket preservation clause over walking the frame. A preservation
     description reads to the model as a generation instruction: the more
     concretely you describe something you meant to keep, the more likely it
     drifts. Describe appearance concretely only for what you are actually
     changing, or when it is the only way to disambiguate between similar objects.
L43  Identity is the hardest invariant. ... When identity comes from a reference
     image, point at that image rather than describing features in words —
     verbal descriptions make the model regenerate and degrade the likeness.
```

**要点**:①一句笼统声明 > 逐帧走查 ②保留描述**会被当成生成指令** ③身份指向图,不用文字描述特征。

## 3. 多图标签(L59)—— mandatory & non-negotiable

```
L59  For Multi-Image Input (N >= 2), the rewritten instruction MUST use
     <image1>, <image2>, ... Do not use natural language references like "图1",
     "第一张图", "the first image", or "image A". This tagging format is
     mandatory and non-negotiable.
```

单图输入(N=1):**不要用标签**,自然引用("图像"/"图片中"/"the image")。

## 4. 输出格式与格式自检(L186-190)

```
L186 单段连续文本,禁 \n
L189 Write it out in full — no ellipsis, no truncation.
L190 State requirements affirmatively ("保持背景与输入图完全一致") rather than as
     prohibitions ("禁止改变背景"). Standard preservation phrasing
     "保持/保留[X]不变" is fine.
```

## 5. 其他关键条款

| 条款 | 原文要点 |
|---|---|
| **只做被要求的事** | `Do not add operations the user did not request, and do not clean up unmentioned defects, overlays or clutter however prominent they look.` |
| **写指令,不写成品描述** | `Lead with the operation, not a description of the finished picture, and write from the perspective of someone holding only the input image(s).` |
| **图内文字是字面的** | `Whenever readable text will appear in the output, commit to the exact characters — every element, quoted` ;`Text you cannot commit to should not be added at all.` |
| **语言决策** | 描述散文按**用户指令语言**;图内渲染文字按 ①用户指定 ②图内主导语言 ③指令语言。渲染文字必须**单语言**,不得混排 |
| **体裁不覆盖语言** | 规格书/分镜/技术参数外观靠**排版与字体**实现,**不靠**把标签换成英文 |
| **锚定图上内容** | `Every spatial, tonal and contextual claim comes from what is visibly there. If you are unsure a detail exists, leave it out.` |
| **消歧后下决断** | 把含糊意图/抽象质量词翻译成**具体可观察**的视觉属性;不留下未解决的备选与模糊程度词 |

## 6. 尺寸字段判定(wh_ratio / ratio_follow)

**互斥**:一个非空,另一个必须 `""`。

| 场景 | 值 |
|---|---|
| 正方/头像/专辑封面 | `1:1` |
| 横版/电脑壁纸/宽屏/视频封面/PPT | `16:9` |
| 竖版/手机壁纸/Stories/短视频封面 | `9:16` |
| 电影画面/cinematic/宽银幕 | `21:9` |
| 海报 | `2:3` |
| 证件照/小红书 | `3:4` |
| iPad/平板 | `4:3` |
| 全景图 | `2:1` |

### 6.1 官方精确像素表(原生 2K,README L210-216)

`wh_ratio` 取值对应的实际生成像素(以官方模型卡为准;上方语义映射表只决定"填哪个比值",像素由下表锁定):

| `wh_ratio` | 像素 (W×H) |
|---|---|
| `1:1`  | 2048 × 2048 |
| `4:3`  | 2400 × 1792 |
| `3:4`  | 1792 × 2400 |
| `3:2`  | 2528 × 1696 |
| `2:3`  | 1696 × 2528 |
| `16:9` | 2752 × 1536 |
| `9:16` | 1536 × 2752 |

> 官方**仅明确内置这 7 个标准比**。其余(21:9 / 2:1 / 5:3 等)为语义指引,实际像素未在模型卡枚举;
> 走 `ratio_follow` 跟底图,或自定义 `wh_ratio` 由管线按比例推导。

### 6.2 默认参数与步数(README Default Parameters)

- `num_inference_steps` 默认 **40**(原版 Qwen-Image-2.1)
- 默认分辨率 **2048 × 2048**(原生 2K 级)
- **多参考图上限:10 张**(N≥11 未声明支持)

### 6.3 Turbo 变体(README,2026-10-09 新增)

`Qwen-Image-2.1-Turbo` 同架构 7B,**8 步**生成/编辑,自带推荐采样 schedule(Diffusers 自动加载),默认 `CFG=1`。
⚠️ 单独设 `num_inference_steps` **不会**覆盖 Turbo 保存的 8 步 schedule;要用 Turbo 必须加载 `Qwen-Image-2.1-Turbo` 权重。

**编辑类默认跟随底图**:`ratio_follow = "<imageX>"`,`wh_ratio = ""`。
**扩图**:不跟随输入比例,按延伸方向推新比例。
**多宫格**:2×2 并排 `1:1`(**不要**过度拉成 3:1)。
**无画布场景生成**(合影/合照):`ratio_follow = ""`,按语义给 `wh_ratio`。

⚠️ **2K/4K/8K 是画质词,不是比例词** —— 不得据此推比例,输出一律按 2K 级处理。
⚠️ **禁止把分辨率/比例写进 `rewritten_prompt`**。

## 7. 校验器实际规则(源码级)

`refs\qwen-image-2.1-skill\skills\qwen-image-2-1-prompter\scripts\validate_prompt.py`

```python
FORBIDDEN_BOOSTERS = ['8k', '4k', 'masterpiece', 'award-winning',
                      'photorealistic masterpiece']
IMAGE_TAG_REGEX = ^<image\d+>$
```

`validate_qwen_prompt(payload) -> (bool, list[str])`,**签名是单个 dict**,不是关键字参数。检查项:

1. `rewritten_prompt` 必须存在且为 str
2. **不含 `\n` / `\r`**
3. 非空
4. **双引号配对**(数量必须为偶数)
5. 不含 `FORBIDDEN_BOOSTERS`(词边界匹配)
6. 必须含 `wh_ratio` 或(`wh_ratio` + `ratio_follow`)
7. 两者互斥;`ratio_follow` 必须匹配 `^<image\d+>$`;`wh_ratio` 必须匹配 `W:H`

⚠️ **这是浅层格式 lint**。实测本库 `0012_万物变化` 三行**全部 `pass=True`** ——
格式合规**不代表**语义有效。**"编辑没生效"不能靠它诊断。**

## 8. 官方示例原文(校准长度)

`refs\Qwen-Image-2.1\prompt_rewrite\data\edit_example.jsonl` 全文 4 条:

```json
{"id":"1412128","prompt":"Depict this symbol as a flag waving in the sky","task_type":"single_scene_complex"}
{"id":"1412215","prompt":"Translate into Hindi.","task_type":"text_edit"}
{"id":"1413730","prompt":"can u this image so that the head twist to the left while the body and arms not moved","task_type":"basic_edit"}
{"id":"1549226","prompt":"将<image1>中的人物和<image2>中的人物置入一个现代抖音直播间的场景中，生成一张两人并排坐在直播桌后共同面向镜头介绍产品的合影照片。保持两位人物的面部特征、发型和服装外观完全不变。","task_type":"multi_portrait"}
```

字符数:**46 / 21 / 85 / 96**。注意第 4 条虽短,但已含三要素:
①`<image1>`/`<image2>` 标签 ②明确操作 ③**一句**笼统保留声明。

## 9. 官方仓库结构(便于自查)

```
refs\Qwen-Image-2.1\
  prompt_rewrite\
    prompts\system_prompt_edit.txt   ← 编辑规范全文(本文件主要来源)
    prompts\system_prompt_t2i.txt    ← 文生图规范全文
    data\edit_example.jsonl          ← 官方编辑示例
    pe_core.py / run_transformers.py / run_vllm.py / serve.sh
  README.md                          ← 模型卡:circles/painted annotations/separate masks
```

官方提供本地跑改写器的脚本(`run_transformers.py` / `run_vllm.py` / `serve.sh`)。
官方 PE 改写器为**两个微调 checkpoint**(统一代码库,`--task t2i|edit` 自动判别):
- T2I:`Qwen/Qwen-Image-2.1-PE-T2I`
- Edit:`Qwen/Qwen-Image-2.1-PE-I2I`
- 基座写作 **Qwen3.5-VL 9B**(README L240)。

⚠️ 本文件旧版写作"Qwen3-VL 8B"并已说本机有 `models\text_encoders\qwen3vl_8b_bf16`——
那是本机现有可读权重,与官方当前 9B PE 不一致;要**完整复现官方 PE 改写**需另行获取 9B 权重,
8B 仅可沿用既有本地流程。
