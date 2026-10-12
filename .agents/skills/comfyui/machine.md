# Your machine

**This file is yours, not the kit's.** It holds the facts about THIS install: where ComfyUI lives, what GPUs
are in the box, how to start the server when it is down. The installer creates it once and then never touches
it again, so a `git pull` plus a reinstall cannot wipe what the bootstrap learned. Nothing here ships back to
the repo.

> 本文件事实于 **2026-09-30** 重新采集:环境与版本取自运行中的 `/system_stats`,模型清单取自 `/object_info`,计数为盘上实测。
> 项目根于 2026-09-30 由 `D:\Comfy` 搬到 `D:\AI\Comfy`,又于 2026-10-12 由 `D:\AI\Comfy` 改名为 **`D:\AI\Comfy-S`**(整体搬家,8 条相对软链不受影响)。若服务重启后数值变化,以实时查询为准。

- **ComfyUI**: source install,core path **`D:\AI\Comfy-S\ComfyUI`**,API at **`http://127.0.0.1:8188`**(运行中,ComfyUI **0.37.0** / 前端 **1.52.7** / Python **3.13.13**)。运行环境是**项目内 `.venv`**(2026-08-16 由 conda 环境迁移而来;旧的 conda 专用环境已删除)。Check: `GET /system_stats` -> 200。
- **GPUs**: 1x `cuda:0` NVIDIA GeForce RTX 4060,VRAM **8.0 GB**(运行中 free 约 6.9 GB)。
- **Models installed**(2026-09-30 实测 `/object_info`,名称省略 `.safetensors`):
  - UNETLoader (**8**): `qwen_image_2.1_bf16`(2.1 基座)、`qwen_image_2512_fp8_e4m3fn`、`qwen_image_edit_2511_fp8mixed`、`qwen_image_fp8_e4m3fn`、`flux-2-klein-9b-fp8`、`minimax_h3_fl2va_pruned_int8_convrot`、`minimax_h3_ref2va_pruned_int8_convrot`、`triposplat_fp16`
  - CheckpointLoaderSimple (**1**): `stable_audio_3_medium.safetensors`(音频)
  - CLIPLoader (**6**): `qwen_2.5_vl_7b_fp8_scaled`(Qwen-Image-Edit 用)、`qwen3vl_8b_bf16`(Qwen-Image 2.1)、`qwen3vl_32b_minimax_h3_nvfp4_awq`(H3 视频)、`qwen_3_8b_fp8mixed`(Klein)、`qwen3.5_2b_bf16` 与 `t5gemma_b_b_ul2`(音频)
  - VAELoader (**10**): `qwen_image_vae`、`qwen_image_2.1_vae_bf16`(64 通道 RGBA)、`flux2-vae`、`full_encoder_small_decoder`(Klein/FLUX.2)、`minimax_h3_video_vae_fp16`、`minimax_h3_video_vae_int8_convrot`、`minimax_h3_audio_vae_fp32`、`taeh3`、`triposplat_vae_decoder_fp16`、`pixel_space`
  - LoraLoaderModelOnly (**11**): `Qwen-Image-2512-Lightning-4steps-V1.0-fp32`、`Qwen-Image-Lightning-4steps-V1.0`、`Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16`、`qwen-image-edit-2511-multiple-angles-lora`、`[Qwen-Edit]3DChineseStyle_25`、`Kook_Qwen_2512_真实幻想`,加 H3 加速五件:`minimax_h3_fl2v_turbo_4step_v1.0_768p` / `minimax_h3_fl2v_turbo_4step_v1.2_768p` / `minimax_h3_fl2v_turbo_8step_v1.0` / `minimax_h3_ref2v_turbo_4step_v0.1` / `minimax_h3_ref2v_turbo_8step_v1.0_768p`
- **Shared models dir / extra_model_paths**: 无 extra_model_paths.yaml;模型实际存放 **`D:\AI\Comfy-S\models`**(`ComfyUI\models` 是其相对软链接),input/output 同样软链到 `D:\AI\Comfy-S\media\七纹刻印`(media 按项目分目录,当前项目 = 七纹刻印)。
- **GUI workflows folder**(bridge 回前端): `D:\AI\Comfy-S\ComfyUI\user\default\workflows\`(该路径是软链接,实际存储 **`D:\AI\Comfy-S\workflows`**,29 个工作流)。可写。
- **Template library**: **`D:\AI\Comfy-S\templates`**(模板包 `comfyui-workflow-templates` 0.11.66,递归 **790** 个 json,按 13 个分类分目录)+ `D:\AI\Comfy-S\ComfyUI\blueprints`(顶层 **116** 个蓝图 json)。⚠️ 本机**没有** kit 默认的 `~/comfyui-agent-kit-data/workflow_templates` 与 `_quick_index.json`;`TASKS.md` 若按该路径找模板索引会落空,直接用上面本地目录。
- **Launch command**(服务未运行、:8188 关闭时): `cd /d D:\AI\Comfy-S\ComfyUI && D:\AI\Comfy-S\.venv\Scripts\python.exe main.py --enable-manager --disable-pinned-memory --fast-disk`(当前进程 argv 实测即 `main.py --enable-manager --disable-pinned-memory --fast-disk --port 8188`)。也可在项目根跑 `bash comfy-server.sh`(跨平台后台服务式:停旧服务 → 后台启动 → 等端口)。**勿用系统 Python 或 conda 环境运行**(`.venv\Scripts\python.exe`)。若 :8188 已被占用,勿重复启动。
- **Known local quirks**(本机与 docs 不符之处,省时的关键):
  - **知识独立安装,无 MCP 驱动层**:未安装 `comfyui-mcp`(npm 全局实测无),SKILL.md 里 `health_check / get_node_info / list_installed_nodes` 等 MCP 工具**不存在**。与 API 通信一律用本目录 `comfy_client.py`(stdlib)直连 :8188,或直接 HTTP。
  - **8GB 小显存**:图像/视频优先 fp8/int8 量化 + Lightning 4 步 LoRA + SageAttention;主文生图链路默认 `--fast-disk --disable-pinned-memory`。
  - **sibling skills 未装**:SKILL.md 提及的 `minimax-h3` / `krea` / `seedance` 不在本机;H3 提示词由本机已有 `h3-prompt-writing` skill 承担,遇到 krea/seedance 模型直接说明未安装。
  - **Qwen-Image-Edit 条件节点**:`TextEncodeQwenImageEditPlus`(三参考图 image1/2/3,提示词内用 `图N` / `Picture N` 编号引用,VAE 参考 latent 写入 `reference_latents`);单图用 `TextEncodeQwenImageEdit`。规范详见 `docs\Qwen-Image-Edit-三参考图提示词规范与可用Skills-2026-08-11.md`。⚠️ Qwen-Image **2.1** 用 `TextEncodeQwenImage21`(一个节点同时出 positive/negative),架构与 2511/2512 不兼容。
  - **自定义插件聚合**:`D:\AI\Comfy-S\custom_nodes`(目录级软链接加载,**46 个可加载插件** = 45 个 git 子模块 + `H3ReferenceSuite` 软链,含 FallingTS / KJNodes / LayerStyle / Impact-Pack / Easy-Use / SeedVR2 / SUPIR / UltimateSDUpscale / HYWM2 / OrbitSheets / MiniMaxH3 套件 / LinkFX / AnimatedLinks / rgthree / controlnet_aux / VideoHelperSuite / Florence2 / IPAdapter_plus / WanVideoWrapper / LNL 等),改节点代码需重启 ComfyUI 生效。历史上 2026-08-12 按下载量批量装入 25 个;`nunchaku` 因 RTX 4060 不支持已删除,`ReActor`/`RMBG`/`SAM2` 等首次运行时会自下模型。
