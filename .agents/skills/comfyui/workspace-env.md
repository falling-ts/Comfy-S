# 本工作区的运行环境、模型与网络

> 本文承载本机(`D:\AI\Comfy`)的版本、依赖、模型清单与网络策略。与本技能根目录的 `machine.md` 互补:`machine.md` 是 kit 采集的机器事实快照,本文是项目维护的版本/模型/代理口径。

## 版本与运行

- **Python 虚拟环境:项目内 `.venv`**(2026-08-16 由 conda 环境迁移而来,官方 `python -m venv` 基于系统 Python 3.13.13 创建;原 conda 专用环境已删除)。启动一律用 `.venv\Scripts\python.exe`(类 Unix 为 `.venv\bin/python`),不要用系统级 Python 或任何 conda 环境运行主程序
- **运行环境 `.venv`:Python 3.13.13 / torch 2.13.0+cu130(CUDA 13.0,RTX 4060 8GB VRAM)**,启动脚本与本文档均用它(`.venv\Scripts\python.exe`,类 Unix 为 `.venv\bin/python`);依赖安装顺序:torch(cu130 index)→ `ComfyUI\requirements.txt` → 插件 requirements → 加速依赖,迁移后与旧 conda 环境包版本对齐(当时的 conda/venv `pip freeze` 快照已随 `backups\` 清空, 要比对就现场 `pip freeze` 生成)
- 共享关键版本(均与核心 v0.39.2 `requirements.txt` 钉定版本一致):comfyui-frontend-package **1.53.10**、comfyui-manager **4.2.2**、comfyui-workflow-templates **0.11.78**、comfyui-embedded-docs **0.5.13**、comfy-aimdo **0.5.5**、comfy-kitchen **0.2.37**、sageattention **2.2.0**(cu130;本地 wheel 已不留档)、triton **3.7.1.post27**(⚠️ Windows 上以 `triton-windows` 包分发,`importlib.metadata.version("triton")` 会报 PackageNotFoundError,以 `triton_windows-*.dist-info` 为准;README 附录 H 的迁移记录同口径)、transformers 4.57.3、diffusers 0.39.0、numpy 2.2.6(受 opencv 4.12 依赖约束 `numpy<2.3`,勿升回 2.5.x)、opencv-python/opencv-contrib-python/opencv-python-headless 4.12.0.88(ComfyUI-LNL 声明 `opencv-python~=4.12.0`)、onnxruntime-gpu 1.29.0、safetensors 0.8.0
- **核心升级流程**(2026-09-21 由 v0.36.0 → v0.37.0 实践; 2026-10 已升至 **v0.39.2**):`git -C ComfyUI fetch --tags` → 查最新 tag → `git checkout <tag>`(detached;工作树里被删的上游占位文件不受影响,不会冲突) → 按 `requirements.txt` 差异补装依赖 → 重启 → `custom_nodes\ComfyUI-FallingTS\dev\_check-workflow-node-compat.py` 验证工作流用到的节点类型全部仍注册 → 根仓库提交子模块指针。升级前先 `pip freeze` 备份到 `backups\`
- **升级兼容性判据**:前端内置节点(`Note`/`MarkdownNote`/`Reroute`/`PrimitiveNode`)与前端注册的 UUID 型 API 节点**不出现**在后端 `/object_info` 里,比对时须白名单排除(脚本已内置),否则每次升级都会误报缺失
- **插件更新流程**(2026-09-21 实践,45 个插件仓库):逐个 `git -C custom_nodes/<插件> fetch --tags --prune` → `git rev-list --count HEAD..origin/<默认分支>` 看落后数 → 在分支上的 `git merge --ff-only origin/<分支>`,**detached HEAD 的** `git checkout <默认分支>`(自动建跟踪分支并到位) → `git diff <旧> <新> -- requirements.txt` 判断是否补装依赖 → 含 `.gitmodules` 的插件(`ComfyUI-Easy-Use`/`ComfyUI-Impact-Pack`/`ComfyUI_UltimateSDUpscale`)再 `git submodule update --init --recursive` → 重启 → 跑 `_check-workflow-node-compat.py`。⚠️ **只更新本地,不推送**(上游子项目禁止提交/推送);更新前先确认各插件 `Ahead=0`,否则会覆盖本地提交
- **模板库更新**:从**运行中的服务**拉 `GET /templates/index.zh.json`(官方核心,按中文 `title` 归入 `templates\<分类>\`)+ `GET /api/workflow_templates`(插件模板 → `自定义节点\<插件>\`),增量写入并重建 `workflow-templates-list.md`;版本号由 `/system_stats` 与 pip 包**动态读取**(勿再硬编码)。拉取逻辑用一次性脚本经 stdin 就地执行(不落盘);**不删除**已下线文件,只在末尾列出供人工判断(2026-09-21 遇到 `图像工具/api_flux_vto.json` 已从索引移除,备份到 `backups\` 后删除)
- **pip 默认走清华镜像**(`pypi.tuna.tsinghua.edu.cn`,配置在 `%APPDATA%\pip\pip.ini`):上游刚发布的包镜像可能尚未同步(实测 `comfyui-workflow-templates-media-assets-02==0.1.3` 上传 19 小时后仍查不到,报 `No matching distribution found`),此时临时加 `--index-url https://pypi.org/simple` 走官方源直连即可
- 前端打包目录 = `<venv>/Lib/site-packages/comfyui_frontend_package/static/`:主入口 `index.html`,打包产物 `assets\`;插件 `web\js` 经 `GET /extensions` 运行时加载、**不参与前端打包**(重建 `assets\` 不影响扩展;前端包 `static\scripts\` 保留 `app.js`/`api.js` 等扩展 import 入口)
- 测试插件「从零安装」:清理浏览器缓存的 `assets\` 打包文件后,对 `http://127.0.0.1:8188` 强刷(`Ctrl+Shift+R`)再验证;**磁盘 `assets\` 勿删**(删了页面白屏)
- 启动:

先激活虚拟环境(`.venv\Scripts\activate` 或 `.venv/bin/activate`),再:

```text
cd ComfyUI
python main.py --enable-manager
```

- 或直接 `.venv\Scripts\python.exe main.py --enable-manager`(在 `ComfyUI` 下;类 Unix 用 `.venv/bin/python`);或运行 `bash comfy-server.sh`(统一跨平台后台服务式,Windows Git Bash / Linux 均可:停旧服务 → 后台启动 → 等端口;Windows 已带 `--disable-pinned-memory --fast-disk`,Linux 用 conda 环境 comfy + `--reserve-vram 22`,可覆盖 `PORT`/`WAIT`/`PY_BIN`/`LOG`/`RESERVE_VRAM`)
- 前端默认地址 `http://127.0.0.1:8188`
- 注意:主程序必须用 `.venv` 的 Python 运行(`.venv\Scripts\python.exe`,类 Unix 为 `.venv/bin/python`),不要用系统级 Python 或任何 conda 环境运行
- 改自定义节点代码后**重启 ComfyUI 生效**,无需复制文件(经软链接即时加载)
- ⚠️ **重启前先确认能不能杀掉旧进程**:`comfy-server.sh` 的停旧服务在 Windows 用 `netstat` + `taskkill /F /T`,但**进程由提权(管理员)shell 启动时,非提权会话会 `Access is denied`**,而脚本把失败 `|| true` 吞掉;更坑的是它的"端口已监听"就绪判据会被**旧进程**满足 ⇒ 打印 `OK: ComfyUI 就绪` 却仍是旧代码在跑(实测 2026-09-30:新实例 `Port 8188 is already in use` 死在日志里,新加的 `/fallingts_prerun/run` 路由一直 405)。**判据**:`Get-NetTCPConnection -LocalPort 8188 -State Listen | % OwningProcess` 与启动前对比 PID;PID 没变就是没重启成功,此时只能让用户自己重启(或在用户同意下用 `Start-Process -Verb RunAs` 走 UAC)
- 验证插件新代码而**不能重启主实例**时,起一个**独立端口的临时实例**(如 `.venv\Scripts\python.exe main.py --cpu --port 8189 --disable-pinned-memory`,日志单独一份):它经同一软链接读到同一份插件代码,不影响 8188;它会打印 `Database is locked. Another ComfyUI process is already using this database.`,只读验证可忽略(要写用户数据时加 `--database-url sqlite:///<另一个>.db`)

### ComfyUI 官方日志(排查插件/请求问题优先看这里)

- **官方日志文件**:`ComfyUI\user\comfyui.log`;多实例同时跑时按端口命名 `comfyui_<port>.log`(如 `comfyui_8188.log`);轮转保留 `comfyui.prev.log` / `comfyui.prev2.log`。启动时日志会打印一行 `** Log path: <路径>` 指明当前文件。
- **CLI 配置**:`--verbose LEVEL FILE` 可自定义控制台级别与文件输出(可重复),如 `--verbose INFO ComfyUI\user\comfyui_8188.log`;`--log-stdout` 把普通输出切到 stdout。
- **日志类别/格式**:行首 `[YYYY-MM-DD HH:MM:SS.mmm]` 时间戳,含级别(DEBUG/DETAIL/INFO/WARNING/ERROR/CRITICAL)。内容包括:启动信息(版本/设备/VRAM)、插件加载(`Import times for custom nodes`)、模型加载、报错 traceback、ComfyUI-Manager 网络操作,以及**自定义节点通过 `logging` 输出**的信息(插件里用 `print` 不一定进文件,建议用 `logging` 才稳定落盘)。
- **前端终端**:浏览器 ComfyUI 界面底部终端(经 WebSocket 推送的环形缓冲)也能实时看到同样的日志,排查前端扩展报错可直接看它。
- **注意**:`logs\comfyui*.log` 是用户自建重定向(如启动脚本),**不是官方位置**,可能缺部分输出;查不到关键日志时先看 `user\comfyui_<port>.log`。

## 模型与蓝图(2026-10-11 现状)

模型实际存放在 `models\` 下(`ComfyUI\models` 为软链接),当前合计约 **263.5 GB**。已就绪:

| 目录 | 已就绪 |
|------|--------|
| diffusion_models | `qwen_image_2512_fp8_e4m3fn`、`qwen_image_fp8_e4m3fn`、`qwen_image_edit_2511_fp8mixed`、`qwen_image_2.1_bf16`(2.1 基座)、`flux-2-klein-9b-fp8`、`triposplat_fp16`、`minimax_h3_fl2va_pruned_int8_convrot`、`minimax_h3_ref2va_pruned_int8_convrot` |
| text_encoders | `qwen_2.5_vl_7b_fp8_scaled`(Qwen-Edit)、`qwen3vl_8b_bf16`(Qwen-Image 2.1)、`qwen_3_8b_fp8mixed`(Klein)、`qwen3.5_2b_bf16`(音频)、`t5gemma_b_b_ul2`(音频)、`qwen3vl_32b_minimax_h3_nvfp4_awq` + `qwen3vl_32b_minimax_h3_int8_convrot`(H3 视频,两档量化并存) |
| vae | `qwen_image_vae`、`qwen_image_2.1_vae_bf16`(2.1,64 通道 RGBA)、`full_encoder_small_decoder`(Klein/FLUX.2)、`flux2-vae`、`triposplat_vae_decoder_fp16`、`minimax_h3_video_vae_fp16` + `minimax_h3_video_vae_int8_convrot`(H3 视频,两档)+ `minimax_h3_audio_vae_fp32` |
| loras | `Qwen-Image-2512-Lightning-4steps-V1.0-fp32`、`Qwen-Image-Lightning-4steps-V1.0`、`Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16`、`qwen-image-edit-2511-multiple-angles-lora`(多视角,配 `ComfyUI-qwenmultiangle` 插件)、`[Qwen-Edit]3DChineseStyle_25`、`Kook_Qwen_2512_真实幻想`、H3 加速**五件**:`minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16` / `minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16` / `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16` / `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16` / `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16` |
| checkpoints | `stable_audio_3_medium.safetensors`(音频,8.59 GB) |
| upscale_models | `4xNomos8kDAT`(原 `4x-UltraSharp.pth`、`RealESRGAN_x4plus.pth` 已移除) |
| background_removal | `birefnet.safetensors` |
| controlnet | `Qwen-Image-InstantX-ControlNet-Inpainting`(InstantX Inpainting,扩图/局部重绘用) |
| facerestore_models | `GFPGANv1.4`、`GFPGANv1.3`、`codeformer-v0.1.0`、`GPEN-BFR-512`(人脸修复,Impact-Pack/ReActor 自动下载) |
| embeddings | `minimaxh3_*` 十个 H3 动作嵌入(`art_is_explosion`/`blooming_flowers`/`bullet_time`/`dark_magic`/`fire_breath`/`four_seasons`/`kiss_camera`/`spiral_ascent`/`storm_magic`/`truman_show`) |
| model_patches | `minimax_h3_fun_controlnet_union_pruned_int8_convrot`(H3 fun-controlnet) |
| latent_upscale_models | `minimax_h3_latent_upscaler_3d_fp16`(配 `h3-latent-upscaler` 插件) |
| geometry_estimation | `depth_anything_3_base` / `depth_anything_3_mono_large` / `depth_anything_3_small` |
| clip_vision | `dino_v3_vit_h.safetensors` |
| vae_approx | `taeh3.safetensors`(H3 预览用近似 VAE) |
| hywm2 | `model.safetensors` + `config.json`(HY-World 2.0 世界重建权重,3.05 GB) |
| configs | SD1.x/SD2.x 标准推理配置 11 个 yaml(上游自带) |
| TTS | `TTS\Qwen\` 下 Qwen3-TTS-12Hz 五变体(0.6B-Base / 0.6B-CustomVoice / 1.7B-Base / 1.7B-CustomVoice / 1.7B-VoiceDesign,各含主模型 + speech_tokenizer);`TTS\SenseVoiceSmall`(ASR,`model.pt` 936 MB) |

路线:Qwen-Image(国漫/中文更优)+ MiniMax H3(视频)+ FLUX.2-Klein(图像)。**已就绪的 `triposplat_fp16` / `triposplat_vae_decoder_fp16` 与 `flux2-vae` 属历史遗留,当前工作流未使用**;曾清理 FLUX.2 全套、旧版 qwen_image、LTX-2.3/Wan 2.2 等,后续按需重新引入(以表格为准)。`ComfyUI\blueprints\` 内置 116 个蓝图(位于 ComfyUI 目录内;除 Qwen 2511 外均缺模型)。

## 网络与代理

- 默认直连外网;直连失败(超时/403/TLS 被掐)时改用本机代理 `127.0.0.1:7890`(Clash Verge 混合端口,HTTP 与 SOCKS5 均可):
  - HTTP 代理:`http://127.0.0.1:7890`(curl `-x http://127.0.0.1:7890`、`HTTPS_PROXY`/`HTTP_PROXY` 环境变量)
  - SOCKS5:`socks5h://127.0.0.1:7890`(curl `-x socks5h://127.0.0.1:7890`)
- 注意:OpenAI 系域名等会被 Cloudflare/SNI 拦截,需走专用节点;huggingface 下载失败时优先直连、再带代理(国内可用 `hf-mirror.com` 镜像)
