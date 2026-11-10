# 本工作区的运行环境、模型与网络

> 本文承载本机(`D:\AI\Comfy-S`)的依赖约束、模型清单与网络策略;版本一律现场查询(见下),本文不固化。与本技能根目录的 `machine.md` 互补:`machine.md` 是 kit 采集的机器事实快照,本文是项目维护的依赖/模型/代理口径。

## 版本与运行

- **Python 虚拟环境:项目内 `.venv`**(2026-08-16 由 conda 环境迁移而来,官方 `python -m venv` 基于系统 Python 创建;原 conda 专用环境已删除)。启动一律用 `.venv\Scripts\python.exe`(类 Unix 为 `.venv\bin/python`),不要用系统级 Python 或任何 conda 环境运行主程序
- **运行环境 `.venv`(RTX 4060 8GB VRAM)**,启动脚本与本文档均用它(`.venv\Scripts\python.exe`,类 Unix 为 `.venv\bin/python`);依赖安装顺序:torch(cu130 index)→ `ComfyUI\requirements.txt` → 插件 requirements → 加速依赖
- **依赖版本一律现场查询,本文件不记版本号**(硬编码会随升级立即过期,并已实际误导过判断):核心版本 `git -C ComfyUI describe --tags`,前端包 `pip show comfyui-frontend-package`,模板包 `pip show comfyui-workflow-templates`,全部依赖 `pip freeze`;运行中的口径以 `GET /system_stats` 为准
- **跨插件约束(装/升级前必查,与具体版本号无关)**:`numpy` 被 opencv 系列声明 `numpy<2.3` 卡住(ComfyUI-LNL 声明 `opencv-python~=4.12.0`),勿升到 2.5.x;`triton` 在 Windows 上以 `triton-windows` 包分发,`importlib.metadata.version("triton")` 会报 PackageNotFoundError,须以 `triton_windows-*.dist-info` 为准;`sageattention` 需 cu130 版 wheel,本地不留档,装前确认来源
- **核心升级流程**:`git -C ComfyUI fetch --tags` → 查最新 tag → `git checkout <tag>`(detached;工作树里被删的上游占位文件不受影响,不会冲突) → 按 `requirements.txt` 差异补装依赖 → 重启 → `custom_nodes\ComfyUI-FallingTS\dev\_check-workflow-node-compat.py` 验证工作流用到的节点类型全部仍注册 → 根仓库提交子模块指针。升级前先 `pip freeze` 备份到 `backups\`
- **升级兼容性判据**:前端内置节点(`Note`/`MarkdownNote`/`Reroute`/`PrimitiveNode`)与前端注册的 UUID 型 API 节点**不出现**在后端 `/object_info` 里,比对时须白名单排除(脚本已内置),否则每次升级都会误报缺失
- **插件更新流程**(2026-11-10 实践,45 个插件仓库):逐个 `git -C custom_nodes/<插件> fetch --tags --prune` → 用 `git rev-parse --abbrev-ref HEAD` 判形态 → 看落后数 `git rev-list --count HEAD..origin/<默认分支>`(默认分支取 `git symbolic-ref refs/remotes/origin/HEAD`,没有则按常见分支名探测)→ 在分支上的 `git checkout -B <分支> origin/<分支>`,**detached HEAD 的**同样 `git checkout -B <默认分支> origin/<默认分支>`(自动建跟踪分支)` → `git diff <旧> <新> -- requirements.txt` 判断是否补装依赖 → 含 `.gitmodules` 的插件(`ComfyUI-Easy-Use`/`ComfyUI-Impact-Pack`/`ComfyUI_UltimateSDUpscale`)再 `git submodule update --init --recursive` → 重启 → 跑 `_check-workflow-node-compat.py`。⚠️ **只更新本地,不推送**(上游子项目禁止提交/推送);更新前先确认各插件 `Ahead=0`,否则会覆盖本地提交
- ⚠️ **注意残留的 `_upd_` 分支**:旧更新流程会留下名为 `_upd_` 的本地分支,此时 `behind/ahead` 计算会因 `origin/_upd_` 不存在而报 `fatal: ambiguous argument`。先用 `git rev-list --count HEAD..origin/<默认分支>` 确认内容已同步(`behind=0`),再 `git checkout -B <默认分支> origin/<默认分支>` 归位并 `git branch -D _upd_`(2026-11-10 实测 6 个插件处于此状态)
- ⚠️ **`pip install --dry-run` 不够**:它只证明依赖可解析,不证明已装。插件声明不全是常态(见上文),**必须重启后扫日志** `No module named` / `IMPORT FAILED` 才能发现真缺的包
- ⚠️ **某个插件能拖死整个 `/object_info`**:`ComfyUI-ReActor` 曾在 `INPUT_TYPES()` 里同步 `urllib` 下载人脸修复模型,机器不通外网时会阻塞到超时,导致节点兼容性检查脚本 120s 超时、整个 `/object_info` 拉不出来。**排查特征**:`/system_stats` 正常但 `/object_info` 超时,日志里有插件栈帧。此类插件已于 2026-11-10 移除
- **模板库更新**:从**运行中的服务**拉 `GET /templates/index.zh.json`(官方核心,按中文 `title` 归入 `templates\<分类>\`)+ `GET /api/workflow_templates`(插件模板 → `自定义节点\<插件>\`),增量写入并重建 `workflow-templates-list.md`;版本号由 `/system_stats` 与 pip 包**动态读取**(勿再硬编码)。拉取逻辑用一次性脚本经 stdin 就地执行(不落盘);**不删除**已下线文件,只在末尾列出供人工判断(2026-09-21 遇到 `图像工具/api_flux_vto.json` 已从索引移除,备份到 `backups\` 后删除)
- **pip 默认走清华镜像**(`pypi.tuna.tsinghua.edu.cn`,配置在 `%APPDATA%\pip\pip.ini`):上游刚发布的包镜像可能尚未同步(实测 `comfyui-workflow-templates-media-assets-02==0.1.3` 上传 19 小时后仍查不到,报 `No matching distribution found`;2026-11-10 升级 v0.44.2 时 `media-assets-02==0.1.29` 同样在镜像上完全不可见),此时临时加 `--index-url https://pypi.org/simple` 走官方源直连即可。**注意整批安装会因单个包卡住而全盘失败**:先单独装镜像缺失的那个包,再装主包
- ⚠️ **装包前必须先停 ComfyUI**:运行中的服务持有 `site-packages` 里的 `.pyd`(实测 `onnx\onnx_cpp2py_export.pyd`),pip 会以 `[WinError 5] 拒绝访问` 中断在半路,留下半装状态
- ⚠️ **pip 在 Windows 可能残留 `~*` 临时目录**(如 `~-mfy_kitchen`、`~~mfy_aimdo`、`google\~upb`),装完顺手清理 `.venv\Lib\site-packages` 下的 `~*` 目录
- **插件依赖声明可能不全**:`audio-separation-nodes-comfyui` 的 `requirements.txt` 不声明 `audio_separator`,但节点运行时会 import;`TTS-Audio-Suite` 把 `torchcrepe`/`faiss-cpu` **注释掉**并要求 `--no-deps` 安装(避与 librosa 冲突)。**判据是用 `pip install --dry-run` 逐插件验证只证明「可解析」,不证明「已安装」** —— 真正可靠的是重启后扫日志里的 `No module named` / `IMPORT FAILED`,再按需补装
- 前端打包目录 = `<venv>/Lib/site-packages/comfyui_frontend_package/static/`:主入口 `index.html`,打包产物 `assets\`;插件 `web\js` 经 `GET /extensions` 运行时加载、**不参与前端打包**(重建 `assets\` 不影响扩展;前端包 `static\scripts\` 保留 `app.js`/`api.js` 等扩展 import 入口)
- 测试插件「从零安装」:清理浏览器缓存的 `assets\` 打包文件后,对 `http://127.0.0.1:8188` 强刷(`Ctrl+Shift+R`)再验证;**磁盘 `assets\` 勿删**(删了页面白屏)
- 启动:

先激活虚拟环境(`.venv\Scripts\activate` 或 `.venv/bin/activate`),再:

```text
cd ComfyUI
python main.py --enable-manager
```

- 或直接 `.venv\Scripts\python.exe main.py --enable-manager`(在 `ComfyUI` 下;类 Unix 用 `.venv/bin/python`);或运行 `bash comfy-server.sh`(统一跨平台后台服务式,Windows Git Bash / Linux 均可:停旧服务 → 后台启动 → 等端口;可覆盖 `PORT`/`WAIT`/`PY_BIN`/`LOG`/`RESERVE_VRAM`)
- ⚠️ **Windows 上不要加 `--disable-pinned-memory`**:关掉后 `get_pin` 恒为 `None`、`handle_pin` 走另一条分支,会让 Qwen Image 2.1 采样崩在 `Overlapped I/O 1450`(2026-11-06 由提交 `eb43108` 修复,`comfy-server.sh` 的 Windows 分支因此只传 `--enable-manager --port`)。Linux 分支仍用 `--fast-disk --reserve-vram 22`(conda 环境 comfy)
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

## 模型与蓝图(2026-11-10 实测)

模型实际存放在 `models\` 下(`ComfyUI\models` 为软链接),当前合计 **243.01 GB / 53 个模型文件 / 仅 10 个目录有内容**(42 个顶层槽位里其余为空占位)。⚠️ 空槽位清单见本节末,别再按旧表找已不在盘上的模型。已就绪:

| 目录 | 已就绪 |
|------|--------|
| diffusion_models | 6 个 / 110.49 GB:`qwen_image_2512_fp8_e4m3fn`、`qwen_image_edit_2511_fp8mixed`、`qwen_image_2.1_bf16`(2.1 基座)、`minimax_h3_fl2va_pruned_int8_convrot`、`minimax_h3_hybrid_fl2va_ref2va_b25-49-int8`、`ltx-2.5-22b-distilled-transformer-comfy-int8-convrot` |
| text_encoders | 6 个 / 80.38 GB:`qwen_2.5_vl_7b_fp8_scaled`(Qwen-Edit)、`qwen3vl_8b_bf16`(Qwen-Image 2.1)、`t5gemma_b_b_ul2`(Stable Audio 3)、`qwen3vl_32b_minimax_h3_nvfp4_awq` + `qwen3vl_32b_minimax_h3_int8_convrot`(H3 视频,两档量化并存)、`gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot`(LTX-2.5) |
| vae | 5 个 / 5.75 GB:`qwen_image_vae`、`qwen_image_2.1_vae_bf16`(2.1,64 通道 RGBA)、`minimax_h3_video_vae_int8_convrot` + `minimax_h3_audio_vae_fp32`、`ltx-2.5-video-vae-bf16` |
| loras | 9 个 / 11.37 GB:`Qwen-Image-2512-Lightning-4steps-V1.0-fp32`、`Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16`、`qwen-image-edit-2511-multiple-angles-lora`(多视角,配 `ComfyUI-qwenmultiangle`)、`Kook_Qwen_2512_真实幻想`、`ltx-2.5-22b-ic-lora-ingredients-0.9`(LTX-2.5)、H3 加速**四件**:`minimax_h3_fl2v_turbo_4step_v1.2_768p` / `minimax_h3_fl2v_turbo_8step_v1.0` / `minimax_h3_ref2v_turbo_4step_v0.1` / `minimax_h3_ref2v_turbo_8step_v1.0_768p`(均 `comfyui_bf16`) |
| checkpoints | 2 个 / 11.45 GB:`ace_step_1.5_turbo_aio`(ACE-Step 音乐)、`stable_audio_3_small_sfx`(音效) |
| foley | 3 个 / 11.86 GB:`hunyuanvideo_foley` + `vae_128d_48k_fp16` + `synchformer_state_dict_fp16`(HunyuanVideo-Foley 视频配音) |
| embeddings | 10 个 / 0.01 GB:`minimaxh3_*` 十个 H3 动作嵌入(`art_is_explosion`/`blooming_flowers`/`bullet_time`/`dark_magic`/`fire_breath`/`four_seasons`/`kiss_camera`/`spiral_ascent`/`storm_magic`/`truman_show`) |
| latent_upscale_models | 1 个 / 0.93 GB:`ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0`(LTX-2.5) |
| hywm2 | 1 个 / 3.05 GB:`model.safetensors` + `config.json`(HY-World 2.0 = WorldMirror 2.0 世界重建权重,配 `ComfyUI-HYWM2`) |
| configs | SD1.x/SD2.x 标准推理配置 11 个 yaml(上游自带) |
| TTS | 10 个 / 7.71 GB:`IndexTTS-2.5`(`gpt.pth` 3.04 GB + `s2mel.pth` + `codec.pth` + `qwen0.6bemo4-merge`)、`w2v-bert-2.0`(2.16 GB)、`bigvgan_v2_22khz_80band_256x`、`campplus`。⚠️ 人声合成(`0063`/`0064`)走 `TTS-Audio-Suite` 的 **IndexTTS-2.5 + Qwen0.6B-emo** 引擎;`CosyVoice`/`dramabox`/`higgs_audio_v3` 为空槽。旧文档所述「SenseVoiceSmall / Qwen3-TTS-12Hz 五变体」已不在盘上 |

⚠️ **空槽位(共 32 个,找模型时别白找)**:`upscale_models`、`controlnet`、`clip_vision`、`model_patches`、`vae_approx`、`geometry_estimation`、`background_removal`、`facerestore_models`、`audio_encoders`、`ASR`、`clip`、`classifiers`、`detection`、`diffusers`、`frame_interpolation`、`gligen`、`hypernetworks`、`LLM`、`mesh2motion`、`nlf`、`optical_flow`、`photomaker`、`reactor`、`SEEDVR2`、`speaker_models`、`style_models`、`ultralytics`、`unet`、`yolo`、`.cache`、`HF-cache`、`configs`(仅配置无权重)。**旧表里的 `4xNomos8kDAT`、`birefnet`、`Qwen-Image-InstantX-ControlNet-Inpainting`、`dino_v3_vit_h`、`taeh3`、`depth_anything_3_*`、`minimax_h3_latent_upscaler_3d_fp16`、`minimax_h3_fun_controlnet_union_pruned` 均已不在盘上**

路线:Qwen-Image(国漫/中文更优)+ MiniMax H3(视频主链)+ LTX-2.5(视频,新接入)+ Stable Audio / ACE-Step / HunyuanVideo-Foley(音频)。**FLUX.2 全套已于 2026-11-01 删除**(`flux-2-klein-9b-fp8` / `qwen_3_8b_fp8mixed` / `flux2-vae` / `full_encoder_small_decoder`,共 17.4 GB);`ComfyUI\blueprints\` 内置 116 个蓝图(位于 ComfyUI 目录内;除 Qwen 2511 外均缺模型)。

## 网络与代理

- 默认直连外网;直连失败(超时/403/TLS 被掐)时改用本机代理 `127.0.0.1:7890`(Clash Verge 混合端口,HTTP 与 SOCKS5 均可):
  - HTTP 代理:`http://127.0.0.1:7890`(curl `-x http://127.0.0.1:7890`、`HTTPS_PROXY`/`HTTP_PROXY` 环境变量)
  - SOCKS5:`socks5h://127.0.0.1:7890`(curl `-x socks5h://127.0.0.1:7890`)
- 注意:OpenAI 系域名等会被 Cloudflare/SNI 拦截,需走专用节点;huggingface 下载失败时优先直连、再带代理(国内可用 `hf-mirror.com` 镜像)
