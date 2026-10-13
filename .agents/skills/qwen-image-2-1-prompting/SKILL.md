---
name: qwen-image-2-1-prompting
description: Qwen-Image 2.1 (and Qwen-Image-Edit) image prompt engineering per Alibaba's official spec — the Attribute-Disentanglement principle (edit only the named attribute at full strength, hold everything else at input fidelity), the two symmetric failure modes Leakage and Under-editing, the <image1>/<image2> multi-image tagging mandate, single-continuous-paragraph output, yes/no on negative prompts and quality boosters, aspect-ratio-via-field not via words, identity-by-reference-not-description, and local-edit/mask reliability limits (issue #137) with the crop-and-stitch workaround. Use when writing, diagnosing, or fixing any Qwen-Image 2.1 / Qwen-Image-Edit prompt, when a local edit "did nothing" or drifted (removing veins, smoothing skin, changing an outfit, swapping a background), or when a resource-table prompt must be checked against the official spec.
---

# Qwen-Image 2.1 提示词工程（官方规范落地）

> 来源：**阿里官方** `prompt_rewrite/prompts/system_prompt_edit.txt` 与 `system_prompt_t2i.txt`,本地在
> `refs\Qwen-Image-2.1`(子模块);2.1 版 Skill 本地在 `refs\qwen-image-2.1-skill`(子模块)。
> 本技能是**官方规范的操作化**,不是教程转述。写/改 Qwen 2.1 提示词前必读。

## 与其他技能的关系(先看这一节,避免撞规范)

| 技能 | 管什么 | 本技能的关系 |
|---|---|---|
| `stories`（原 `stories-resource-tables`，2026-10-11 并入 `stories`） | 资源表 md 结构、`<br>` 分段、三段/五段段序、尺寸桶、`@{表/ID}` 引用 | **上游总纲**。本技能只管**送进模型的提示词文本本身**,不改表结构 |
| `qwen-image-2-1-prompting`(本技能) | Qwen 2.1 提示词的**写法与诊断** | 官方规范层 |

### ⚠️ 两套规范已知冲突点(必须知道,别盲目照一边)

| 冲突项 | `stories`（原 `stories-resource-tables`） | 官方 Qwen 2.1 规范 | 处置 |
|---|---|---|---|
| 分段 | 必须 `<br>` 分 5 段(否则 md 表被换行断开) | **单段连续文本,禁任何换行** | **表内用 `<br>` 保表结构,送模型前把 `<br>` 合成单段** —— 见 `references/local-edit.md` |
| 图号 | `图1`/`图2`/`图3` | **必须 `<image1>`/`<image2>`**,自然语言引用被明文禁止 | 改表内文本为 `<imageN>`;实测槽位一一对应,无需改线 |
| 负词 | 允许多条负词清单 | 负词极少用;官方示例几乎不用 | 砍到只留本次真正要压的 |
| 比例 | 表内有宽/高列 | **禁止把分辨率/比例写进提示词**,走 `wh_ratio`/`ratio_follow` 字段 | 比例只填表列,不写进正词 |
| 风格段 | 必须有 `写实三维CG风格` 段头 | 质量标签属禁用的 booster,要写**可观察视觉属性** | 保留风格段(库内规范),但**不堆 `4k`/`8k`/`masterpiece` 类词** |

**一句话**:`<br>` 是为了 md 表能存活、`<imageN>` 是为了模型能听懂 —— 两者不矛盾,`<br>` 在**送出前**消化掉即可。

## 核心原则:属性解耦,全力编辑(Attribute Disentanglement at Full Strength)

> **只改用户点名的那一个属性,把它推到强而明确的程度;其余一切保持在输入保真度上。**

两种**对称**的失败模式:

- **Leakage(泄漏)** —— 动了用户没点名的地方(锐化顺手改了色调、换装掉了配饰、改背景"好心"清理了没提到的东西)
- **Under-editing(编辑不足)** —— **输出看起来像没编辑过的原图**,因为改动被施加得太轻

> **Preservation locks content, never edit strength.**(保留条款锁的是**内容**,永远不是**编辑强度**)
> Recognizability is bought by naming what stays fixed, not by holding the effect back.
> (可辨识性靠**点名什么不变**换来,而不是靠把效果压小换来)

⚠️ **这是最容易搞反的一条**:很多人为了"保住原图"而把改动写弱 —— 官方说这**正好错了**。
写保守了 → 得到一张没变的图;要保原图,靠**一句笼统的保留声明**,不靠削弱改动。

## 十条硬规则(速查)

1. **多图必须用 `<image1>`/`<image2>`/…** 严禁 `图1`、`第一张图`、`the first image`、`image A`。原文:**mandatory and non-negotiable**。单图输入则**禁止**用标签,自然引用即可
2. **输出单段,禁 `\n`**
3. **禁把分辨率/比例写进提示词** —— 走 `wh_ratio`(值)/`ratio_follow`(`<imageX>`),**两者互斥**,一个非空另一个必须为 `""`
4. **2K/4K/8K 是画质词不是比例词**;输出一律按 2K 级处理
5. **要正面表述,不要禁止** —— 写 `保持背景与输入图完全一致`,不写 `禁止改变背景`。标准保留措辞 `保持/保留[X]不变` 是认可的
6. **保留描述要抽象,不要具体重绘** —— 原文:*the more concretely you describe something you meant to keep, the more likely it drifts*(越具体描述想保留的东西,它越容易漂)。按**类型/位置/角色**点名,不要描绘外观
7. **一句笼统保留声明 > 逐帧走查**(`prefer one blanket preservation clause over walking the frame`)
8. **身份是最硬的不可变量**;身份来自参考图时**指向那张图**,不要用文字描述特征 —— 原文:*verbal descriptions make the model regenerate and degrade the likeness*
9. **只做被要求的事**,不要清理没提到的缺陷/杂物,不管它多显眼
10. **图内文字是字面的** —— 要出现可读文字就必须逐字用双引号确定,否则不要加;按图内主导语言,不得混语言

**质量助推词黑名单**(官方校验器内置,命中即错):
`8k`、`4k`、`masterpiece`、`award-winning`、`photorealistic masterpiece`
—— 理由:**要写可观察的视觉属性,而不是打质量标签**。

## 官方示例有多短(校准你的长度直觉)

官方 `edit_example.jsonl` 四条"合格编辑指令":

| 任务 | 提示词全文 | 字符 |
|---|---|---|
| `single_scene_complex` | `Depict this symbol as a flag waving in the sky` | 46 |
| `text_edit` | `Translate into Hindi.` | 21 |
| `basic_edit` | `can u this image so that the head twist to the left while the body and arms not moved` | 85 |
| `multi_portrait` | `将<image1>中的人物和<image2>中的人物置入一个现代抖音直播间的场景中，生成一张两人并排坐在直播桌后共同面向镜头介绍产品的合影照片。保持两位人物的面部特征、发型和服装外观完全不变。` | 96 |

⇒ **21~96 字符**是官方认定的合格长度。**几百字的五段式提示词远超出官方示例一个量级**,
堆得越长,保留条款越压过编辑强度(见 Under-editing)。

## 诊断流程:编辑"没生效"时按顺序查

手里有一张"看起来几乎没变"的输出时,**按这个顺序**排查,别一上来就加词:

1. **是不是 Under-editing?**(最常见)—— 看提示词里"要保留的东西"的篇幅是否**超过**了"要改的东西";
   是否用了弱化词(`轻微`/`略微`/`稍稍`/`尽量`/`弱化到不易察觉`)
   → 治法:**改动写到强而明确 + 保留压成一句**
2. **是不是把要保留的东西**具体重绘**了?** —— 是否在逐项枚举五官/发型/服装/构图
   → 治法:**删掉枚举,改成 `保持<image1>的人物身份、画面内容与构图完全不变`**
3. **图号引用对不对?** —— 多图是否用了 `图1` 而非 `<imageN>`;接图顺序对不对
4. **底图与遮罩同源吗?** —— 遮罩必须涂在**该条的底图**上;底图换了而遮罩没换 = 遮罩位置全错
5. **是不是要求模型尊重遮罩边界?** —— 见下节,这条路**本就不可靠**
6. **正负词是否拉锯?** —— 正词要"保留毛孔绒毛"、负词要"抹平皮肤纹理" ⇒ 净效果两者都弱
7. **是否要求模型"做减法"?** —— 去血管/去瑕疵/抹平这类**减少细节**的编辑天生难,模型先验偏向加细节

### ⚠️ 遮罩不能保证"只改遮罩内"(官方未解决)

官方 README 明确 2.1 **支持**用 circles / painted annotations / **separate masks** 做局部编辑
⇒ **遮罩是官方支持的控制通道,不是失败原因**。

但官方仓库 issue #137(*"inpaint cannot be conditioned to fit inside a masked area"*)
**至今 open、0 回复**:生成内容经常不贴遮罩,模型想画的对象比遮罩大 → 在遮罩边缘被裁切,
破坏"外部必须完全不变"的精确编辑。**靠提示词写 `Do not alter any pixel outside the mask` 无效**(已有实测)。

⇒ 对"只改手/脸,别的都不许动"这类严苛要求,**不要指望单次全图编辑+遮罩**。
用 `ComfyUI-Inpaint-CropAndStitch`(本机已装):**按遮罩裁出 → 局部重绘 → 贴回**。

## 本地工作流接线事实(实测,2026-09-24)

`00120_万物变化_QI2.1` 的 mdtable 节点(节点 10)8 个输出槽**全部连线**,与表列**严格一一对应**:

| 表列 | 槽 | 模型端 |
|---|---|---|
| `原图` | 1 | 底图 |
| `灰度遮罩` | 2 | MASK |
| `图1` | 3 | **`<image1>`** |
| `图2` | 4 | `<image2>` |
| `图3` | 5 | `<image3>` |
| `变化-正词` | 6 | `prompt` |
| `变化-负词` | 7 | `negative_prompt` |

由 `TextEncodeQwenImage21` 单节点同时产出 positive/negative 与 latent(带参考图编码)。
⇒ **表里写 `<image1>` 就等于模型端 `<image1>`,是纯文本改动,无需重接工作流。**

## 官方模型卡新增事实(2026-10-09,提示词/接线相关)

> 来源:`refs/Qwen-Image-2.1/README.md`(当前 HEAD `1993c3a`)。下列为模型能力,非"提示词格式错误",
> 但直接影响怎么写提示词、怎么接工作流。权威数值见 `references/official-rules.md` §6.1–6.3。

### ① 原生透明图(RGBA)—— 官方指定前缀
模型原生支持透明背景生成;**必须用这个开头格式**:
> `This is an RGBA image with transparency. <你的描述>. The image has alpha channel and the background is transparent.`
例:`This is an RGBA image with transparency. A cute cartoon dragon sticker. The image has alpha channel and the background is transparent.`
⇒ 这**不是**可选美化,是官方要求的提示词前缀;做贴纸/图标/合成遮罩前序图时要用。

### ② 精确比例像素表(原生 2K)
`wh_ratio` → 实际像素:`1:1`=2048×2048、`4:3`=2400×1792、`3:4`=1792×2400、`3:2`=2528×1696、`2:3`=1696×2528、`16:9`=2752×1536、`9:16`=1536×2752。官方仅内置这 7 个标准比。

### ③ 默认参数
`num_inference_steps=40`,默认 `2048×2048`。**多参考图上限 10 张**。

### ④ Turbo 变体(8 步)
`Qwen-Image-2.1-Turbo` 同架构,**8 步**、默认 `CFG=1`,自带采样 schedule;单设 `num_inference_steps` 不覆盖其 schedule,需加载 Turbo 权重才生效。本机 QI2.1 工作流若要走快出,需另接 Turbo 权重(当前工作流未用)。

## 校验器(浅层 lint,别当语义判据)

```python
import importlib.util
spec = importlib.util.spec_from_file_location(
    "vp", "refs/qwen-image-2.1-skill/skills/qwen-image-2-1-prompter/scripts/validate_prompt.py")
vp = importlib.util.module_from_spec(spec); spec.loader.exec_module(vp)
ok, errors = vp.validate_qwen_prompt(
    {"rewritten_prompt": p, "wh_ratio": "", "ratio_follow": "<image1>"})
```

⚠️ **只查格式**(换行/引号平衡/禁用词/尺寸字段互斥),**不判语义有效性**。
实测本库三行**全部 `pass=True`** —— 说明"编辑没生效"**不是格式问题**,别拿它兜底。

## 参考文件

- **[references/official-rules.md](references/official-rules.md)** —— 官方规范原文摘录(带 `system_prompt_edit.txt` 行号)+ 完整校验规则 + 尺寸字段判定
- **[references/local-edit.md](references/local-edit.md)** —— 局部编辑/遮罩专题:血管类"做减法"编辑的完整改法、crop-and-stitch 流程、本库踩坑实录

## 写提示词前自检清单

- [ ] 多图用了 `<image1>`/`<image2>`;单图没用标签
- [ ] 单段连续文本(送模型前 `<br>` 已合成)
- [ ] 提示词里**没有**分辨率/比例字样
- [ ] 没有 `8k`/`4k`/`masterpiece`/`award-winning`/`photorealistic masterpiece`
- [ ] 要求都是**肯定式**,没有 `禁止…`/`不要…`
- [ ] 保留部分是**一句笼统声明**,没有逐项列举外观
- [ ] 保留部分篇幅**没有超过**改动部分
- [ ] 点名要改的属性推到了**强而明确**的程度(没有 `轻微`/`尽量`/`略微`)
- [ ] 负词是**短清单**,且与正词不拉锯
- [ ] 身份来自参考图时是**指向图**,不是文字描述特征
- [ ] 要求"做减法"的编辑(去血管/去瑕疵)已考虑走 crop-and-stitch 而非全图+遮罩
