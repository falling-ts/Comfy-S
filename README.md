# Comfy — AI-driven ComfyUI all-modal workspace

> This repository is a **ready-to-use ComfyUI all-modal workspace**: the ComfyUI main program, MiniMax H3 video + Qwen-series image + Stable Audio/Qwen3-TTS audio generation, 44 custom node packs (GGUF/KJNodes/upscaling/speedup, etc.), 34 image/video/audio workflows, and a model catalog plan.
>
> **Core idea: all installing, configuring, running, generating, and workflow training is delegated to the AI (OpenCode).** You only need to: install Git → clone this repository → install OpenCode → let it work.

---

## Table of Contents

- [What is this](#what-is-this)
- [Before you start](#before-you-start)
- [Step 1: Install Git](#step-1-install-git)
- [Step 2: Clone this project](#step-2-clone-this-project)
- [Step 3: Install OpenCode (Desktop)](#step-3-install-opencode-desktop)
- [Step 4: Run OpenCode as administrator and set up the symlinks](#step-4-run-opencode-as-administrator-and-set-up-the-symlinks)
- [Step 5: Have OpenCode install its own CLI (optional)](#step-5-have-opencode-install-its-own-cli-optional)
- [Step 6: Have OpenCode install other AI tools (optional)](#step-6-have-opencode-install-other-ai-tools-optional)
- [Step 7: Have OpenCode set up the Python environment](#step-7-have-opencode-set-up-the-python-environment)
- [Step 8: Have OpenCode install ComfyUI dependencies and start it](#step-8-have-opencode-install-comfyui-dependencies-and-start-it)
- [Step 9: From here on, everything is the AI's job](#step-9-from-here-on-everything-is-the-ais-job)
- [FAQ](#faq)
- [Appendices](#appendices)

---

## What is this

- **ComfyUI main program** (`ComfyUI\` submodule, detached HEAD following upstream release tags, currently v0.39.2) — a local node-based AI image/video/audio generation engine
- **Custom nodes** (44, centralized in the root `custom_nodes\`, loaded via a **directory-level** symlink at `ComfyUI\custom_nodes\`; the full list is in `AGENTS.md`):
  - `ComfyUI-FallingTS` — our own general-purpose utility node pack (22 nodes: Continue/Route/Fanout/Selector/Table/Switch/MarkDownTable/FrameRateConvert/ImageComposite/LoadImage/LoadVideo/LoadAudio/VideoComponents/H3AddGuide + the 3 world-model nodes WorldSurroundPanorama/WorldPanoramaViews/WorldRefinePLY, plus PreviewVideo/PreviewImageSave/AutoSaveImage/PreviewAudioSave/AudioTrim and 27 frontend enhancements)
  - `ComfyUI-GGUF` / `ComfyUI-KJNodes` — GGUF quantized loading / large utility node pack
  - `ComfyUI-SeedVR2_VideoUpscaler` / `ComfyUI-SUPIR` / `ComfyUI_UltimateSDUpscale` — super-resolution upscaling/restoration
  - The 5 H3-ecosystem plugins (Spectrum / SolAttn / ReservedVRAM / Qwen3-TTS / latent-upscaler) + the other 39
- **Workflow suite**: 34, grouped by number (001x Everything / 002x Scene camera / 003x Scene generation + world model / 004x Video generation / 005x Decomposition / 006x Audio generation / 007x Audio extraction; see [Appendix B](#appendix-b--workflow-catalog))
- **Model directory** (`models\`, symlinked to the project root) — see [Appendix C](#appendix-c--model-download-list)
- **Docs**: a local clone of the official docs at `refs\ComfyUI-Docs\`; the workspace description in `AGENTS.md`

---

## Before you start

- **System**: Windows 10/11 or Linux (this repo is written for Windows deployment by default; see "Appendix H: Migrating to Linux" for Linux/macOS deployment)
- **Hardware**: 16 GB+ RAM; an **NVIDIA GPU** gives the best experience; it runs without an NVIDIA card, but slowly
- **Network**: just needs external internet access; some regions need a proxy; for model downloads inside China use the `hf-mirror.com` mirror (see Appendix E)
- **You don't need to install anything in advance** — Python, CUDA, the virtualenv, and all the CLIs are installed by the AI for you

---

## Step 1: Install Git

Git is used to clone this repository and manage the submodules. Download the installer from **https://git-scm.com/download/win** (64-bit, click "Next" through the default options); after installing, run `git --version` in a terminal — if it prints a version number, you're good.

---

## Step 2: Clone this project

Run in Git Bash:

```bash
git clone https://github.com/falling-ts/Comfy
cd Comfy
```

When done you have a complete workspace containing `ComfyUI\`, the various `ComfyUI-*\` plugins, `workflows\`, `models\`. **All subsequent work happens inside this `Comfy` directory.**

> Note: after cloning, `models\` is empty (models are too large to ship with the repo) — download them per [Appendix C](#appendix-c--model-download-list); `media\` is empty too; it's home for input/output files.

---

## Step 3: Install OpenCode (Desktop)

OpenCode is the AI workhorse between you and this workspace — it installs software, configures the environment, and runs workflows.

1. Open **https://opencode.ai/zh/download** in a browser and download the **Desktop** edition
2. Install and launch OpenCode
3. In the left panel, **Add project**, and select the `Comfy` directory you just cloned
4. After that, just talk to the AI inside this project

---

## Step 4: Run OpenCode as administrator and set up the symlinks

> ⚠️ **Important**: this workspace relies on **relative-path symbolic links** pointing the relevant directories inside `ComfyUI\` at the project root (`models\`, `media\`, `workflows\`, the plugin directories). **Creating symlinks requires administrator privileges, so run OpenCode as administrator.**

1. Find OpenCode in the Start menu, right-click → **Run as administrator**
2. Open this project (add the `Comfy` directory) and send it the following:

> Please check and repair this project's symlinks per the "symlink plan" below (all **relative-path** symlinks, 8 total; the full list is in `AGENTS.md` "Symlink map"):
>
> 1. **Directory-level plugin link**: make sure `ComfyUI\custom_nodes` is a symlink pointing to `..\custom_nodes` (the root plugin aggregation directory; all 45 plugins are loaded through this single link; **not** the old one-link-per-plugin scheme);
> 2. **Base links**: `ComfyUI\input` → `..\media\七纹刻印`, `ComfyUI\output` → `..\media\七纹刻印`, `ComfyUI\models` → `..\models`, `ComfyUI\user\default\workflows` → `..\..\..\workflows`;
> 3. **Sub-links**: `custom_nodes\H3ReferenceSuite` → `..\refs\minimax-h3-guide\custom_nodes\H3ReferenceSuite`; `.claude` → `.agents`; `stories\.obsidian\plugins` → `..\plugins`;
> 4. Once everything is done, confirm these paths show as "symbolic links" and verify subdirectories like `ComfyUI\models\diffusion_models` can be entered normally.
>
> Note: only replace real directories; keep real directories like `ComfyUI\temp\`; all links use relative paths so they survive moving the whole project folder.

3. With the symlinks ready, continue to [Step 5](#step-5-have-opencode-install-its-own-cli-optional).

---

## Step 5: Have OpenCode install its own CLI (optional)

If you like the command line, say "install the opencode CLI for me — search the web for the specific download/install"; once installed, `cd Comfy && opencode` and go.

---

## Step 6: Have OpenCode install other AI tools (optional)

When needed, say "install the following AI tools for me: codex, claude code, cc-switch — search the web for the specific download/install"; you get a swappable AI CLI suite.

---

## Step 7: Have OpenCode set up the Python environment

Send this to OpenCode (to create a `.venv` virtualenv at the project root):

> Create a Python 3.13 virtualenv `.venv` in the project root (if the system has no Python 3.13, install the official Python 3.13 first). Search the web for the specific download/install.
>
> Note: the environment must live at the project root `.venv` (not the system Python); all subsequent dependencies go into this environment — don't use system Python.

Once done, verify (it will run in the terminal):

```powershell
.\.venv\Scripts\activate   # on Unix-like systems: source .venv/bin/activate
python --version
```

---

## Step 8: Have OpenCode install ComfyUI dependencies and start it

Send this to OpenCode (it will, in order: install the CUDA build of PyTorch → install the main dependencies → install each plugin's dependencies → start):

> Enter the `ComfyUI` directory and, in order:
>
> 1. **First install the CUDA build of PyTorch**: run
>    `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130`
>    (first detect which CUDA version my NVIDIA GPU/driver supports and pick the matching `cuXXX`; if there's no NVIDIA card, install the CPU build)
> 2. Then install the rest: `pip install -r requirements.txt`
> 3. Then go into every plugin directory under `custom_nodes\` (45 of them, see the directory layout in `AGENTS.md`), check each one's required dependencies (its `requirements.txt` or README) and install them all.
> 4. Finally, back in `ComfyUI`, start it: `python main.py --enable-manager`
>
> Once it starts successfully, tell me the frontend address.

After startup, open **http://127.0.0.1:8188** in a browser — that's the ComfyUI frontend.

---

## Step 9: From here on, everything is the AI's job

Once the environment is ready, you can have the AI do everything:

- Download models (per [Appendix C](#appendix-c--model-download-list); just say "download model xx into models\yyy\")
- Run / modify / create workflows (in `workflows\`)
- Install new custom nodes, debug, tune parameters, generate images, train
- Video/audio/image generation (MiniMax H3, Stable Audio, Qwen series, etc.)

In one sentence: **you say "what you want"; the AI handles "how to do it".**

---

## FAQ

- **Proxy / slow downloads**: direct connection by default; on failure use a local proxy (e.g. Clash's `127.0.0.1:7890`); for HuggingFace models inside China use the `hf-mirror.com` mirror — just replace the `huggingface.co` prefix in the link with `hf-mirror.com` (see Appendix E)
- **Symlinks**: `ComfyUI\custom_nodes` (directory-level, aggregates 45 plugins), `models`/`input`/`output`/`workflows`, etc. — 8 relative-path symlinks in total. Creating links needs administrator privileges; the recommended way is to **run OpenCode as administrator** and have it repair them (see [Step 4](#step-4-run-opencode-as-administrator-and-set-up-the-symlinks)); or manually enable "Developer Mode" (Settings → Privacy & security → For developers → Developer mode on)
- **Not enough VRAM**: the Klein 9B distilled version is VRAM-hungry (a 24G card is tight at 1024 tiles; drop to 768 if OOM); MiniMax H3 needs a lot of VRAM — for low-VRAM cards use the quantized version or the cloud (see the Appendix C notes)
- **After placing models, remember to restart ComfyUI** so the loaders pick up the new models

---

# Appendices

## Appendix A · Project structure

```
Comfy/
├── ComfyUI/                  # ComfyUI main program (submodule, detached HEAD, currently v0.39.2)
│   ├── main.py               # startup entry (python main.py --enable-manager)
│   ├── custom_nodes/         # custom nodes (directory-level symlink → ../custom_nodes)
│   ├── input/  output/       # input/output (symlink → ../media/七纹刻印)
│   ├── user/default/workflows  # user workflows (symlink → ../../../workflows)
│   └── models/               # models (symlink → ../models)
├── custom_nodes/             # plugin aggregation directory: 44 plugin submodules + H3ReferenceSuite link
│   ├── ComfyUI-FallingTS/    # our own general-purpose utility node pack (22 nodes + world-model nodes + frontend enhancements)
│   ├── ComfyUI-GGUF/  ComfyUI-KJNodes/   # quantized loading / utility node pack
│   └── ...(the other 41, see the directory layout in AGENTS.md)
├── docs/                     # 44 categorized docs
├── refs/                     # 7 reference submodules (ComfyUI-Docs / Obsidian-Dev-Docs / Obsidian-API / Qwen-Image-2.1 / qwen-image-2.1-skill / MiniMax-H3 / minimax-h3-guide) + Qwen-Image-Edit-Skills (local dir, not a submodule)
├── workflows/                # 34 user workflows (001x~007x, see Appendix B)
├── models/                   # where models actually live (~263.5 GB, 40 top-level directories, see Appendix C)
├── media/                    # input images/audio + generated results (template/ + per-story project dirs, currently 七纹刻印/)
├── templates/  webs/         # official template cache + third-party research (RunningHub/Bilibili/AutoDL)
├── stories/                  # Obsidian story-writing workspace
├── backups/                  # pre-change backups of workflows/docs (local only)
└── AGENTS.md                 # workspace description (for AI to read; directory layout/symlinks/conventions all here)
```

### Symlinks (8 total, all relative paths)

`ComfyUI\input`/`output` → `media\七纹刻印`, `ComfyUI\models` → `models`, `ComfyUI\user\default\workflows` → `workflows`, `ComfyUI\custom_nodes` → `custom_nodes` (**directory-level, aggregates 45 plugins**), `custom_nodes\H3ReferenceSuite` → `refs\minimax-h3-guide\...`, `.claude` → `.agents`, `stories\.obsidian\plugins` → `stories\plugins`. All are **relative-path** symlinks — they survive moving the whole project; creating/repairing them needs administrator privileges; the full list is in `AGENTS.md` "Symlink map"; `ComfyUI\temp\` is a real directory (not a link) and can be cleaned up anytime.

## Appendix B · Workflow catalog

`workflows\` contains **35** main workflows, named "number-purpose" and grouped (the frontend saves right here):

### Image / "Everything" class (001x, 10; image side based on Qwen-Image-2512 / Qwen-Image 2.1 / Qwen-Edit 2511, 0013–0015 on MiniMax H3)

| Workflow | Purpose |
|--------|------|
| `0011_万物建模` | Main pipeline (everything modeling) |
| `0010_灰度遮罩` | Grayscale mask tool |
| `0012_万物变化` | Everything change/transform |
| `0013_首图建模` | H3 I2VA: first-image → video → frame extraction → character asset |
| `0014_参考建模` | H3 Ref2VA: reference-image modeling |
| `0015_建模截帧` | Modeling frame extraction |
| `0016_建模拆图` | Split a contact sheet into 2×2 / 3×3 tiles and auto-save each |
| `0017_建模细节` | Per-tile local detail refinement (Qwen-Image-Edit) |
| `00110_万物建模_QI2.1` | Qwen-Image 2.1 version of `0011` (**shares** `0011`'s data table) |
| `00120_万物变化_QI2.1` | Qwen-Image 2.1 version of `0012` (**shares** `0012`'s data table) |

### Scene camera class (002x, 6)

| Workflow | Purpose |
|--------|------|
| `0020_场景首帧` | Scene first-frame generation |
| `0021_场景拉镜` | Camera pull-out / push-in transform |
| `0022_场景推镜` | Camera push-in transform |
| `0023_场景旋镜` | Camera orbit rotation |
| `00200_场景首帧_QI2.1` | Qwen-Image 2.1 version of `0020` (**shares** `0020`'s data table) |
| `00220_场景推镜_QI2.1` | Qwen-Image 2.1 version of `0022` (**shares** `0022`'s data table) |

### Scene generation + world model class (003x, 6, MiniMax H3)

| Workflow | Purpose | H3 mode |
|--------|------|---------|
| `0030_文生场景` | text → scene video (visual only, no audio track) | T2VA (fl2va) |
| `0031_首帧场景` | first-frame image → scene video | I2V (fl2va) |
| `0032_参考场景` | multi-image + multi-video reference → video | R2V (ref2va) |
| `0034_世界模型` | 360° orbit video → panorama strip → view batch → one highest-quality 3DGS PLY | world model (self-owned nodes + HYWM2) |
| `0035_场景截帧` | load video → frame extraction → 8 single frames + 4-view/8-direction composites auto-saved | — |

### Video generation class (004x, 5, MiniMax H3)

| Workflow | Purpose | H3 mode |
|--------|------|---------|
| `0040_文生视频` | text → video (generic version isomorphic to 0030) | T2VA (fl2va) |
| `0041_首帧视频` | first-frame image → video | I2V (fl2va) |
| `0042_首尾视频` | first+last frame → video | fl2va |
| `0043_关键帧视频` | arbitrary keyframe anchoring via AddGuide | keyframe (fl2va) |
| `0044_参考视频` | reference image/video → video | R2V (ref2va) |

> 0030/0031/0032 correspond one-to-one with 0040/0041/0042/0044 (the former is the scene-pipeline version, the latter the generic version); the audio track has been removed from all — video + audio are merged in the post pipeline (005x-007x).

### Decomposition class (005x, 2)

| Workflow | Purpose |
|--------|------|
| `0050_视频截帧` | video → per-frame images |
| `0051_视频拆音` | video → separated audio |

### Audio generation class (006x, 5)

| Workflow | Purpose | Core model |
|--------|------|---------|
| `0060_背景音乐` | Pure instrumental BGM | Stable Audio 3 (built-in Sage acceleration) |
| `0061_环境音效` | Ambient/atmosphere sound | Stable Audio 3 |
| `0062_效果音效` | One-shot / SFX | Stable Audio 3 |
| `0063_文生人声` | text voice description → speech | Qwen3-TTS VoiceDesign |
| `0064_参考人声` | 3-second reference audio clone → speech | Qwen3-TTS CustomVoice |

### Audio extraction class (007x, 1)

| Workflow | Purpose |
|--------|------|
| `0070_截取声音` | Load an audio file, crop a segment on the waveform, preview/save three takes |

> The old image 8 / video 4 / audio 5 workflows that used to be archived under `templates\` before 2026-08-09 have been deleted; the current numbering scheme is canonical.

## Appendix C · Model download list

> Scheme principles: fully open-source, local inference, zero API cost. The list below corresponds **one-to-one** with the local `models\` directory (verified 2026-10-11: ~263.5 GB across 40 top-level directories); the status column reflects what is actually ready locally. A brand-new environment (Linux 5090 server) must re-fetch from the download URLs, or migrate `models` wholesale via rsync per [Appendix H.4](#h4--file-transfer-and-symlinks). **Recommended download order**: audio small items first (the full Qwen3-TTS set, SenseVoice, Stable Audio 3) → video large items (the full MiniMax H3 set — download both fl2va and ref2va) → image large items (Qwen-Image 2512/Edit 2511, Qwen-Image 2.1, FLUX.2 Klein). Note that `flux-2-klein-9b-fp8` is a **gated repo** (you must log in to HF and accept the BFL terms); after placing models, **restart ComfyUI** so they are recognized.

### Image class

| Model | Target directory | Status | Download URL |
|------|---------|------|---------|
| `qwen_image_2512_fp8_e4m3fn.safetensors` | `models\diffusion_models\` | ✅ ready | <https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_2512_fp8_e4m3fn.safetensors> |
| `qwen_image_fp8_e4m3fn.safetensors` (predecessor of 2512, backup) | `models\diffusion_models\` | ✅ ready | <https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_fp8_e4m3fn.safetensors> |
| `qwen_image_edit_2511_fp8mixed.safetensors` | `models\diffusion_models\` | ✅ ready | <https://www.modelscope.cn/models/Kakazhuce/qwen_image_edit_2511_fp8mixed/resolve/master/qwen_image_edit_2511_fp8mixed.safetensors> |
| `qwen_image_2.1_bf16.safetensors` (Qwen-Image 2.1 base, 7B unified generate+edit) | `models\diffusion_models\` | ✅ ready | <https://huggingface.co/Comfy-Org/Qwen-Image-2.1_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_2.1_bf16.safetensors> |
| `flux-2-klein-9b-fp8.safetensors` | `models\diffusion_models\` | ✅ ready | <https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-fp8/resolve/main/flux-2-klein-9b-fp8.safetensors> ⚠️ gated |
| `triposplat_fp16.safetensors` (legacy, not used by any current workflow) | `models\diffusion_models\` | ✅ ready | local file (kept from an earlier experiment) |
| `qwen_3_8b_fp8mixed.safetensors` (Klein text encoder) | `models\text_encoders\` | ✅ ready | <https://huggingface.co/Comfy-Org/flux2-klein-9B/resolve/main/split_files/text_encoders/qwen_3_8b_fp8mixed.safetensors> |
| `full_encoder_small_decoder.safetensors` (Klein/FLUX.2 decoder) | `models\vae\` | ✅ ready | <https://huggingface.co/black-forest-labs/FLUX.2-small-decoder/resolve/main/full_encoder_small_decoder.safetensors> |
| `qwen_2.5_vl_7b_fp8_scaled.safetensors` (Qwen-Edit text encoder) | `models\text_encoders\` | ✅ ready | <https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors> |
| `qwen3vl_8b_bf16.safetensors` (Qwen-Image 2.1 text encoder) | `models\text_encoders\` | ✅ ready | <https://huggingface.co/Comfy-Org/Qwen-Image-2.1_ComfyUI/resolve/main/split_files/text_encoders/qwen3vl_8b_bf16.safetensors> |
| `qwen_image_vae.safetensors` | `models\vae\` | ✅ ready | <https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors> |
| `qwen_image_2.1_vae_bf16.safetensors` (Qwen-Image 2.1 VAE, 64-channel RGBA) | `models\vae\` | ✅ ready | <https://huggingface.co/Comfy-Org/Qwen-Image-2.1_ComfyUI/resolve/main/split_files/vae/qwen_image_2.1_vae_bf16.safetensors> |
| `flux2-vae.safetensors` (legacy, not used by any current workflow) | `models\vae\` | ✅ ready | local file (kept from an earlier experiment) |
| `triposplat_vae_decoder_fp16.safetensors` (legacy, not used by any current workflow) | `models\vae\` | ✅ ready | local file (kept from an earlier experiment) |
| `4xNomos8kDAT.safetensors` (upscaling, recommended) | `models\upscale_models\` | ✅ ready | <https://huggingface.co/Phips/4xNomos8kDAT/resolve/main/4xNomos8kDAT.safetensors> |
| `Qwen-Image-2512-Lightning-4steps-V1.0-fp32.safetensors` (2512 acceleration LoRA) | `models\loras\` | ✅ ready | <https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/loras/Qwen-Image-2512-Lightning-4steps-V1.0-fp32.safetensors> |
| `Qwen-Image-Lightning-4steps-V1.0.safetensors` (predecessor 2512 acceleration LoRA, backup) | `models\loras\` | ✅ ready | <https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/loras/Qwen-Image-Lightning-4steps-V1.0.safetensors> |
| `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` (2511 acceleration LoRA) | `models\loras\` | ✅ ready | <https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/loras/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors> |
| `qwen-image-edit-2511-multiple-angles-lora.safetensors` (multi-angle LoRA, pairs with the `ComfyUI-qwenmultiangle` plugin) | `models\loras\` | ✅ ready | community LoRA (local file; migrated with `models` on 5090) |
| `birefnet.safetensors` (matting/background removal) | `models\background_removal\` | ✅ ready | <https://huggingface.co/Comfy-Org/birefnet> |
| `Kook_Qwen_2512_真实幻想.safetensors` (2512 realistic/fantasy style LoRA, used by image-01 text-to-image) | `models\loras\` | ✅ ready | local file (community LoRA, no fixed URL; migrated with `models` on 5090, see [Appendix H.4](#h4--file-transfer-and-symlinks)) |
| `[Qwen-Edit]3DChineseStyle_25.safetensors` (Qwen-Edit 3D Chinese-style LoRA, used by image-01 text-to-image) | `models\loras\` | ✅ ready | local file (community LoRA, no fixed URL; migrated with `models` on 5090, see [Appendix H.4](#h4--file-transfer-and-symlinks)) |
| `Qwen-Image-InstantX-ControlNet-Inpainting.safetensors` (Qwen-Image Inpainting ControlNet, outpainting/partial redraw; used by the scene pull/push "outpainting" stage) | `models\controlnet\` | ✅ ready | <https://huggingface.co/Comfy-Org/Qwen-Image-InstantX-ControlNets/resolve/main/split_files/controlnet/Qwen-Image-InstantX-ControlNet-Inpainting.safetensors> |

### Face restoration (facerestore_models, auto-downloaded on first use of Impact-Pack Detailer / ReActor)

| Model | Target directory | Status | Download URL |
|------|---------|------|---------|
| `GFPGANv1.4.pth` (general face restoration, preferred) | `models\facerestore_models\` | ✅ ready | <https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/GFPGANv1.4.pth> |
| `GFPGANv1.3.pth` (backup) | same as above | ✅ ready | <https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/GFPGANv1.3.pth> |
| `codeformer-v0.1.0.pth` (CodeFormer detail enhancement, non-commercial license) | same as above | ✅ ready | <https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/codeformer-v0.1.0.pth> |
| `GPEN-BFR-512.onnx` (GPEN, lightweight speedup) | same as above | ✅ ready | <https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/GPEN-BFR-512.onnx> |

### Other ready slots (2026-10-11)

| Model | Target directory | Status | Download URL |
|------|---------|------|---------|
| `minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors` (H3 fun-controlnet) | `models\model_patches\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/model_patches/minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors> |
| `minimax_h3_latent_upscaler_3d_fp16.safetensors` (pairs with the `h3-latent-upscaler` plugin) | `models\latent_upscale_models\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/latent_upscale_models/minimax_h3_latent_upscaler_3d_fp16.safetensors> |
| `minimaxh3_*.safetensors` — 10 H3 motion embeddings (`art_is_explosion`/`blooming_flowers`/`bullet_time`/`dark_magic`/`fire_breath`/`four_seasons`/`kiss_camera`/`spiral_ascent`/`storm_magic`/`truman_show`) | `models\embeddings\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/tree/main/embeddings> |
| `depth_anything_3_base` / `depth_anything_3_mono_large` / `depth_anything_3_small` | `models\geometry_estimation\` | ✅ ready | <https://huggingface.co/depth-anything/Depth-Anything-3> |
| `dino_v3_vit_h.safetensors` (CLIP vision) | `models\clip_vision\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/clip_vision/dino_v3_vit_h.safetensors> |
| `taeh3.safetensors` (approximate VAE for H3 preview) | `models\vae_approx\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae_approx/taeh3.safetensors> |
| HY-World 2.0 weights: `model.safetensors` + `config.json` (3.05 GB, for the `ComfyUI-HYWM2` plugin / workflow `0034_世界模型`) | `models\hywm2\` | ✅ ready | <https://huggingface.co/tencent/HY-World-2.0> |
| SD1.x / SD2.x standard inference configs, 11 yaml files | `models\configs\` | ✅ ready | ships with the ComfyUI repo |

### Audio class

| Model | Target directory | Status | Download URL |
|------|---------|------|---------|
| `stable_audio_3_medium.safetensors` | `models\checkpoints\` | ✅ ready | <https://huggingface.co/Comfy-Org/stable-audio-3/resolve/main/checkpoints/stable_audio_3_medium.safetensors> |
| `t5gemma_b_b_ul2.safetensors` (StableAudio text encoder) | `models\text_encoders\` | ✅ ready | <https://huggingface.co/Comfy-Org/stable-audio-3/resolve/main/text_encoders/t5gemma_b_b_ul2.safetensors> |
| Qwen3-TTS-12Hz-1.7B-Base (all-purpose: clone + dialogue, default for workflows ④⑤, ~4.5 GB) | auto-downloaded by the plugin to `models/TTS/Qwen/` | ✅ ready | <https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base> |
| Qwen3-TTS-12Hz-1.7B-CustomVoice (9 preset voices, ~4.5 GB) | same as above | ✅ ready | <https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice> |
| Qwen3-TTS-12Hz-1.7B-VoiceDesign (natural-language voice design, ~4.5 GB) | same as above | ✅ ready | <https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign> |
| Qwen3-TTS-12Hz-0.6B-Base (low-VRAM cloning, ~4 GB VRAM, ~2.5 GB) | same as above | ✅ ready | <https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base> |
| Qwen3-TTS-12Hz-0.6B-CustomVoice (low-VRAM preset voices, ~2.5 GB) | same as above | ✅ ready | <https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice> |
| SenseVoiceSmall (ASR auto-transcription of reference text, required by workflow ⑤, ~0.9 GB) | auto-downloaded by the plugin | ✅ ready | <https://huggingface.co/FunAudioLLM/SenseVoiceSmall> |
> **Notes on downloading Qwen3-TTS**: all are **directory-type models** and must be downloaded as whole directories (downloading only the safetensors won't load); `Qwen3TTSLoader`'s `auto_download` (on by default) automatically downloads the whole directory from ModelScope. For manual download: place the 5 Qwen3-TTS models at `models/TTS/Qwen/<model-name>/`, and `SenseVoiceSmall` at `models/TTS/SenseVoiceSmall/`.

| `qwen3.5_2b_bf16.safetensors` (audio encoder) | `models\text_encoders\` | ✅ ready | <https://huggingface.co/Comfy-Org/Qwen3.5/resolve/main/text_encoders/qwen3.5_2b_bf16.safetensors> |

### Video class (MiniMax H3, Comfy-Org/MiniMax-H3 repo)

| Model | Target directory | Status | Download URL |
|------|---------|------|---------|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` (FL2VA, for T2V/I2V) | `models\diffusion_models\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors> |
| `minimax_h3_ref2va_pruned_int8_convrot.safetensors` (Ref2VA, **for R2V reference-to-video, a separate file**) | `models\diffusion_models\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors> |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (text encoder) | `models\text_encoders\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors> |
| `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` (text encoder, second quantisation tier kept alongside nvfp4) | `models\text_encoders\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors> |
| `minimax_h3_video_vae_fp16.safetensors` (video VAE) | `models\vae\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_fp16.safetensors> |
| `minimax_h3_video_vae_int8_convrot.safetensors` (video VAE, second quantisation tier kept alongside fp16) | `models\vae\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_int8_convrot.safetensors> |
| `minimax_h3_audio_vae_fp32.safetensors` (audio VAE) | `models\vae\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_audio_vae_fp32.safetensors> |

> **fl2va and ref2va are task variants of the same base**: the text/image-to-video workflows (0030/0031/0040/0041) use fl2va, the reference-generation workflows (0032/0044) use ref2va — download both. The repo also has bf16/int8_convrot/pruned_fp8_scaled variants to choose from.

### MiniMax H3 Turbo LoRA (official Comfy-Org conversion, ready)

> The H3 Turbo acceleration LoRA (bf16, **~5x speedup**) officially converted by Comfy-Org, from the `loras/` directory of the `Comfy-Org/MiniMax-H3` repo; for downloads inside China, replace the `huggingface.co` prefix with `hf-mirror.com`. Companion requirements: ComfyUI v0.30.0+, KJNodes, ComfyUI-ReservedVRAM, SageAttention.

| Model | Target directory | Status | Download URL |
|------|---------|------|---------|
| `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors` (fl2va 4-step, 768p training domain, 1.82 GB, workflow default) | `models\loras\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors> |
| `minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors` (fl2va 4-step v1.2, newer revision) | `models\loras\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors> |
| `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` (fl2va 8-step, higher quality, 1.82 GB) | `models\loras\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors> |
| `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` (ref2va 4-step, for R2V workflows, 0.36 GB) | `models\loras\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors> |
| `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors` (ref2va 8-step, higher quality) | `models\loras\` | ✅ ready | <https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors> |

### MiniMax H3 speedup essentials

- **Standard kit (built into the workflows)**: Sage Attention (+20–30%, KJNodes `Patch Sage Attention KJ`) + EasyCache (built-in ComfyUI node, parameters 0.30/0.20/0.90, at the cost of long-video coherence) + Turbo LoRA (~5x, see above)
- **VRAM**: runs on 8G/12G/16G (dynamic offloading, clip encoder on CPU); local max is 768p, 2K needs the official API; when VRAM is tight, add a `🎈VRAM/RAM-Cleanup` node or `--vram-headroom`

## Appendix D · Plugins to install

| Plugin | Purpose | URL | Status |
|------|------|------|------|
| ComfyUI-Qwen3-TTS | The open-source TTS main option (clone/voice design/emotion tags/unlimited multi-character dialogue, Apache-2.0) | <https://github.com/wanaigc/ComfyUI-Qwen3-TTS> | ✅ installed |
| ComfyUI-Angelo (optional) | Klein click-to-edit | <https://github.com/shootthesound/ComfyUI-Angelo> | not installed (install when needed) |

### H3 speedup plugins (installed 2026-08-06)

| Plugin | Purpose | GitHub | Status |
|------|------|--------|------|
| ComfyUI-Spectrum-MiniMax-H3 | Spectral feature prediction, reduces sampling evaluations (275★) | <https://github.com/xmarre/ComfyUI-Spectrum-MiniMax-H3> | ✅ submodule |
| ComfyUI-SolAttn_triton | Sol-Attn sparse attention (kijai, verified only on 4090/5090) | <https://github.com/kijai/ComfyUI-SolAttn_triton> | ✅ submodule |
| ComfyUI-ReservedVRAM | Dynamic VRAM reservation, prevents OOM | <https://github.com/Windecay/ComfyUI-ReservedVRAM> | ✅ submodule |
| H3ReferenceSuite (H3RefLoader) | H3 reference loading / workflow suite | ships with <https://github.com/juemin4-source/minimax-h3-guide> | ✅ symlink (see Appendix A) |

> EasyCache is a built-in ComfyUI node (no plugin needed); the ComfyUI-MiniMaxH3-Cache / ComfyUI_GJJ_Nodes that were once considered are not installed (the former is replaced by the built-in EasyCache, the latter is unnecessary).

### Outpainting/crop-upscale plugins (installed 2026-08-10)

| Plugin | Purpose | GitHub | Status |
|------|------|--------|------|
| ComfyUI-Impact-Pack | Local upscaling/detection refinement: `DetailerForEach`/`FaceDetailer` region box-select → crop → upscale → redraw → paste back (3251★) | <https://github.com/ltdrdata/ComfyUI-Impact-Pack> | ✅ submodule |
| ComfyUI_LayerStyle | Layer stylization node pack: `LayerUtility: CropByMask` / `LayerMask: MaskBoxDetect` draw a mask and select a region (3118★) | <https://github.com/chflame163/ComfyUI_LayerStyle> | ✅ submodule |
| ComfyUI-Easy-Use | Usability node pack: `easy imageCrop` frontend box-drag screenshot, `easy imageSplitGrid` nine-grid split-upscale (2651★) | <https://github.com/yolain/ComfyUI-Easy-Use> | ✅ submodule |
| ComfyUI-SeedVR2_VideoUpscaler | SeedVR2 HD restoration/upscaling (image + video, 2723★) | <https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler> | ✅ submodule |
| ComfyUI-SUPIR | SUPIR super-resolution upscale restoration (2303★) | <https://github.com/kijai/ComfyUI-SUPIR> | ✅ submodule |

> All of the above are registered as **git submodules** and loaded via the **directory-level** relative symlink at `ComfyUI\custom_nodes\` (a single link aggregates all plugins). For acceleration enablement details see [Appendix C speedup essentials](#minimax-h3-speedup-essentials).

## Appendix E · Network and mirrors

- **Direct external connection by default**; on direct-connection failure (timeout/403/TLS cut), switch to a local proxy, e.g. the Clash Verge mixed port `127.0.0.1:7890` (both HTTP and SOCKS5 work)
- **HuggingFace China mirror**: just replace the `huggingface.co` prefix in the download link with `hf-mirror.com`, e.g.
  `https://hf-mirror.com/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_fp16.safetensors`
- Some sites (e.g. OpenAI-family domains) get blocked by Cloudflare on direct connection; you need a proxy node that allows the corresponding domain

## Appendix H · Migrating to a Linux + RTX 5090D server (2026-08-06)

> Goal: Windows (8 GB VRAM / 16 GB RAM) → Linux server (RTX 5090D, 32 GB GDDR7).
> Baseline environment: torch 2.13.0+cu130, sageattention 2.2.0+cu130 (post6), triton-windows 3.7.1.post27 (Windows-only; on Linux use `triton`).

### H.1 Hardware / drivers (prerequisites)

- RTX 5090D = Blackwell architecture, **sm_120**, 32 GB GDDR7; the CUDA cores are the same as the 5090 (21760), but the AI throughput is about 71% of the 5090 (2375 vs 3352 TOPS)
- **The Linux driver must be ≥ 570** (CUDA 12.8+); just install the latest 580/6xx series; only continue once `nvidia-smi` recognizes sm_120
- torch must support sm_120: **2.7+cu128 or later**; the 2.13.0+cu130 used here satisfies it. Never use an old torch (2.5.x/cu124 will report `no kernel image available for sm_120`)

### H.2 Rebuilding the environment (Linux cannot directly reuse the Windows environment)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install torch==2.13.0+cu130 torchvision==0.28.0+cu130 torchaudio==2.11.0+cu130 \
  --index-url https://download.pytorch.org/whl/cu130
# The remaining dependencies come from a `pip freeze` of the Windows environment as requirements; the only replacement:
#   triton-windows==3.7.1.post27 → triton (matching torch 2.13)
```

- **sageattention**: 2.2 supports Blackwell; before compiling from source, set `TORCH_CUDA_ARCH_LIST="12.0"` (**only 12.0, do not add 9.0**, or the compile fails); on Blackwell it's about 6% faster than torch attention (community measurement, lower than Ada)

### H.3 Startup parameters (differences from Windows, key points)

| Windows parameter | Linux handling |
|---|---|
| `--disable-pinned-memory` | **Remove** (a Windows 0.30.x regression workaround; on Linux, pinned memory can use up to 95% of RAM — it's a speedup item) |
| `--fast-disk` | **Remove** (a compromise for 8G VRAM / 16G RAM; with 32G VRAM, Qwen-2512 fp8 ~19.5G fits entirely, no disk paging needed) |
| `--enable-manager` | Keep |
| Suggested addition | The default dynamic VRAM is fine; when models can stay resident, try `--highvram` (main model 19.5G + text encoder 7.9G ≈ 27.4G) |

Change the startup script to `start-comfyui.sh`:

```bash
#!/usr/bin/env bash
cd "$(dirname "$0")/ComfyUI"
source ../.venv/bin/activate
python main.py --enable-manager
```

### H.4 File transfer and symlinks

- The super-project: `git clone --recurse-submodules <remote>` (**54 submodules**)
- **models ~263.5 GB are rsynced separately** (`rsync -avP`); the server needs ≥350 GB NVMe reserved
- Rebuild the symlinks (`ln -s` relative paths, 8 total, see the Appendix A list):
  - `ComfyUI/input → ../media/七纹刻印`, `ComfyUI/output → ../media/七纹刻印`, `ComfyUI/models → ../models`, `ComfyUI/user/default/workflows → ../../../workflows`
  - `ComfyUI/custom_nodes → ../custom_nodes` (**directory-level, aggregates 45 plugins**), `custom_nodes/H3ReferenceSuite → ../refs/minimax-h3-guide/custom_nodes/H3ReferenceSuite`, `.claude → .agents`, `stories/.obsidian/plugins → ../plugins`
- `ComfyUI-FallingTS/.env` (API keys) does not go into git; place it separately on the server and `chmod 600`
- Chinese file names/paths are fine under Linux UTF-8

### H.5 Server recommendations

- RAM **≥64 GB** (the H3 video pipeline eats RAM; 32G is the floor); pair it with 32–64 GB swap as a safety net
- Remote access: SSH port-forward to `127.0.0.1:8188`, or `--listen 0.0.0.0` + firewall allowlist
- The 5090D at full load is 575 W; confirm the power supply and cooling headroom
