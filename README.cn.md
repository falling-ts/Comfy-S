# Comfy — AI 驱动的 ComfyUI 全模态工作区

> 本仓库是一套开箱即用的 **ComfyUI 全模态工作区**:包含 ComfyUI 主程序、MiniMax H3 视频 + Qwen 系列图像 + Stable Audio/Qwen3-TTS 音频生成、45 个自定义节点(GGUF/KJNodes/超分/加速等)、35 个图片/视频/音频工作流,以及模型目录规划。
>
> **核心思路:所有安装、配置、运行、出图、训练工作流,都交给 AI(OpenCode)来做。** 你只需要:装 Git → 克隆本仓库 → 装 OpenCode → 让它干活。

---

## 目录

- [这是什么](#这是什么)
- [开始之前](#开始之前)
- [第 1 步:安装 Git](#第-1-步安装-git)
- [第 2 步:克隆本项目](#第-2-步克隆本项目)
- [第 3 步:安装 OpenCode(桌面版)](#第-3-步安装-opencode桌面版)
- [第 4 步:以管理员身份运行 OpenCode,建立软连接](#第-4-步以管理员身份运行-opencode按软连接方案建立软连接)
- [第 5 步:让 OpenCode 装它自己的 CLI(可选)](#第-5-步让-opencode-装它自己的-cli可选)
- [第 6 步:让 OpenCode 安装其它 AI 工具(可选)](#第-6-步让-opencode-安装其它-ai-工具可选)
- [第 7 步:让 OpenCode 配置 Python 环境](#第-7-步让-opencode-配置-python-环境)
- [第 8 步:让 OpenCode 安装 ComfyUI 依赖并启动](#第-8-步让-opencode-安装-comfyui-依赖并启动)
- [第 9 步:之后一切都交给 AI](#第-9-步之后一切都交给-ai)
- [常见问题](#常见问题)
- [附录](#附录)

---

## 这是什么

- **ComfyUI 主程序**(`ComfyUI\` 子模块,detached HEAD 跟随上游 release tag,当前 v0.39.2)—— 本地节点式 AI 图像/视频/音频生成引擎
- **自定义节点**(45 个,集中于根 `custom_nodes\`,经 `ComfyUI\custom_nodes\` **目录级**软链接加载;完整清单见 `AGENTS.md`):
  - `ComfyUI-FallingTS` —— 自研通用工具节点集(22 节点:Continue/Route/Fanout/Selector/Table/Switch/MarkDownTable/FrameRateConvert/ImageComposite/LoadImage/LoadVideo/LoadAudio/VideoComponents/H3AddGuide + 世界模型三节点 WorldSurroundPanorama/WorldPanoramaViews/WorldRefinePLY,以及 PreviewVideo/PreviewImageSave/AutoSaveImage/PreviewAudioSave/AudioTrim,另加 27 个前端增强)
  - `ComfyUI-GGUF` / `ComfyUI-KJNodes` —— GGUF 量化加载 / 大型工具节点包
  - `ComfyUI-SeedVR2_VideoUpscaler` / `ComfyUI-SUPIR` / `ComfyUI_UltimateSDUpscale` —— 超分放大/修复
  - H3 生态 6 插件(Spectrum / SolAttn / ReservedVRAM / Qwen3-TTS / latent-upscaler / OrbitSheets 场景参考板)+ 其余 39 个
- **工作流方案**:35 个,按编号分组(001x 万物 / 002x 场景镜头 / 003x 场景生成与世界模型 / 004x 视频生成 / 005x 拆解 / 006x 音频生成 / 007x 音频截取;见[附录 B](#附录-b工作流方案总览))
- **模型目录**(`models\`,软链接到项目根)—— 见[附录 C](#附录-c模型下载清单)
- **文档**:官方文档本地克隆 `refs\ComfyUI-Docs\`;工作区说明 `AGENTS.md`

---

## 开始之前

- **系统**:Windows 10/11 或 Linux(本仓库默认按 Windows 部署编写,Linux/macOS 部署见「附录 H 迁移 Linux」)
- **硬件**:内存 16G 以上;**有 NVIDIA 显卡**(N 卡)体验最佳;无 N 卡也能跑,但慢
- **网络**:能访问外网即可;部分地区需代理;国内下载模型可用 `hf-mirror.com` 镜像(见附录 E)
- **你不需要提前装任何东西**——Python、CUDA、虚拟环境、各种 CLI 都由 AI 帮你装

---

## 第 1 步:安装 Git

Git 用于克隆本仓库、管理子模块。到 **https://git-scm.com/download/win** 下载安装包(64-bit,默认选项一路「下一步」),装完在终端执行 `git --version` 能打印版本号即成功。

---

## 第 2 步:克隆本项目

在 Git Bash 里执行:

```bash
git clone https://github.com/falling-ts/Comfy
cd Comfy
```

完成后,你会得到一个包含 `ComfyUI\`、各 `ComfyUI-*\` 插件、`workflows\`、`models\` 的完整工作区。**后续所有操作都在这个 `Comfy` 目录里进行。**

> 提示:克隆后 `models\` 是空的(模型体积大,不随仓库分发),需要按[附录 C](#附录-c模型下载清单)下载;`media\` 是空的,是输入/输出文件的家。

---

## 第 3 步:安装 OpenCode(桌面版)

OpenCode 是你和这套工作区之间的 AI 主力,负责装软件、配环境、跑工作流。

1. 浏览器打开 **https://opencode.ai/zh/download** ,下载「**桌面端**」
2. 安装并启动 OpenCode
3. 在左侧「**添加项目**」,选择刚才克隆的 `Comfy` 目录
4. 之后在这个项目里和 AI 对话即可

---

## 第 4 步:以管理员身份运行 OpenCode,按软连接方案建立软连接

> ⚠️ **很重要**:本工作区依赖「相对路径符号链接」,把 `ComfyUI\` 里的相关目录指向项目根(`models\`、`media\`、`workflows\`、各插件目录)。**创建符号链接需要管理员权限,所以必须以管理员身份运行 OpenCode。**

1. 在开始菜单找到 OpenCode,右键 →「**以管理员身份运行**」
2. 打开本项目(添加 `Comfy` 目录),把下面这段话发给它:

> 请按以下「软连接方案」检查并修复本项目的软链接(全部用**相对路径**符号链接,共 8 个,完整清单见 `AGENTS.md`「软链接映射」):
>
> 1. **目录级插件链接**:确认 `ComfyUI\custom_nodes` 是符号链接,指向 `..\custom_nodes`(根目录插件聚合目录,45 个插件全部经这一个链接加载;**不是**旧方案的一插件一链接);
> 2. **基础链接**:`ComfyUI\input` → `..\media\七纹刻印`、`ComfyUI\output` → `..\media\七纹刻印`、`ComfyUI\models` → `..\models`、`ComfyUI\user\default\workflows` → `..\..\..\workflows`;
> 3. **子链接**:`custom_nodes\H3ReferenceSuite` → `..\refs\minimax-h3-guide\custom_nodes\H3ReferenceSuite`;`.claude` → `.agents`;`stories\.obsidian\plugins` → `..\plugins`;
> 4. 全部完成后,确认这些路径显示为「符号链接」,并验证 `ComfyUI\models\diffusion_models` 等子目录可正常进入。
>
> 注意:只能替换真实目录;`ComfyUI\temp\` 等真实目录保留;所有链接一律用相对路径,保证整个项目文件夹移动后不失效。

3. 软链接就绪后,继续[第 5 步](#第-5-步让-opencode-装它自己的-cli可选)。

---

## 第 5 步:让 OpenCode 装它自己的 CLI(可选)

习惯命令行的话,对它说「帮我安装 opencode cli 版本,具体下载安装,你从网络搜索」,装好后 `cd Comfy && opencode` 即可使用。

---

## 第 6 步:让 OpenCode 安装其它 AI 工具(可选)

需要时对它说「帮我安装以下 AI 工具:codex、claude code、cc-switch。具体下载安装,你从网络搜索」,即可获得可随时切换的 AI CLI 组合。

---

## 第 7 步:让 OpenCode 配置 Python 环境

把这段话发给 OpenCode(让它在项目根目录创建 `.venv` 虚拟环境):

> 在项目根目录创建 Python 3.13 虚拟环境 `.venv`(若系统没有 Python 3.13,先安装官方 Python 3.13)。具体下载安装,你从网络搜索。
>
> 注意:环境必须在项目根目录 `.venv`(不是系统 Python),后面所有依赖都装进这个环境,不要用系统 Python。

完成后验证(它会在终端里执行):

```powershell
.\.venv\Scripts\activate   # 类 Unix 用 source .venv/bin/activate
python --version
```

---

## 第 8 步:让 OpenCode 安装 ComfyUI 依赖并启动

把这段话发给 OpenCode(它会依次完成:装 CUDA 版 PyTorch → 装主程序依赖 → 装各插件依赖 → 启动):

> 进入 `ComfyUI` 目录,按顺序:
>
> 1. **先装 CUDA 版 PyTorch**:执行
>    `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130`
>    (先检测我的 NVIDIA 显卡和驱动支持哪个 CUDA 版本,选择匹配的 `cuXXX`;若没有 N 卡则装 CPU 版)
> 2. 再装剩余依赖:`pip install -r requirements.txt`
> 3. 然后进入 `custom_nodes\` 下全部插件目录(45 个,见 `AGENTS.md` 目录结构),逐个检查各自需要的依赖(如各自的 `requirements.txt` 或 README),都帮我安装好。
> 4. 最后回到 `ComfyUI` 目录启动:`python main.py --enable-manager`
>
> 启动成功后告诉我前端地址。

启动后,浏览器打开 **http://127.0.0.1:8188** 即是 ComfyUI 前端界面。

---

## 第 9 步:之后一切都交给 AI

环境就绪后,所有工作都可以让 AI 帮你做:

- 下载模型(按[附录 C](#附录-c模型下载清单),直接说"下载 xx 模型到 models\yyy\")
- 运行 / 修改 / 新建工作流(在 `workflows\` 里)
- 安装新自定义节点、排错、调参、出图、训练
- 视频/音频/图片生成(MiniMax H3、Stable Audio、Qwen 系列等)

一句话总结:**你负责"想要什么",AI 负责"怎么做"。**

---

## 常见问题

- **代理 / 下载慢**:默认直连;失败时用本机代理(如 Clash 的 `127.0.0.1:7890`);HuggingFace 模型国内可用 `hf-mirror.com` 镜像,把链接前缀 `huggingface.co` 换成 `hf-mirror.com` 即可(见附录 E)
- **符号链接**:`ComfyUI\custom_nodes`(目录级,聚合 45 插件)、`models`/`input`/`output`/`workflows` 等共 8 个相对路径符号链接。创建链接需要管理员权限,推荐**以管理员身份运行 OpenCode**再让它修复(见[第 4 步](#第-4-步以管理员身份运行-opencode按软连接方案建立软连接));或手动开启「开发者模式」(设置 → 隐私和安全性 → 开发者选项 → 开启开发者模式)
- **显存不足**:Klein 9B 蒸馏版较吃显存(24G 卡跑 1024 tile 偏紧,爆显存降到 768);MiniMax H3 需大显存,低显存建议用量化版或云端(详见附录 C 备注)
- **模型放好后记得重启 ComfyUI**,加载节点才会识别新模型

---

# 附录

## 附录 A · 项目结构

```
Comfy/
├── ComfyUI/                  # ComfyUI 主程序(子模块,detached HEAD,当前 v0.39.2)
│   ├── main.py               # 启动入口(python main.py --enable-manager)
│   ├── custom_nodes/         # 自定义节点(目录级软链接 → ../custom_nodes)
│   ├── input/  output/       # 输入/输出(软链接 → ../media/七纹刻印)
│   ├── user/default/workflows  # 用户工作流(软链接 → ../../../workflows)
│   └── models/               # 模型(软链接 → ../models)
├── custom_nodes/             # 插件聚合目录:45 个插件子模块 + H3ReferenceSuite 链接
│   ├── ComfyUI-FallingTS/    # 自研通用工具节点集(22 节点 + 世界模型节点 + 前端增强)
│   ├── ComfyUI-GGUF/  ComfyUI-KJNodes/   # 量化加载 / 工具节点包
│   ├── ComfyUI-OrbitSheets/  # H3 场景/角色参考板(多视角运镜 + 视觉选帧拼网格图)
│   └── ...(其余 41 个,见 AGENTS.md 目录结构)
├── docs/                     # 44 个分类文档
├── refs/                     # 7 个参考类子模块(ComfyUI-Docs / Obsidian-Dev-Docs / Obsidian-API / Qwen-Image-2.1 / qwen-image-2.1-skill / MiniMax-H3 / minimax-h3-guide)+ Qwen-Image-Edit-Skills(本地目录,非子模块)
├── workflows/                # 用户工作流 35 个(001x~007x,见附录 B)
├── models/                   # 模型实际存放处(约 263.5GB,40 个顶层目录,见附录 C)
├── media/                    # 输入图片/音频 + 生成结果(template/ + 各故事库目录,当前为 七纹刻印/)
├── templates/  webs/         # 官方模板缓存 + 三方调研(RunningHub/Bilibili/AutoDL)
├── stories/                  # Obsidian 故事写作工作区
├── backups/                  # 工作流/文档修改前备份(仅本地)
└── AGENTS.md                 # 工作区说明(供 AI 读取,目录结构/软链接/规范全在此)
```

### 软连接(共 8 个,全部相对路径)

`ComfyUI\input`/`output` → `media\七纹刻印`、`ComfyUI\models` → `models`、`ComfyUI\user\default\workflows` → `workflows`、`ComfyUI\custom_nodes` → `custom_nodes`(**目录级,聚合 45 插件**)、`custom_nodes\H3ReferenceSuite` → `refs\minimax-h3-guide\...`、`.claude` → `.agents`、`stories\.obsidian\plugins` → `stories\plugins`。全部为**相对路径**符号链接,项目整体移动后不失效;创建/修复需管理员权限,完整清单见 `AGENTS.md`「软链接映射」;`ComfyUI\temp\` 为真实目录(非链接),可随时清理。

## 附录 B · 工作流方案总览

`workflows\` 下共 **35 个**主工作流,按「编号-用途」命名分组(前端保存即在此):

### 图片/万物类(001x,10 个;图片侧基于 Qwen-Image-2512 / Qwen-Image 2.1 / Qwen-Edit 2511,0013~0015 为 MiniMax H3)

| 工作流 | 用途 |
|--------|------|
| `0011_万物建模` | 主线主流程(万物建模) |
| `0010_灰度遮罩` | 灰度遮罩工具 |
| `0012_万物变化` | 万物变化/变换 |
| `0013_首图建模` | H3 I2VA:首图 → 视频 → 抽帧 → 反推人物资产 |
| `0014_参考建模` | H3 Ref2VA 参考建模 |
| `0015_建模截帧` | 建模截帧 |
| `0016_建模拆图` | 拼图按 2×2 / 3×3 拆成单图并自动保存 |
| `0017_建模细节` | 逐块局部细节精修(Qwen-Image-Edit) |
| `00110_万物建模_QI2.1` | `0011` 的 Qwen-Image 2.1 版(**共用** `0011` 数据表) |
| `00120_万物变化_QI2.1` | `0012` 的 Qwen-Image 2.1 版(**共用** `0012` 数据表) |

### 场景镜头类(002x,6 个)

| 工作流 | 用途 |
|--------|------|
| `0020_场景首帧` | 场景首帧生成 |
| `0021_场景拉镜` | 镜头拉远/拉近变换 |
| `0022_场景推镜` | 镜头推进变换 |
| `0023_场景旋镜` | 镜头环绕旋转 |
| `00200_场景首帧_QI2.1` | `0020` 的 Qwen-Image 2.1 版(**共用** `0020` 数据表) |
| `00220_场景推镜_QI2.1` | `0022` 的 Qwen-Image 2.1 版(**共用** `0022` 数据表) |

### 场景生成与世界模型类(003x,6 个,MiniMax H3)

| 工作流 | 用途 | H3 模式 |
|--------|------|---------|
| `0030_文生场景` | 文本 → 场景视频(仅画面,无音轨) | T2VA(fl2va) |
| `0031_首帧场景` | 首帧图 → 场景视频 | I2V(fl2va) |
| `0032_参考场景` | 多图 + 多视频参考 → 视频 | R2V(ref2va) |
| `0033_OrbitSheets场景` | 锚点图 → H3 多视角运镜 → 视觉选帧拼「场景参考板」网格图 | I2V(fl2va)+ OrbitSheets 插件 |
| `0034_世界模型` | 360° 环绕视频 → 横向展开长图 → 视角批 → 一个最高质量 3DGS PLY | 世界模型(自研节点 + HYWM2) |
| `0035_场景截帧` | 加载视频 → 截帧 → 8 单图 + 四图/八向合成自动保存 | — |

### 视频生成类(004x,5 个,MiniMax H3)

| 工作流 | 用途 | H3 模式 |
|--------|------|---------|
| `0040_文生视频` | 文本 → 视频(与 0030 同构的通用版) | T2VA(fl2va) |
| `0041_首帧视频` | 首帧图 → 视频 | I2V(fl2va) |
| `0042_首尾视频` | 首尾帧 → 视频 | fl2va |
| `0043_关键帧视频` | AddGuide 锚定任意帧 | 关键帧(fl2va) |
| `0044_参考视频` | 参考图/视频 → 视频 | R2V(ref2va) |

> 0030/0031/0032 与 0040/0041/0042/0044 结构一一对应(前者为场景流水线版,后者为通用版);均已去除音频轨道,视频 + 音频在后期流水线(005x-007x)中合并。0033 为场景参考生产补充:产出「场景参考板」网格图(供 0032/0044 作参考输入)。

### 拆解类(005x,2 个)

| 工作流 | 用途 |
|--------|------|
| `0050_视频截帧` | 视频 → 逐帧图片 |
| `0051_视频拆音` | 视频 → 分离音频 |

### 音频生成类(006x,5 个)

| 工作流 | 用途 | 核心模型 |
|--------|------|---------|
| `0060_背景音乐` | 纯器乐 BGM | Stable Audio 3(内置 Sage 加速) |
| `0061_环境音效` | 环境/氛围音 | Stable Audio 3 |
| `0062_效果音效` | 一次性/打击音效 | Stable Audio 3 |
| `0063_文生人声` | 文本描述音色 → 说话 | Qwen3-TTS VoiceDesign |
| `0064_参考人声` | 3s 参考音频克隆 → 说话 | Qwen3-TTS CustomVoice |

### 音频截取类(007x,1 个)

| 工作流 | 用途 |
|--------|------|
| `0070_截取声音` | 加载音频,在波形上截取一段,预览/保存三份 |

> 2026-08-09 前曾归档于 `templates\` 的旧版图片 8/视频 4/音频 5 工作流已删除,全部以当前编号体系为准。

## 附录 C · 模型下载清单

> 方案原则:全开源、本地推理、零 API 费用。以下清单与本地 `models\` 目录**一一对应**(2026-10-11 核查:约 263.5GB,40 个顶层目录),状态列反映本地实际就绪情况;全新环境(Linux 5090 服务器)需按下载地址重新获取,或按[附录 H.4](#h4-文件搬运与软链接)随 `models` 整体 rsync 迁移。**下载顺序建议**:先音频小件(Qwen3-TTS 全套、SenseVoice、Stable Audio 3)→ 视频大件(MiniMax H3 全套,fl2va 与 ref2va 都要下)→ 图片大件(Qwen-Image 2512/Edit 2511、Qwen-Image 2.1、FLUX.2 Klein)。注意 `flux-2-klein-9b-fp8` 为**门控仓库**(需登录 HF 接受 BFL 协议);模型放好后**重启 ComfyUI** 才会被识别。

### 图片类

| 模型 | 放置目录 | 状态 | 下载地址 |
|------|---------|------|---------|
| `qwen_image_2512_fp8_e4m3fn.safetensors` | `models\diffusion_models\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_2512_fp8_e4m3fn.safetensors> |
| `qwen_image_fp8_e4m3fn.safetensors`(2512 前代,备用) | `models\diffusion_models\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_fp8_e4m3fn.safetensors> |
| `qwen_image_edit_2511_fp8mixed.safetensors` | `models\diffusion_models\` | ✅ 已就绪 | <https://www.modelscope.cn/models/Kakazhuce/qwen_image_edit_2511_fp8mixed/resolve/master/qwen_image_edit_2511_fp8mixed.safetensors> |
| `qwen_image_2.1_bf16.safetensors`(Qwen-Image 2.1 基座,7B 统一「生成+编辑」) | `models\diffusion_models\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/Qwen-Image-2.1_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_2.1_bf16.safetensors> |
| `flux-2-klein-9b-fp8.safetensors` | `models\diffusion_models\` | ✅ 已就绪 | <https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-fp8/resolve/main/flux-2-klein-9b-fp8.safetensors> ⚠️门控 |
| `triposplat_fp16.safetensors`(历史遗留,当前工作流未使用) | `models\diffusion_models\` | ✅ 已就绪 | 本地文件(早期实验保留) |
| `qwen_3_8b_fp8mixed.safetensors`(Klein 文本编码器) | `models\text_encoders\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/flux2-klein-9B/resolve/main/split_files/text_encoders/qwen_3_8b_fp8mixed.safetensors> |
| `full_encoder_small_decoder.safetensors`(Klein/FLUX.2 解码器) | `models\vae\` | ✅ 已就绪 | <https://huggingface.co/black-forest-labs/FLUX.2-small-decoder/resolve/main/full_encoder_small_decoder.safetensors> |
| `qwen_2.5_vl_7b_fp8_scaled.safetensors`(Qwen-Edit 文本编码器) | `models\text_encoders\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors> |
| `qwen3vl_8b_bf16.safetensors`(Qwen-Image 2.1 文本编码器) | `models\text_encoders\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/Qwen-Image-2.1_ComfyUI/resolve/main/split_files/text_encoders/qwen3vl_8b_bf16.safetensors> |
| `qwen_image_vae.safetensors` | `models\vae\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors> |
| `qwen_image_2.1_vae_bf16.safetensors`(Qwen-Image 2.1 VAE,64 通道 RGBA) | `models\vae\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/Qwen-Image-2.1_ComfyUI/resolve/main/split_files/vae/qwen_image_2.1_vae_bf16.safetensors> |
| `flux2-vae.safetensors`(历史遗留,当前工作流未使用) | `models\vae\` | ✅ 已就绪 | 本地文件(早期实验保留) |
| `triposplat_vae_decoder_fp16.safetensors`(历史遗留,当前工作流未使用) | `models\vae\` | ✅ 已就绪 | 本地文件(早期实验保留) |
| `4xNomos8kDAT.safetensors`(放大,推荐) | `models\upscale_models\` | ✅ 已就绪 | <https://huggingface.co/Phips/4xNomos8kDAT/resolve/main/4xNomos8kDAT.safetensors> |
| `Qwen-Image-2512-Lightning-4steps-V1.0-fp32.safetensors`(2512 加速 LoRA) | `models\loras\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/loras/Qwen-Image-2512-Lightning-4steps-V1.0-fp32.safetensors> |
| `Qwen-Image-Lightning-4steps-V1.0.safetensors`(2512 前代加速 LoRA,备用) | `models\loras\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/loras/Qwen-Image-Lightning-4steps-V1.0.safetensors> |
| `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors`(2511 加速 LoRA) | `models\loras\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/loras/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors> |
| `qwen-image-edit-2511-multiple-angles-lora.safetensors`(多视角 LoRA,配 `ComfyUI-qwenmultiangle` 插件) | `models\loras\` | ✅ 已就绪 | 社区 LoRA(本地文件,5090 随 `models` 迁移) |
| `birefnet.safetensors`(抠图/背景移除) | `models\background_removal\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/birefnet> |
| `Kook_Qwen_2512_真实幻想.safetensors`(2512 写实/幻想风格 LoRA,图片-01 文生图在用) | `models\loras\` | ✅ 已就绪 | 本地文件(社区 LoRA,无固定 URL;5090 随 `models` 迁移,见[附录 H.4](#h4-文件搬运与软链接)) |
| `[Qwen-Edit]3DChineseStyle_25.safetensors`(Qwen-Edit 3D 国风 LoRA,图片-01 文生图在用) | `models\loras\` | ✅ 已就绪 | 本地文件(社区 LoRA,无固定 URL;5090 随 `models` 迁移,见[附录 H.4](#h4-文件搬运与软链接)) |
| `Qwen-Image-InstantX-ControlNet-Inpainting.safetensors`(Qwen-Image Inpainting ControlNet,扩图/局部重绘;场景拉镜/推镜「扩图」段在用) | `models\controlnet\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/Qwen-Image-InstantX-ControlNets/resolve/main/split_files/controlnet/Qwen-Image-InstantX-ControlNet-Inpainting.safetensors> |

### 人脸修复(facerestore_models,Impact-Pack Detailer / ReActor 首次使用时自动下载)

| 模型 | 放置目录 | 状态 | 下载地址 |
|------|---------|------|---------|
| `GFPGANv1.4.pth`(通用人脸修复,优先) | `models\facerestore_models\` | ✅ 已就绪 | <https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/GFPGANv1.4.pth> |
| `GFPGANv1.3.pth`(备用) | 同上 | ✅ 已就绪 | <https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/GFPGANv1.3.pth> |
| `codeformer-v0.1.0.pth`(CodeFormer 细节增强,非商用许可) | 同上 | ✅ 已就绪 | <https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/codeformer-v0.1.0.pth> |
| `GPEN-BFR-512.onnx`(GPEN,轻量提速) | 同上 | ✅ 已就绪 | <https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/GPEN-BFR-512.onnx> |

### 其余已就绪槽位(2026-10-11)

| 模型 | 放置目录 | 状态 | 下载地址 |
|------|---------|------|---------|
| `minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors`(H3 fun-controlnet) | `models\model_patches\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/model_patches/minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors> |
| `minimax_h3_latent_upscaler_3d_fp16.safetensors`(配 `h3-latent-upscaler` 插件) | `models\latent_upscale_models\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/latent_upscale_models/minimax_h3_latent_upscaler_3d_fp16.safetensors> |
| `minimaxh3_*.safetensors` —— 10 个 H3 动作嵌入(`art_is_explosion`/`blooming_flowers`/`bullet_time`/`dark_magic`/`fire_breath`/`four_seasons`/`kiss_camera`/`spiral_ascent`/`storm_magic`/`truman_show`) | `models\embeddings\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/tree/main/embeddings> |
| `depth_anything_3_base` / `depth_anything_3_mono_large` / `depth_anything_3_small` | `models\geometry_estimation\` | ✅ 已就绪 | <https://huggingface.co/depth-anything/Depth-Anything-3> |
| `dino_v3_vit_h.safetensors`(CLIP 视觉) | `models\clip_vision\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/clip_vision/dino_v3_vit_h.safetensors> |
| `taeh3.safetensors`(H3 预览用近似 VAE) | `models\vae_approx\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae_approx/taeh3.safetensors> |
| HY-World 2.0 权重:`model.safetensors` + `config.json`(3.05 GB,供 `ComfyUI-HYWM2` 插件 / 工作流 `0034_世界模型`) | `models\hywm2\` | ✅ 已就绪 | <https://huggingface.co/tencent/HY-World-2.0> |
| SD1.x / SD2.x 标准推理配置 11 个 yaml | `models\configs\` | ✅ 已就绪 | 随 ComfyUI 仓库自带 |

### 音频类

| 模型 | 放置目录 | 状态 | 下载地址 |
|------|---------|------|---------|
| `stable_audio_3_medium.safetensors` | `models\checkpoints\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/stable-audio-3/resolve/main/checkpoints/stable_audio_3_medium.safetensors> |
| `t5gemma_b_b_ul2.safetensors`(StableAudio 文本编码器) | `models\text_encoders\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/stable-audio-3/resolve/main/text_encoders/t5gemma_b_b_ul2.safetensors> |
| Qwen3-TTS-12Hz-1.7B-Base(万能:克隆+对话,工作流 ④⑤ 默认,~4.5 GB) | 插件自动下载至 `models/TTS/Qwen/` | ✅ 已就绪 | <https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base> |
| Qwen3-TTS-12Hz-1.7B-CustomVoice(9 预设音色,~4.5 GB) | 同上 | ✅ 已就绪 | <https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice> |
| Qwen3-TTS-12Hz-1.7B-VoiceDesign(自然语言造声,~4.5 GB) | 同上 | ✅ 已就绪 | <https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign> |
| Qwen3-TTS-12Hz-0.6B-Base(低显存克隆,约 4GB VRAM,~2.5 GB) | 同上 | ✅ 已就绪 | <https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base> |
| Qwen3-TTS-12Hz-0.6B-CustomVoice(低显存预设音色,~2.5 GB) | 同上 | ✅ 已就绪 | <https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice> |
| SenseVoiceSmall(ASR 自动转写参考文本,工作流 ⑤ 必需,~0.9 GB) | 插件自动下载 | ✅ 已就绪 | <https://huggingface.co/FunAudioLLM/SenseVoiceSmall> |
> **Qwen3-TTS 下载说明**:均为**目录型模型**,必须整目录下载(仅下 safetensors 无法加载);`Qwen3TTSLoader` 的 `auto_download`(默认开)会自动从 ModelScope 整目录下载。手动下载时:5 个 Qwen3-TTS 放 `models/TTS/Qwen/<模型名>/`,`SenseVoiceSmall` 放 `models/TTS/SenseVoiceSmall/`。

| `qwen3.5_2b_bf16.safetensors`(音频编码) | `models\text_encoders\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/Qwen3.5/resolve/main/text_encoders/qwen3.5_2b_bf16.safetensors> |

### 视频类(MiniMax H3,Comfy-Org/MiniMax-H3 仓库)

| 模型 | 放置目录 | 状态 | 下载地址 |
|------|---------|------|---------|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors`(FL2VA,T2V/I2V 用) | `models\diffusion_models\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors> |
| `minimax_h3_ref2va_pruned_int8_convrot.safetensors`(Ref2VA,**R2V 参考生视频用,独立文件**) | `models\diffusion_models\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors> |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`(文本编码器) | `models\text_encoders\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors> |
| `qwen3vl_32b_minimax_h3_int8_convrot.safetensors`(文本编码器,与 nvfp4 两档并存) | `models\text_encoders\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors> |
| `minimax_h3_video_vae_fp16.safetensors`(视频 VAE) | `models\vae\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_fp16.safetensors> |
| `minimax_h3_video_vae_int8_convrot.safetensors`(视频 VAE,与 fp16 两档并存) | `models\vae\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_int8_convrot.safetensors> |
| `minimax_h3_audio_vae_fp32.safetensors`(音频 VAE) | `models\vae\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_audio_vae_fp32.safetensors> |

> **fl2va 与 ref2va 是同一基座的任务变体**:文生/图生工作流(0030/0031/0040/0041)用 fl2va,参考生成工作流(0032/0044)用 ref2va,两者都要下。仓库另有 bf16/int8_convrot/pruned_fp8_scaled 档可选。

### MiniMax H3 Turbo LoRA(官方 Comfy-Org 转换版,已就绪)

> Comfy-Org 官方转换的 H3 Turbo 加速 LoRA(bf16,**约 5 倍提速**),来源 `Comfy-Org/MiniMax-H3` 仓库 `loras/` 目录;国内下载把前缀 `huggingface.co` 换成 `hf-mirror.com`。配套要求:ComfyUI v0.30.0+、KJNodes、ComfyUI-ReservedVRAM、SageAttention。

| 模型 | 放置目录 | 状态 | 下载地址 |
|------|---------|------|---------|
| `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors`(fl2va 4 步,768p 训练域,1.82GB,工作流默认) | `models\loras\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors> |
| `minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors`(fl2va 4 步 v1.2,更新修订版) | `models\loras\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors> |
| `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors`(fl2va 8 步,质量更高,1.82GB) | `models\loras\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors> |
| `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors`(ref2va 4 步,R2V 工作流用,0.36GB) | `models\loras\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors> |
| `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`(ref2va 8 步,质量更高) | `models\loras\` | ✅ 已就绪 | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors> |

### MiniMax H3 加速要点

- **标配(工作流已内置)**:Sage Attention(+20~30%,KJNodes `Patch Sage Attention KJ`)+ EasyCache(ComfyUI 内置节点,参数 0.30/0.20/0.90,代价为长视频连贯性下降)+ Turbo LoRA(~5x,见上节)
- **显存**:8G/12G/16G 均可跑(动态卸载,clip 编码器放 CPU);本地最高 768p,2K 需官方 API;显存紧张可加 `🎈VRAM/RAM-Cleanup` 节点或 `--vram-headroom`

## 附录 D · 需安装的插件

| 插件 | 用途 | 地址 | 状态 |
|------|------|------|------|
| ComfyUI-Qwen3-TTS | 开源 TTS 主方案(克隆/音色设计/情绪标签/无限多角色对话,Apache-2.0) | <https://github.com/wanaigc/ComfyUI-Qwen3-TTS> | ✅ 已装 |
| ComfyUI-Angelo(可选) | Klein 点击式编辑 | <https://github.com/shootthesound/ComfyUI-Angelo> | 未装(需要时再装) |

### H3 加速插件(已装,2026-08-06)

| 插件 | 用途 | GitHub | 状态 |
|------|------|--------|------|
| ComfyUI-Spectrum-MiniMax-H3 | 谱特征预测,减少采样求值(275★) | <https://github.com/xmarre/ComfyUI-Spectrum-MiniMax-H3> | ✅ submodule |
| ComfyUI-SolAttn_triton | Sol-Attn 稀疏注意力(kijai,仅 4090/5090 实测) | <https://github.com/kijai/ComfyUI-SolAttn_triton> | ✅ submodule |
| ComfyUI-ReservedVRAM | 动态预留显存,防 OOM | <https://github.com/Windecay/ComfyUI-ReservedVRAM> | ✅ submodule |
| H3ReferenceSuite(H3RefLoader) | H3 参考加载/工作流套件 | 随 <https://github.com/juemin4-source/minimax-h3-guide> | ✅ 软链接(见附录 A) |

> EasyCache 为 ComfyUI 内置节点(无需插件);曾考虑的 ComfyUI-MiniMaxH3-Cache / ComfyUI_GJJ_Nodes 未安装(前者以内置 EasyCache 等价替代,后者非必要)。

### 扩图/裁切放大插件(已装,2026-08-10)

| 插件 | 用途 | GitHub | 状态 |
|------|------|--------|------|
| ComfyUI-Impact-Pack | 局部放大/检测精修:`DetailerForEach`/`FaceDetailer` 区域框选→裁剪→放大→重绘→贴回(3251★) | <https://github.com/ltdrdata/ComfyUI-Impact-Pack> | ✅ submodule |
| ComfyUI_LayerStyle | 图层风格化节点集:`LayerUtility: CropByMask`/`LayerMask: MaskBoxDetect` 画遮罩选区域(3118★) | <https://github.com/chflame163/ComfyUI_LayerStyle> | ✅ submodule |
| ComfyUI-Easy-Use | 易用节点集:`easy imageCrop` 前端拖框截图、`easy imageSplitGrid` 九宫格拆块放大(2651★) | <https://github.com/yolain/ComfyUI-Easy-Use> | ✅ submodule |
| ComfyUI-SeedVR2_VideoUpscaler | SeedVR2 高清修复/放大(图像+视频,2723★) | <https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler> | ✅ submodule |
| ComfyUI-SUPIR | SUPIR 超分放大修复(2303★) | <https://github.com/kijai/ComfyUI-SUPIR> | ✅ submodule |

> 以上全部注册为 **git submodule**,经 `ComfyUI\custom_nodes\` **目录级**相对符号链接加载(单链接聚合全部插件)。加速启用细节见[附录 C 加速要点](#minimax-h3-加速要点)。

## 附录 E · 网络与镜像

- **默认直连外网**;直连失败(超时/403/TLS 被掐)时,改用本机代理,如 Clash Verge 混合端口 `127.0.0.1:7890`(HTTP 与 SOCKS5 均可)
- **HuggingFace 国内镜像**:把下载链接前缀 `huggingface.co` 换成 `hf-mirror.com` 即可,例:
  `https://hf-mirror.com/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_fp16.safetensors`
- 部分站点(如 OpenAI 系域名)直连会被 Cloudflare 拦截,需走允许对应域名的代理节点

## 附录 H · 迁移到 Linux + RTX 5090D 服务器（2026-08-06）

> 目标:Windows(8GB 显存 / 16GB 内存)→ Linux 服务器(RTX 5090D,32GB GDDR7)。
> 本机基准环境:torch 2.13.0+cu130、sageattention 2.2.0+cu130(post6)、triton-windows 3.7.1.post27(Windows 专属,Linux 换 `triton`)。

### H.1 硬件 / 驱动(先决条件)

- RTX 5090D = Blackwell 架构,**sm_120**,32GB GDDR7;CUDA 核心与 5090 相同(21760),但 AI 算力约为 5090 的 71%(2375 vs 3352 TOPS)
- **Linux 驱动必须 ≥ 570**(CUDA 12.8+),建议直接装最新 580/6xx 系;装完 `nvidia-smi` 能识别 sm_120 才可继续
- torch 必须支持 sm_120:**2.7+cu128 及以上**;本机用的 2.13.0+cu130 满足。切勿用旧 torch(2.5.x/cu124 会报 `no kernel image available for sm_120`)

### H.2 环境重建(Linux 不能直接复用 Windows 环境)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install torch==2.13.0+cu130 torchvision==0.28.0+cu130 torchaudio==2.11.0+cu130 \
  --index-url https://download.pytorch.org/whl/cu130
# 其余依赖从 Windows `pip freeze` 生成 requirements,唯一替换:
#   triton-windows==3.7.1.post27 → triton(与 torch 2.13 匹配)
```

- **sageattention**:2.2 支持 Blackwell;源码编译前设置 `TORCH_CUDA_ARCH_LIST="12.0"`(**只写 12.0,不要加 9.0**,否则编译失败);Blackwell 上相对 torch attention 提速约 6%(社区实测,低于 Ada)

### H.3 启动参数(与 Windows 的差异,重点)

| Windows 参数 | Linux 处理 |
|---|---|
| `--disable-pinned-memory` | **删除**(Windows 0.30.x 回归修复用;Linux pinned 内存可用到 95% RAM,是加速项) |
| `--fast-disk` | **删除**(8G 显存/16G 内存的妥协;32G 显存可整体装下 Qwen-2512 fp8 约 19.5G,无需磁盘换页) |
| `--enable-manager` | 保留 |
| 建议新增 | 默认 dynamic VRAM 即可;模型常驻不吃紧时可试 `--highvram`(主模型 19.5G + 文本编码器 7.9G ≈ 27.4G) |

启动脚本改为 `start-comfyui.sh`:

```bash
#!/usr/bin/env bash
cd "$(dirname "$0")/ComfyUI"
source ../.venv/bin/activate
python main.py --enable-manager
```

### H.4 文件搬运与软链接

- 超项目:`git clone --recurse-submodules <remote>`(**54 个子模块**)
- **models 约 263.5GB 单独 rsync**(`rsync -avP`);服务器需预留 ≥350GB NVMe
- 软链接重建(`ln -s` 相对路径,共 8 个,见附录 A 清单):
  - `ComfyUI/input → ../media/七纹刻印`、`ComfyUI/output → ../media/七纹刻印`、`ComfyUI/models → ../models`、`ComfyUI/user/default/workflows → ../../../workflows`
  - `ComfyUI/custom_nodes → ../custom_nodes`(**目录级,聚合 45 插件**)、`custom_nodes/H3ReferenceSuite → ../refs/minimax-h3-guide/custom_nodes/H3ReferenceSuite`、`.claude → .agents`、`stories/.obsidian/plugins → ../plugins`
- `ComfyUI-FallingTS/.env`(API Key)不进 git,服务器上单独放置并 `chmod 600`
- 中文文件名 / 路径在 Linux UTF-8 下无问题

### H.5 服务器建议

- 内存 **≥64GB**(H3 视频流程吃内存,32G 是底线);配 32~64GB swap 兜底
- 远程访问:SSH 端口转发到 `127.0.0.1:8188`,或 `--listen 0.0.0.0` + 防火墙白名单
- 5090D 满载 575W,确认电源与散热余量
