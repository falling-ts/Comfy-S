# Qwen-Image-Edit 三参考图提示词规范与可用 Skills 调研(2026-08-11)

> 调研日期:2026-08-11。数据来源:本地源码(`ComfyUI\comfy_extras\nodes_qwen.py`、`comfy\text_encoders\qwen_image.py`)、本地工作流(`workflows\万物建模.json`、`webs\RunningHub\workflows\`)、官方文档(QwenLM/Qwen-Image 仓库、HF 模型卡)、GitHub 搜索。

## 一、核心提示词节点:三参考图的机制(源码层面)

Qwen-Image-Edit 的核心条件编码节点有两个,均在 `ComfyUI\comfy_extras\nodes_qwen.py`:

| 节点 | 图像输入 | 用途 |
|------|---------|------|
| `TextEncodeQwenImageEdit` | `image`(单图) | 原生单图编辑 |
| **`TextEncodeQwenImageEditPlus`** | **`image1` / `image2` / `image3`**(三参考图) | 多图参考编辑(核心节点) |

### 节点自动拼接的格式(源码事实)

`TextEncodeQwenImageEditPlus.execute()`(`nodes_qwen.py:73-106`)对每张接入的图生成前缀文本,再拼到用户提示词**前面**:

```
Picture 1: <|vision_start|><|image_pad|><|vision_end|>
Picture 2: <|vision_start|><|image_pad|><|vision_end|>
Picture 3: <|vision_start|><|image_pad|><|vision_end|>
<你的提示词>
```

即 `image_prompt + prompt`,随后套官方 chat 模板:

```
<|im_start|>system
Describe the key features of the input image (color, shape, size, texture, objects, background), then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input where appropriate.<|im_end|>
<|im_start|>user
{image_prompt + prompt}<|im_end|>
<|im_start|>assistant
```

### 图像 token 与 reference_latents(两条参考通道)

- **VL 视觉理解通道**:每张参考图先缩到约 **384×384**,`<|image_pad|>`(token 151655)按**出现顺序**替换为对应图片的视觉嵌入(`qwen_image.py:45-48`)。
- **VAE 参考潜在通道**:接了 `vae` 后,每张图再缩到约 **1024×1024** 面积(边长取 8 的倍数),VAE 编码成参考 latent,**按顺序**写入 conditioning 的 `reference_latents` 列表(`nodes_qwen.py:104-105` → `model_base.py:1043-1048`),采样器把全部参考图当"硬参考"用。

> ⚠️ 两条通道的图片顺序一致,`reference_latents` 列表第 N 项对应提示词里的第 N 张图。

## 二、提示词中如何引用三张参考图(规范)

| 方式 | 写法 | 说明 |
|------|------|------|
| **正规标签(推荐)** | `Picture 1` / `Picture 2` / `Picture 3` | 节点自动前缀、与官方训练对齐的标签 |
| **中文社区通行** | `图1` / `图2` / `图3`(或 `图片N`、`第N张图`) | VL 模型按顺序对应到图,大量实际工作流使用 |
| **空间位置** | "左侧那张"、"背景那张" | 模型看到真实图像内容,位置描述也能生效 |
| ❌ 不要手动输入 | `<\|vision_start\|><\|image_pad\|><\|vision_end\|>` | 节点自动加,手写会破坏模板 |

**官方能力边界**:Qwen-Image-Edit-**2509** 起支持多图编辑(经图像拼接训练),支持 "person+person / person+product / person+scene" 等组合,**最优 1-3 张输入**(官方 `Qwen-Image-Edit-2509.md`;阿里云百炼文档同样标注"数量 1-3 张")。

### 完整示例(三图,来自 RunningHub 工作流)

`webs\RunningHub\workflows\图片处理\Qwen+Image+Edit+2511-支持单图多图编辑.json`:

```
<|im_start|>system
Describe the key features of the input image (color, shape, size, texture, objects, background), then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input where appropriate.<|im_end|>
<|im_start|>user
Picture 1: <|vision_start|><|image_pad|><|vision_end|>Picture 2: <|vision_start|><|image_pad|><|vision_end|>Picture 3: <|vision_start|><|image_pad|><|vision_end|>让图1的女人的衣服替换为图2款式的汉服,保持角色姿态角度不变,把背景替换成图3的背景<|im_end|>
<|im_start|>assistant
```

其他真实用例(均按编号引用):
- "请将**图1**的女生和**图2**的狐狸和兔子三人融合成一张三人俯拍自拍照…"(`Qwen+2511+图生图一致性之王!.json`)
- "把**图1**的人物融入**图2**白色区域内,并补全场景和光影…"(`Qwen+一键换脸、换头.json`)
- "将**图1**中的角色移至**图2**中,并调整为与**图2**角色相似的姿势…"(`图片换人+换背景V2=QwenEdit.json`)
- "**图1**角色参考**图2**中的姿势,持剑前冲战斗姿态,保持图1中角色和场景的一致性"(`姿势迁移—FireRed-Image-Edit-1.1.json`)
- "参考**图1**字体的风格和颜色,换成文字异世相遇"(`字体效果模仿-风格迁移.json`)
- "移除**图片1**中的红颜色"(`万能图片去水印加高清.json`)

### 常用三图编辑提示词示例(可直接抄用)

> 一句话规则:**提示词里用 `图1` / `图2` / `图3`(或 Picture 1/2/3)指代三张图,说明要对哪张图做什么**即可。无需手写 `<|vision_start|>` 标签(节点自动加),三图顺序对应 图1/图2/图3。

1. **换装**(图1人 + 图2衣服款式 + 图3背景):
   ```
   让图1的女人的衣服替换为图2款式的汉服,保持角色姿态角度不变,把背景替换成图3的背景
   ```
2. **多人物融合**(图1 + 图2 合成一张):
   ```
   请将图1的女生和图2的狐狸兔子融合成一张三人合影,保持图1人脸相似度,光线明亮均匀
   ```
3. **人物 + 姿势参考**(图1角色 + 图2姿势):
   ```
   图1角色参考图2中的姿势,持剑前冲战斗姿态,保持图1中角色和场景的一致性
   ```
4. **人物放入场景**(图1人物 + 图2场景):
   ```
   把图1的人物融入图2中,调整姿势与光线,使人物自然融入,无明显合成痕迹
   ```
5. **风格 / 文字迁移**(图1风格 + 换文字):
   ```
   参考图1字体的风格和颜色,换成文字"异世相遇"
   ```

要点:
- 指令**只说"改什么"**,别长篇大论;文字编辑把目标文字用引号括起。
- 若以某张图为底、其余做参考:把目标图接在 **image1**,参考图接 image2/image3。
- 接错图片顺序等于指错图。

## 三、GJJ 自研节点:标签不同,需注意

`custom_nodes\ComfyUI_GJJ_Nodes\nodes\gjj_qwen_image_edit_plus.py` 的 **`GJJ_TextEncodeQwenImageEditPlus`** 与原生节点有两点关键差异:

1. **标签格式为 `imageN` 而非 `Picture N`**:自动前缀 `image{index}: <|vision_start|><|image_pad|><|vision_end|>`,即 `image1:` / `image2:` / `image3:`(452、476 行)。且 `_rewrite_qwen_image_references()`(397-411 行)会把提示词里的 `Picture N` / `image N` / `图N` / `第N张图` **自动重写为 `imageN`**。
2. **主画布自动切换**:提示词写到"图2的背景 / background of image 2"时,节点静默把第 2 张图作为出图主画布(`_detect_background_image_index`)。多图 + VAE 时按 FireRed 平等参考方式把前 3 图全部写入 `reference_latents`。

> 若在图内混用原生节点与 GJJ 节点,提示词引用需各自遵循对应标签。

## 四、社区节点实现(与原生一致,均用 "Picture N")

| 仓库 | ★ | 参考图数 | 说明 |
|------|---|---------|------|
| `lrzjason/Comfyui-QwenEditUtils` | 836 | 5 | RunningHub 大量三图工作流实际实现;已演进为 `ComfyUI-EditUtils` |
| `princepainter/ComfyUI-PainterQwenImageEdit` | 77 | 10 | 多图 + mask,`Picture N` 前缀 |
| `PixWizardry/ComfyUI_PixQwenImageEditEnhanced` | 4 | 5 | 增强 VLM 条件节点 |
| `lihaoyun6/ComfyUI-QwenPromptRewriter` | 76 | — | 用 Qwen LLM 把提示词改写为对齐 Qwen-Image/Edit 在线版风格(提示词重写工具,非 SKILL) |

## 五、GitHub 可用 Skills 调研

> 结论:截至 2026-08-11,**没有**专门针对"ComfyUI TextEncodeQwenImageEditPlus 三参考图提示词格式"的现成 agent skill。以下为最相关的 skill / 知识源。

| 仓库 | ★ | 类型 | 与 qwen-image-edit 的关系 |
|------|---|------|--------------------------|
| `SlavaSexton/ComfyUI-Agent-Kit` | 69 | agent skill + MCP,驱动本地 ComfyUI | ✅ 最对口:`MODELS/image-open.md` 明确 Qwen-Image-Edit 提示词规范(surgical 指令、"Image 1" 编号引用、上限 3、负提示词不支持用单空格) |
| `StanleyChanH/aliyun-image-skill` | 5 | agent SKILL,阿里云百炼 API | ✅ 覆盖 Qwen-Image-Edit(单图编辑 + 多图融合 + 图像翻译),`references/image-edit.md` 含输入 1-3 张、参数、分辨率;需 `DASHSCOPE_API_KEY` |
| `bearstonem/comfyui-qwen-imagegen` | 0 | ComfyUI SKILL | ⚠️ 仅 Qwen Image 2.5 **文生图**,非编辑 |
| `runapi-ai/qwen-image` | 0 | RunAPI SKILL | ⚠️ 通用 agent 生图(API) |
| `catherineliaooo/qwen-image-gen` 等 | 1-2 | 阿里云百炼 API skill | ⚠️ 文生图,含提示词手册 |

### 已拉取到本项目的 skill 源码与安装状态

见 `refs\Qwen-Image-Edit-Skills\`(2026-09-30 由 `docs\` 迁入 `refs\`):
- `aliyun-image-skill\` — 阿里云 API 版 Qwen-Image-Edit skill 全量源码(纯存档,未安装)
- `comfyui-agent-kit\` — ComfyUI-Agent-Kit 的 comfyui skill 知识文件(56 文件:SKILL.md、MODELS 提示词规范、NODE_LIBRARY、comfy_client.py 等)

**安装状态(2026-08-11)**:**`comfyui` skill 已安装到项目 `.agents\skills\comfyui\`**(知识独立安装,未装 npm MCP 驱动层;`machine.md` 已按本机真实环境填好,见其"Known local quirks")。后续更新可从 `refs\Qwen-Image-Edit-Skills\comfyui-agent-kit\` 重新复制。

## 六、建议

- **提示词写作**:统一用 **"图N" 编号引用**(中文工作流通行)或 **"Picture N"**(正规),指令只描述改动(surgical instruction),文字编辑把目标文字用引号括起。
- **负提示词**:原生 Qwen-Image-Edit 负提示词支持有限,留空或单空格即可(Agent-Kit 规范)。
- **skill 安装**:若需让 WorkBuddy 具备写 qwen-image-edit 提示词能力,推荐基于本调研自建一个适配本地 ComfyUI 的 `qwen-image-edit-prompt-writing` skill(结构参考 `h3-prompt-writing`),而非直接安装依赖 API key 的第三方 skill。
