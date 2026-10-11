# HY-World 2.0 装进 ComfyUI 的可行性 —— 实测结论

- 日期：**2026-09-27**
- 本机：RTX 4060 **8GB**（sm_89 / Ada）｜RAM **15.8GB**（空闲 6.3GB）｜ComfyUI **v0.37.0**｜Python 3.13.13 / torch 2.13.0+cu130
- 磁盘：D: 剩余 **187.5GB**｜models 现有最大单模型 **19.53GB**
- 数据来源：HF `tencent/HY-World-2.0` 官方文件清单（blobs=true，总 **162.73GB**）、官方 README/DOCUMENTATION、运行中 ComfyUI 的 `/object_info`（**2900 个已注册节点**）、本机 `templates\3D模型\`（41 个官方 3D 模板）、GitHub 插件 README

> ⚠️ 根 `scripts\` 临时目录已于 2026-10-11 移除，下文的 `scripts\_hywm2-*` / `scripts\_out-0034-*` 仅作历史记录。

---

## 0. 三句话结论

1. **HY-World 2.0 的「重建段」已在本机装通、跑出真实产物，并已接进 0034 工作流**：WorldMirror-2（1.26B / **3.27GB** bf16）经插件 `ComfyUI-HYWM2` 落地，**4 张照片 → 3DGS + 点云，30 秒**；**8 视图（0034 的 md 表数据）→ 773,024 个高斯，45 秒，8GB 显存跑通**。生成段 HY-Pano-2 是 **~80B / ~158GB**，装不了也跑不动。详见 **§6 安装实施记录** 与 **§7 0034 改造记录**。
2. **ComfyUI 确实有自动显存管理，机制成立，但对 HY-World 2.0 的生成段无效** —— 权重再大也能靠 `--fast-disk` 磁盘流式跑，前提是 **ComfyUI 自己实现了该架构**。HY-Pano-2 用的是官方自带的 `modeling_hunyuan_image_3.py`（Hunyuan Image 3 架构），**ComfyUI v0.37.0 里没有任何 HunyuanImage3 / HY-World 节点**。
3. **「用节点操作生成的模型」这一半完全就绪且已实测** —— ComfyUI 原生自带一整套 3D 资产操作节点（3DGS 三格式导出、网格补洞 `FillHoles`、相机出图、可交互视口）；本次已把 HY-World 2.0 产出的 `.ply` 走通 `Load3D → File3DToSplat → SplatToFile3D(.spz) / SplatToMesh → SaveGLB / RenderSplat / PreviewGaussianSplat`。

---

## 1. HY-World 2.0 的真实组成（官方 Model Zoo）

四段流水线：**HY-Pano 2.0（全景生成）→ WorldNav（轨迹规划）→ WorldStereo 2.0（世界扩展）→ WorldMirror 2.0 + 3DGS 训练（世界合成）**

| 段 | 模型 | 参数 | 权重体积 | 权重位置 | ComfyUI 节点 |
|----|------|------|---------|---------|-------------|
| 世界重建 | **WorldMirror-2** | ~1.2B | **4.82GB**（单 safetensors） | `tencent/HY-World-2.0/HY-WorldMirror-2.0` | ❌ 无原生；社区插件 `ComfyUI-HYWM2` |
| 全景生成 | **HY-Pano-2** | **~80B** | **~158GB**（32 分片 × ~5.1GB） | `tencent/HY-World-2.0/HY-Pano-2.0` | ❌ 无 |
| 全景生成（轻） | HY-Pano-2-Qwen | ~425M | 810MB（LoRA） | 同上 | ❌ 无 |
| 世界扩展 | **WorldStereo-2** | ~17B | ~34GB | **`hanshanxue/WorldStereo`**（第三方个人账号，♥4） | ❌ 无 |
| 轨迹规划 | WorldNav | 未公开 | — | 未公开 | ❌ 无 |

**官方安装要求**（README「Install Requirements」）：CUDA 12.8、Python 3.11.15、**FlashAttention**（Hopper 推荐 FA3，备选 FA2）、自定义 `gsplat_maskgaussian`。官方建议**先跑通 world recon，再加 worldgen**。

> ⚠️ 两张硬墙：① 官方全文**没有给出单卡显存数字**（只有 `disable_heads` / `fsdp_cpu_offload` / `enable_bf16` / `use_fsdp` 这类降显存开关）；② RTX 4060 是 **Ada sm_89**，**FA3 仅 Hopper 可用**，只能走 FA2。

---

## 2. 你的两个前提，逐条核对

### 2.1 「既然生图 35G 都行」→ 机制成立，但数字不对

**成立的部分**：ComfyUI v0.37.0 有 `--fast-disk`，官方定义是 *"Force disk-backed dynamic loading and offload over unpinned RAM"* —— **权重从磁盘流式加载并卸载，不常驻内存**，配合 `--async-offload`（NVIDIA 默认开启）+ 动态 VRAM 缓存（`--cache-ram`）。本机正是用它在 **8GB VRAM + 15.8GB RAM** 上跑 19.53GB 的 MiniMax H3。所以「模型比显存大」不是障碍。

**数字不对的部分**：本机**没有 35GB 的模型**。`models\diffusion_models` 实测最大：

| 体积 | 模型 |
|------|------|
| 19.53 GB | minimax_h3_fl2va_pruned_int8_convrot |
| 19.53 GB | minimax_h3_ref2va_pruned_int8_convrot |
| 19.12 GB | qwen_image_edit_2511_fp8mixed |
| 19.03 GB | qwen_image_2512_fp8_e4m3fn |
| 19.03 GB | qwen_image_fp8_e4m3fn |
| 13.25 GB | qwen_image_2.1_bf16 |

（`qwen_image_2.1_bf16` 若解除 fp8 量化是 ~40GB 级，但当前盘上是 13.25GB。）

### 2.2 「ComfyUI 自动根据显存处理，应该可以处理世界模型」→ ❌ 不成立

**ComfyUI 的自动显存管理只对「ComfyUI 自己实现了架构的模型」生效。** 它不能把任意一个新架构的权重变出节点来。

实测证据：`comfy_extras\*.py` 里**没有任何** `world` / `WorldMirror` / `WorldStereo` 节点文件；`/object_info` 的 2900 个节点中，唯一命中 "world" 的是 `MoGePanoramaInference`（MoGe 全景几何估计，不是世界模型）。HY-Pano-2 自带 `modeling_hunyuan_image_3.py` + `siglip2.py` + `tokenizer.json` —— 是 **Hunyuan Image 3 架构**，而 ComfyUI 只有 HunyuanDiT / HunyuanVideo / Hunyuan3D 三代节点，**没有 HunyuanImage3**。

**再叠加数量级问题**：158GB 权重，即使 NVMe 按 3GB/s 算，**遍历一遍就要 53 秒**；扩散推理动辄数十步，且 D 盘只剩 187.5GB —— 装完基本占满整盘。这已经不是"显存够不够"，而是**根本不成立**。

---

## 3. 你问的「现成的节点」——实测清单

### 3.1 世界模型采样节点：**0 个**

没有 HY-World / HY-Pano / WorldStereo / WorldMirror / Matrix-3D / Cosmos / UniWorld 的任何节点。

### 3.2 但「类世界模型采样」（几何估计 / 3DGS 生成）有 3 条原生链路

| 链路 | 节点 | 权重是否已就位 |
|------|------|--------------|
| **DepthAnything3 → 网格** | `LoadDA3Model` → `DA3Inference` → `DA3GeometryToMesh`（+ `DA3Render`） | ✅ 已就位：`geometry_estimation\depth_anything_3_mono_large.safetensors` **1.27GB**、`_base` 516MB、`_small` 131MB |
| **MoGe → 网格（含全景）** | `LoadMoGeModel` → `MoGeInference` / **`MoGePanoramaInference`** → `MoGePointMapToMesh` | ❌ 权重缺失（需下载） |
| **TripoSplat → 3DGS** | `TripoSplatConditioning` → 采样 → `VAEDecodeTripoSplat` → SPLAT | ✅ 已就位：`diffusion_models\triposplat_fp16.safetensors` **0.71GB** + `vae\triposplat_vae_decoder_fp16.safetensors` **0.55GB** |

另有重量级但缺权重的：Hunyuan3D v2（6 节点）、TRELLIS2 / Pixal3D（10 节点）。

### 3.3 「根据生成结果用节点操作生成的模型」——**这一半完全就绪**

**输入**

| 节点 | 能力 |
|------|------|
| `Load3D` | 读 **`.gltf/.glb/.obj/.fbx/.stl/.spz/.splat/.ply/.ksplat`**，输出 image / mask / mesh_path / normal / **camera_info** / recording_video / model_3d / model_3d_info |
| `Load3DAdvanced` | 同上，带 viewport_state（可存相机状态） |
| `LoadImage` / `LoadVideo` / `VHS_LoadVideo*` | 图像 / 视频输入（多视图帧序列） |

**几何 → 网格**：`DA3GeometryToMesh`、`MoGePointMapToMesh`、`VoxelToMesh(Basic)`（Hunyuan3D 体素）

**SPLAT（3DGS）操作链**

| 节点 | 作用 |
|------|------|
| `File3DToSplat` | 把 `.ply/.spz/.ksplat/.splat` 文件变成可运算的 SPLAT |
| `TransformSplat` | 平移 xyz / 旋转 xyz / 缩放 xyz |
| `MergeSplat` | 多段 splat 合并（**拼接大场景的关键**） |
| `SplatToMesh` | 3DGS → 网格（resolution / kernel / smooth / min_opacity …） |
| `RenderSplat` | **按 `camera_info` 出图**（width/height/frames/splat_scale/sharpen/render_style/背景/opacity 阈值）→ image + mask |
| `GetSplatCount` | 高斯点数量 |
| **`SplatToFile3D`** | 导出三格式：**`ply`**（完整球谐）/ **`ksplat`**（mkkellogg SplatBuffer）/ **`spz`**（Niantic gzip，约小 10×） |

**MESH 操作链（14 个后处理 + 8 个 IO/保存）**

| 节点 | 作用 |
|------|------|
| **`FillHoles`** | **原生网格补洞**（max_perimeter / weld_epsilon_rel / max_vertices / fill_chains） |
| `WeldVertices` / `MeshSmoothNormals` | 焊接顶点 / 平滑法线 |
| `DecimateMesh` / `RemeshMesh` | 减面 / 重网格化（band、fix_poles、drop_small_components） |
| `MergeMeshes` / `RotateMesh` / `Get3DComponents` / `GetMeshInfo` | 合并 / 旋转 / 拆件 / 统计 |
| `UnwrapMesh` / `RenderUVAtlas` | UV 展开 / 出 UV 图 |
| `ApplyTextureToMesh` | image（base_color / metallic / roughness / occlusion / normal）贴回网格 |
| `BakeTextureFromVoxel` / `BakeNormalMapFromMesh` / `BakeAmbientOcclusion` | 体素烘纹理 / 法线烘焙 / AO 烘焙 |
| `MeshTextureToImage` | 反取 PBR 贴图 |
| `RenderMesh` | 按相机出图（mode / width / height / background） |
| `CreateCameraInfo` | 造相机（mode / target / roll / fov / zoom / camera_type）→ 驱动 `RenderSplat`/`RenderMesh` |

**导出与交互视口**

| 节点 | 作用 |
|------|------|
| `SaveGLB` / `MeshToFile3D` / `Save3DAdvanced` | 网格/资产落盘（GLB/GLTF/FBX/OBJ/STL/USDZ） |
| `SaveGaussianSplat` / `SavePointCloud` | 3DGS / 点云落盘（带相机与视口状态录屏） |
| **`Preview3D` / `Preview3DAdvanced`** | **浏览器内可交互 3D 视口** |
| **`PreviewGaussianSplat` / `PreviewPointCloud`** | **可交互 3DGS / 点云视口** |

> 👉 对比 §0034 现状：0034 现在用 `ComfyUI-FallingTS\web\viewer\` 自建视口；**上游 v0.37.0 已自带 `PreviewGaussianSplat` / `PreviewPointCloud` / `Preview3DAdvanced`**，且能直接吃 `SaveGaussianSplat` 的输出。

### 3.4 官方 3D 模板：本机已有 41 个（`templates\3D模型\`）

**权重就位、可直接开跑**：`3d_triposplat_image_to_gaussian_splat.json`（图 → 3DGS，含 `SplatToFile3D` + `RenderSplat` + `SplatToMesh` + `SaveGLB` + `CreateCameraInfo` + `CreateVideo/SaveVideo`）
**只差权重**：`3d_moge_panorama_to_mesh.json`（**全景图 → mesh**）、`3d_moge_perspective_to_mesh.json`、`3d_pixal3d_trellis2_image_to_model.json`、`3d_pixal3d_multi_views.json`、`3d_hunyuan3d_*`（4 个）
**云端付费 API**：`api_hunyuan3d_*`（6）、`api_meshy*`（5）、`api_rodin*`（5）、`api_tripo*`（13）

> ⚠️ 新模板用**前端子图（UUID 节点）**封装：`3d_triposplat_*` 里是 `b64333d5-4e6f-4e99-9506-2ec4f63259fe`，`3d_moge_*` 里是 `94961018-e012-4f04-9891-adc008a73d54`。读 JSON 时要按子图展开，别以为节点缺失。

---

## 4. 社区插件核实（每个都亲手抓过）

**全网至少有 5 个第三方封装，官方（Comfy-Org）零支持。** 本机 `comfy_extras\` 全树与 790 个官方模板内搜 `HunyuanWorld|WorldMirror|WorldStereo|HY-World` 均**零命中**。

| 仓库 | 星 | 最后更新 | 封装的是什么 | 显存声明 | 结论 |
|------|---|---------|-------------|---------|------|
| **`AHEKOT/ComfyUI_HYWorld2`** | **★76** | 2026-07-13 | **最全**：v1.5.1，`tencent/HY-World-2.0`→WorldMirror **V1+V2** 重建、WorldStereo、WorldGen 轨迹（SAM3 + navmesh）、Qwen 全景、PLY/splat 导出与视口、11 节点；自带依赖安装节点 | README 无数字；节点有 `low_vram_mode` / `model_cpu_offload` | ⚠️ **星最多但会毁环境**：`pyproject.toml` 要求 **`transformers>=5.2.0`**（本机 4.57.3，H3/Qwen 节点全依赖它），且 `install.py` 要 **MSVC + CUDA Toolkit 本地编译** `gsplat_maskgaussian`。**不要装进主 venv** |
| **`PozzettiAndrea/ComfyUI-HYWM2`** | ★2 | 2026-08-24 | **只封装重建段**：`HY-WorldMirror-2.0`，走 bf16 镜像 `apozz/hy-worldmirror-2-bf16`（1.26B / **3.27GB**）。9 节点：Load / Reconstruct / SamplePanorama(equirect→透视切图) / Export PLY / Export Gaussians PLY / Export .splat / Preview / PLY 视口 / Splat 视口；vendored 官方 worldrecon 全量代码 | README 无数字；有按空闲显存自动收缩 `target_size` 的逻辑 | ✅ **本机选定**（见 §7）：依赖只有 `comfy-env` + `comfy-3d-viewers`，`gsplat`/`flash-attn` **全部在隔离 env 内**，主 venv 零改动 |
| `cedarconnor/ComfyUI-HunyuanWorld-Mirror` | ★52 | 2025-11-21（10 个月未更新） | HunyuanWorld-Mirror **1.0**（重建，11 节点，COLMAP 导出 + WebGL 视口） | **最低 12GB 显存 / 16GB 内存**；1 帧 ≈4GB；**8 帧 518² ≈7GB**；8–24 帧 8–12GB | ⚠️ 8GB 贴边可行，但封装的是 **1.0 不是 2.0** |
| `guoyouworld/ComfyUI-HY-World-2.0` | ★1 | 2026-06-12 | 宣称覆盖 HY-Pano 2.0 + WorldMirror 2.0 + WorldStereo 2.0 | **≥24GB 显存（48GB 推荐）/≥32GB 内存/≥50GB 磁盘** | ❌ 声明最全但未装时会**走假输出兜底**；8GB 不够 |
| `krmahil/comfyui-hunyuan-world` | ★0 | 2026-04-24（仅活跃 1 天） | HunyuanWorld **1.0**（PanoDiT 全景 + 分层网格） | **需 FLUX.1-dev 与 FLUX.1-Fill-dev 各 ~23GB**；全精度 **~40GB**、FP8 **~24GB**、FP8+缓存 **~20GB** | ❌ 显存不够 |
| `A043-studios/ComfyUI_HunyuanWorldnode` | ★2 | 2025-08-02 | **名字误导**：实际是 Hunyuan3D **物体级** 3D | 4–8GB+ | ⚠️ 不是世界模型 |
| `cedarconnor/ComfyUI_HunyuanWorld` | — | — | — | — | ❌ **404 不存在** |

**其他世界模型在 ComfyUI 里的覆盖**：`Matrix-3D` 无节点（搜索 total_count 0）；`BLM Boundless` 无节点；`UniWorld-View` 无（★22 的 `judian17/ComfyUI-UniWorld-jd17` 是 **UniWorld-V1 图像编辑**，无关）；**`Cosmos-Predict2` 有 ComfyUI 原生支持**（`comfy\supported_models.py` 的 `CosmosT2IPredict2` / `CosmosI2VPredict2` + `comfy_extras\nodes_cosmos.py`），但**全树无 "Predict2.5"**。

**HY-Pano-2（~80B / 158GB）没有任何插件真正加载其权重** —— AHEKOT 的"全景"节点实为 Qwen-Image 系 ERP 外扩，不是 HY-Pano-2。

---

## 5. 结论与三条可选路线

| 方案 | 内容 | 下载量 | 8GB 可行性 | 风险 |
|------|------|-------|-----------|------|
| **A. 真·HY-World 2.0 重建段** ✅**已选** | 装 `PozzettiAndrea/ComfyUI-HYWM2`（WorldMirror-2，1.26B / **3.27GB** bf16）→ 多视图/视频 → 3DGS / 点云 / 深度 / 法线 / 相机 → 接原生 `File3DToSplat` → `SplatToFile3D(.spz)` / `SaveGLB` / `RenderSplat` → `PreviewGaussianSplat`（0034 视口） | ~3.3GB 权重 + 隔离 env（torch 2.8/cu128 ≈2.5GB） | ✅ 大概率可行（同门 Mirror 1.0 的 8 帧档实测 ~7GB） | 插件仅 ★2；`comfy-env` 隔离安装是实验特性；FA 走 FA2（Ada 无 FA3） |
| **B. 零下载立刻可跑** | 用**已在磁盘**的 TripoSplat（0.71GB）+ DA3（1.27GB），跑 `3d_triposplat_image_to_gaussian_splat`，或自建 `DA3Inference → DA3GeometryToMesh → FillHoles → DecimateMesh → SaveGLB`，接 `PreviewGaussianSplat` | **0** | ✅ 最好（权重仅 ~2GB，原生节点） | 不是 HY-World 2.0，是单图/单目 → 3DGS/网格 |
| **C. HY-Pano-2 生成段** | 80B / 158GB，需自建 conda env + FA2 | **~158GB** | ❌ **明确不建议** | 无 ComfyUI 节点；D 盘剩 187.5GB 会被占满；单步需遍历 158GB 权重 |

**顺带修正前一轮调研的一处**：`FillHoles`（原生补洞）此前未被计入 L0′ 路线 —— L0′ 原来是「局部 inpaint 补洞」，现在多了一个**纯几何**的补洞选项，可以先用 `FillHoles` 收小洞、再用 inpaint 补大洞，比纯生成式补洞的几何自洽性更好。

---

## 6. 安装实施记录（已执行，2026-09-27）

### 6.1 选型与落地

| 项 | 值 |
|----|-----|
| 插件 | `custom_nodes\ComfyUI-HYWM2`（克隆自 <https://github.com/PozzettiAndrea/ComfyUI-HYWM2>，v0.0.13，GPL-3.0） |
| 未选 AHEKOT（★76）的原因 | 其 `pyproject.toml` 要求 **`transformers>=5.2.0`**，本机为 4.57.3（ComfyUI v0.37.0 钉定，H3/Qwen 节点全依赖），装进主 venv 会整体崩；且 `install.py` 需 MSVC + CUDA Toolkit 本地编译 `gsplat_maskgaussian` |
| 主 venv 改动 | **零**。`requirements.txt` 只有 `comfy-env==0.3.89`（已在）+ `comfy-3d-viewers==0.2.44`（本次装入）。依赖快照备份在 `backups\pip-freeze-20260927-hywm2-before.txt` |
| 隔离环境 | `C:\Users\zghyu\AppData\Local\Programs\comfy-env`（pixi 工作区，全局共享）；env 名 `hywm2-nodes`，Python 3.13.15 |
| 权重 | `models\hywm2\model.safetensors` **3,273,940,974 B** + `config.json` **842 B**，均与插件 `EXPECTED_SIZES` 精确一致（`apozz/hy-worldmirror-2-bf16`，1.26B 参数） |
| 节点注册 | 2900 → **2909**，9 个 HYWM2 节点全部生效 |

### 6.2 踩过的 4 个坑（都已解决）

1. **软链接布局导致 comfy-env 找不到 ComfyUI 本体**
   `python install.py` 报 `Could not locate ComfyUI base; skipping workspace install`。
   根因：`find_comfyui_dir_from_node()` 先试 `import folder_paths`，独立运行时导入失败 → 退化为向上找 `main.py`；而插件真实位于 `D:\AI\Comfy\custom_nodes\`（`ComfyUI\custom_nodes` 只是软链），向上找不到。
   修法：`$env:PYTHONPATH='D:\AI\Comfy\ComfyUI'` 后运行 `install.py`，`folder_paths` 可导入即返回 `base_path`。
   同一根因还导致插件 `prestartup_script.py` 把 assets 复制到了 **`D:\AI\Comfy\input`**（错误层级）而非 `ComfyUI\input` —— 该目录现为残留，可删。
2. **CUDA wheel 无 cu13.0 版本 → 自动降级**
   `gsplat` / `flash-attn` 在 cu13.0+torch2.13 无预编译轮子，comfy-env 自动探测到 **cu12.8/torch2.8** 组合并装上预编译 wheel：`gsplat-1.5.3+cu128torch2.8`、`flash_attn-2.8.3+cu128torch2.8`（来自 `PozzettiAndrea/cuda-wheels` releases）。**无需本地编译**；隔离 env 内 torch 降为 2.8.0+cu128，ComfyUI 主环境仍 2.13.0+cu130。
3. **插件依赖表漏 `requests` 与 `comfy-kitchen`**（本地补丁，**未提交**，写在 `nodes\comfy-env.toml`）
   - `requests`：vendored `hyworldmirror/utils/visual_util.py:13` 顶层 import，缺失即 `ModuleNotFoundError`。
   - `comfy-kitchen==0.2.35`：`reconstruct.py` 会 `import comfy.model_patcher`，该链最终 `import comfy_kitchen`；隔离 env 不含 ComfyUI 自身依赖，故须显式补。
   - 其余扫描出的缺包**不需要**：`moviepy`（函数内惰性 import，仅深度视频）、`pycolmap`（仅 COLMAP 导出）、`flash_attn_interface`（FA3，在 try/except 内且有 FA2 兜底）。
4. **`Load3DAdvanced` 看不到点云/高斯文件**
   它只列 `MESH_EXTENSIONS = {.gltf,.glb,.obj,.fbx,.stl}`；`.ply/.splat/.spz/.ksplat` 要用 **`Load3D`**（`Load3D` 列全部 9 种扩展名）。
   且 `Load3D` 的 `LOAD_3D` 控件**必须**带齐 `image`/`mask`/`normal` 三个真实文件名（`execute` 无条件 `load_image(image=image['image'])`）+ `camera_info`，空字典会 `KeyError: 'image'`。
   另：导出类节点（`HYWM2Export*`）不是 output 节点，**必须接一个 output 消费者**（如 `HYWM2PreviewPointCloud` / 视口节点）才会执行。

### 6.3 实测结果（RTX 4060 8GB）

**重建**（4 张厨房照片 `assets\kitchen`，`target_size=952`，精度 auto）：

```
LoadHYWM2Model → LoadImagesFromDir//Inspire(4 张) → HYWM2Reconstruct
  → 30 秒完成（首次含模型加载），status=success
  → hywm2_kitchen_ts952_gs.ply    15,633,140 B   3DGS
  → hywm2_kitchen_ts952_gs.splat   7,501,312 B   234,416 个高斯
  → hywm2_kitchen_ts952_pts.ply    3,516,420 B   点云
```

**原生节点操作生成结果**（同一张 .ply 喂 `Load3D`）：

```
Load3D(.ply) → File3DToSplat → SplatToFile3D(spz) → SaveGaussianSplat  → output\3d\*_spz_00001.spz   2,127,118 B
                             → SplatToMesh → SaveGLB                   → output\3d\*_mesh_00001_.glb 13,677,708 B
                             → RenderSplat(color/normal) → PreviewImage → 512×512 PNG 两张
                             → PreviewGaussianSplat / Preview3DAdvanced → 可交互视口（spz / glb）
  4 秒完成，status=success
```

**产物判读（真读）**：`RenderSplat` 出的彩图是一间结构正确的厨房 —— 左侧黄色冰箱、后墙窗户与采光、右侧橱柜与灶台、地板；`HYWM2Reconstruct` 出的法线图能分辨后墙、柜体、抽油烟机与凳子。地板有横向条带伪影 = 4 个视角偏少、覆盖不足，属预期，不是流程问题。

**结论**：8GB 上 **HY-World 2.0 的重建段可以真实跑通**，且产物能被 ComfyUI 原生节点完整操作（高斯→网格→GLB、→spz、按相机出图、交互视口）。生成段（HY-Pano-2 80B/158GB）仍然不可行。

### 6.4 本次写入的路径（可清理）

| 路径 | 内容 | 说明 |
|------|------|------|
| `custom_nodes\ComfyUI-HYWM2\` | 插件本体（未纳入 git 子模块） | 保留 |
| `models\hywm2\` | WorldMirror-2 权重 3.27GB | 保留 |
| `C:\Users\zghyu\AppData\Local\Programs\comfy-env\` | pixi 隔离环境（含 torch 2.8/cu128、gsplat、flash-attn） | 保留 |
| `ComfyUI\temp\hywm2_test\` | 重建产物（3DGS/点云） | 临时，可删 |
| `ComfyUI\input\3d\`（= `output\3d\`，同一目录） | 测试用 3D 文件副本 + `_ref*.png` 占位图 + 原生节点导出的 .spz/.glb | 测试残留，可删 |
| `D:\AI\Comfy\input\` | 插件 prestartup 复制到错误层级的 assets（eth_courtyard/kitchen/workspace/pano.png/icon.png） | **残留，可删** |
| `media\七纹刻印\0034_世界模型\`（= `ComfyUI\output\0034_世界模型\`） | 0034 世界模型产物：**只有一个 `0034_世界模型_世界3DGS.ply`（79.2MB / 1,164,128 高斯）**（`.splat`、点云 `.ply`、以及脚本重复产的那份均已归档到 `backups\backup-0034-{去非PLY产物,脚本重复产物}-20260927\`） | **真实产物，勿删**（参见 §7） |
| `custom_nodes\ComfyUI-FallingTS\dev\make-0034-scene.py` / `_run-0034.py` / `_verify-0034-gs.py` | 0034 生成器（幂等）+ 无头运行器 + 3DGS 渲染判读器 | 保留 |
| `backups\backup-0034_*接入HYWM2世界模型前.*` ×3 | 改造前的 0034 / API prompt / 生成器快照 | 保留 |
| `scripts\_hywm2-*.py` | 本次 5 个测试/探测脚本 | 临时 |

---

## 7. 0034_世界模型 工作流：已接入真·世界模型（2026-09-27）

### 7.1 为什么之前"没有变化"

0034 此前是 **DA3 多视角 → 贴图网格**版（8 节点）：`md 数据表 → ImageBatchMulti → DA3Inference(multiview) → DA3GeometryToMesh → MeshToFile3D → Preview3DAdvanced`。
它是在 **HY-World 2.0 被清理掉**之后建的替代方案 —— 更早一版 0034 本来就是 HYWM2 设计，其生成器 `make_0034_world_model.py` 的备注写着「插件、权重、隔离运行环境、测试产物与临时脚本**已按你的要求清理**，本工作流保留为设计留档，HYWM2 节点当前未注册」。本次把 HY-World 2.0 装回来后，0034 才具备换回真世界模型的条件。

### 7.2 改造后的结构（**5 节点 / 10 连线 / 5 列**，生成器静态校验全过）

> ⚠️ 2026-09-27 同日三次追加改动：① **用户要求「不要网格，只要世界模型」**，整条 DA3 网格支路已删除；
> ② 随后**「我只要 ply，我要最高质量的，其它全部抛弃」**，`.splat` 导出、点云 `.ply` 导出、splat 视口、
> `PreviewAny` 四个节点全删；③ 再后来**「把精修节点化进 0034」** —— 重建与精修一起挪进
> `WorldRefinePLY`（**已并入自有插件 `ComfyUI-FallingTS\world-refine`**，见 §7.7），`LoadHYWM2Model` / `HYWM2Reconstruct` /
> `HYWM2ExportGaussiansPLY` 三个节点**出图**。原因见 §7.7（图内节点被"先装模型再测空闲显存"压在 406，
> 拿不到脚本那条 504）。
> 生成器里加了双重反向校验：网格节点族、被抛弃的导出/视口节点，**以及这三个被挪走的重建节点**，
> 一旦回流就报 PROBLEM。本节表格与 §7.3 已按现状更新，其中 11 节点 / 406 / 45 秒等是历史值。

**输入仍是 md 数据表**（`stories\七纹刻印\0034_世界模型.md`，无任何硬编码图片路径）；八列 `前面…左前` 合成一个 8 视图批：

| 链路 | 产物 |
|------|------|
| `FallingTSMarkDownTable` → `ImageBatchMulti` → **`WorldRefinePLY`**（`ComfyUI-FallingTS\world-refine`）→ `HYWM2PLYAdvancedGaussianViewer` | **一个 3DGS `.ply`**：504 前馈 + 尺度过滤 + 外观精修（PSNR 24.46 → 29.48 dB） |

- **可交互 3D 视口保留**：节点 19（`.ply`，并列字段 dtype/数量与渲染解释方式）。它只读不写，
  同时负责保活上游 `WorldRefinePLY`（STRING 输出必须有 output 消费者）。
- `宽度/高度` 与 `偏航角/俯仰角/距离/目标深度/视场角` 六列都是**预留元数据**，不接任何节点。
- **零图片/视频/网格输出**：全图无 `Save*` / `RenderSplat` / `RenderMesh` / `PreviewImage*` /
  `PreviewVideo` / `CreateVideo`；中间图只进 `ComfyUI\temp\worldrefine\<输入内容哈希>\`。
- 生成器 `custom_nodes\ComfyUI-FallingTS\dev\make-0034-scene.py`（幂等，自身跑六条布局规范 + 链路完整性 + 零输出 + 无网格
  + **唯一 PLY 产物**校验）。三改前的快照在 `backups\backup-0034_世界模型.json-20260927-去非PLY导出前.json`、
  `backups\backup-make-0034-scene.py-20260927-去非PLY导出前.py`。

### 7.3 实测（RTX 4060 8GB，无头 API 提交）

**三改后重跑**（2026-09-27，生成器重出图 + 无头 API 提交 `custom_nodes\ComfyUI-FallingTS\dev\0034_api_prompt.json`，`status=success`）：

```
4 节点 API 图:  FallingTSMarkDownTable → ImageBatchMulti → WorldRefinePLY → PLY 视口
一次 Run: 55 秒  status=success
  [refine] free=6.94GB -> _auto_target_size=504       ← 装模型前测空闲, 所以是 504
  [refine] PSNR 均值 24.46 -> 29.48 dB  透明度中位 0.1943 -> 0.2180
  唯一产物 0034_世界模型_世界3DGS.ply  79,161,121 B / 1,164,128 个高斯
  ply_url /view?filename=0034_世界模型_世界3DGS.ply&type=output&subfolder=0034_世界模型
```

- **输入保真已校验**：`WorldRefinePLY` 落给脚本的 8 张临时 PNG 与 md 表原本那 8 张
  **逐像素相同、批序一致**（`custom_nodes\ComfyUI-FallingTS\dev\_check-worldrefine-inputs.py`）。
  图内产物与早先脚本产物**同尺寸但 SHA256 不同** —— 那是前馈/精修的浮点级非确定性，
  不是输入差异；所以这条链路**不做"逐字节可复现"的承诺**。
- ⚠️ **缓存陷阱（仍然适用）**：ComfyUI 按"节点输入哈希"缓存。图改了但节点参数没变时，整个 Run 会在
  **5 秒**内"成功"结束而**根本不重算、不重写文件**。
  精修侧另有一层缓存：`ComfyUI\temp\worldrefine\<8 张图内容哈希>\preds.pt`，**按内容校验**，换图必然重算。
- **历史值（图内节点时代）**：`[Inference] shape=[1, 8, 3, 238, 406]`。三次对照（关掉未用的
  `predict_depth/normals/points` 三个 head / `POST /free` 把空闲显存从 2.4GB 抬到 6.8GB / 三种变体产出）
  结果**完全一致** ⇒ 406 不是显存不够，而是"测得太晚"（见 §7.7）。探针脚本
  `custom_nodes\ComfyUI-FallingTS\dev\_probe-0034-heads.py`、`custom_nodes\ComfyUI-FallingTS\dev\_probe-0034-vram.py` 留档。

**产物真读**：把这份 3DGS 用核心 `RenderSplat` 渲成 768×768（8 秒 4 帧）后判读，得到一间**结构自洽的书房** —— 门洞与门扇、门左侧**圆形白色挂钟**、窗洞亮度区、四面墙与天花、右侧家具轮廓；环绕到另一机位后盒体结构不崩。门与挂钟的相对位置与 md 表场景描述「后墙中部偏右一扇关着的深色木门……门右侧墙面一只圆形白色挂钟」**吻合**，说明 8 个面的世界坐标确实被解到同一坐标系里。颜色偏灰是预期的架构限制：3DGS 头只输出 **SH degree 0（视图无关颜色）**，而这 8 张来自 H3 旋转视频的帧彼此不一致，模型只能把颜色平均掉。

**删除前（两条支路并存，历史值）**：8 视图一次 Run **45 秒**，另有 B 支路网格 GLB 落到 `temp\`。

**产物真读**：把这份 3DGS 用核心 `RenderSplat` 渲成 768×768（8 秒 4 帧）后判读，得到一间**结构自洽的书房** —— 门洞与门扇、门左侧**圆形白色挂钟**、窗洞亮度区、四面墙与天花、右侧家具轮廓；环绕到另一机位后盒体结构不崩。门与挂钟的相对位置与 md 表场景描述「后墙中部偏右一扇关着的深色木门……门右侧墙面一只圆形白色挂钟」**吻合**，说明 8 个面的世界坐标确实被解到同一坐标系里。颜色偏灰是预期的架构限制：3DGS 头只输出 **SH degree 0（视图无关颜色）**，而这 8 张来自 H3 旋转视频的帧彼此不一致，模型只能把颜色平均掉。

### 7.4 这一轮踩到的两个坑（都会静默失败）

1. **软链侧的相对路径算错 → viewer 的 URL 变成 404。**
   插件 `_build_view_url` 用**真实路径**（`D:\AI\Comfy\media\七纹刻印\…`）对 `folder_paths.get_output_directory()`（**软链路径** `D:\AI\Comfy\ComfyUI\output`）求 `relpath`，得到 `..\..\media\…` 开头 → 被判"不在 output 内" → 回落成 `subfolder=` 为空的 URL，视口里永远加载不出模型。
   **修法**：`output_dir` 用**软链侧**绝对路径 `D:\AI\Comfy\ComfyUI\output\0034_世界模型`（同一物理文件）。顺带这个写法**跟随当前项目**，比硬编码 `media\七纹刻印` 更稳。校验结果：`/view?filename=0034_世界模型_世界3DGS.splat&type=output&subfolder=0034_世界模型` → **HTTP 200 / 24,736,768 B**。
2. **`Load3D` 只扫 `input\3d\**`，不是整个 input。**
   `nodes_load_3d.py:18` 写死 `os.path.join(folder_paths.get_input_directory(), "3d")`。所以落在 `input\0034_世界模型\` 的 3DGS **不会**进它的下拉列表；要拿原生节点加工（`SplatToMesh`/`SaveGLB`/`FillHoles`）必须先把文件放到 `input\3d\`。
   附带确认了会话开头那个悬案：**V3 节点的 `define_schema()` 结果在进程内被缓存**，启动后新建的文件不会出现在下拉里 —— 重启后 `Load3DAdvanced` 立刻从 `['none']` 变成能列出 `3d\…glb`，与缓存假设一致。
   不过 `Load3D.validate_inputs` 只调 `exists_annotated_filepath`、**不校验下拉列表**，所以无头运行可直接喂未列入下拉的相对路径，不必拷贝、不必重启。

### 7.5 遗留

- **浏览器必须 F5 强刷**才能看到新 0034；⚠️ 如果 0034 的标签页还开着，前端内存里是**旧副本**，此时按保存会把旧内容整份写回磁盘覆盖本次改动。若被覆盖，重跑 `python custom_nodes\ComfyUI-FallingTS\dev\make-0034-scene.py` 即可原样恢复（生成器幂等）。
- 表内当前这八张素材**不闭合**（从 0031 的 H3 旋转视频抽帧，每面墙各是一张正面视角，相邻面重叠不足）→ 会拼出开口的墙皮扇面。换真机环绕实拍（或 Qwen 多视角 LoRA，相邻面共享墙角）即可闭合，链路与参数都不用改。
- 8 视图在 8GB 上被模型内部按 token 预算压到长边 **406**（实测 238×406；腾空显存与关掉未用 head 都不改变它，见 §7.3），是架构内的固定预算、不是可调参数。精修脚本已重建并落定：`custom_nodes\ComfyUI-FallingTS\world-refine\refine_0034_gs.py`（见 §8）。
- 0034 的 `偏航角/俯仰角/距离/目标深度/视场角` 五列仍是**预留元数据**（按"先不输出图片视频"保留）。

### 7.6 导出的格式有哪些、差在哪（2026-09-27 实测 header 核对）

> **现状（三改后）：0034 一次 Run 只写 1 个文件** —— `0034_世界模型_世界3DGS.ply`
> （`WorldRefinePLY` 在 `eff=504` 上前馈 + 尺度过滤 + 外观精修，1,164,128 个高斯，见 §7.7 与 §8）。
> `.splat` 与点云 `.ply` 已按用户要求抛弃：文件移到 `backups\backup-0034-去非PLY产物-20260927\`，导出节点从图里删除。
> 下面这张表保留三种格式的对照，作为"为什么选 `.ply`"的依据。

二改前，0034 一次 Run 曾写 **3 个文件、2 种扩展名**（`HYWM2Export*` 没有格式下拉框，格式由节点决定）：

| 文件 | 大小 | 记录数 | 每记录 | 内容 |
|------|------|--------|--------|------|
| `0034_世界模型_世界3DGS.splat` | 24,736,768 B | **773,024** | 32 B 定长 | pos f32×3 + **线性** scale f32×3 + RGBA u8 + 四元数 u8 |
| `0034_世界模型_世界3DGS.ply` | 51,537,888 B | **757,904** | 68 B | `x,y,z,nx,ny,nz` + `f_dc_0..2` + `opacity` + `scale_0..2` + `rot_0..3`，全 f32，`binary_little_endian` |
| `0034_世界模型_世界点云.ply` | 11,595,540 B | 773,024 | 15 B | `x,y,z` f32 + `red,green,blue` uchar —— **只有点，没有高斯** |

⚠️ **`.ply` 这个扩展名在本链路里有两个完全不同的含义**：3DGS 的 `.ply`（17 个属性/顶点）与点云的 `.ply`（6 个属性/顶点）。光看扩展名分不出来，只看 header 的 `property` 列表才认得出。

`.splat` 与 3DGS `.ply` 的实质差异：

1. **球谐**：PLY 里 `f_dc_0..2` 是标准 3DGS 的 SH 直流分量槽位（本模型只出 degree 0，但槽位在、SH-aware 工具能直接读）；`.splat` **完全没有 SH**，只有 RGB。
2. **精度**：PLY 全 f32；`.splat` 把颜色和四元数都压成 8 bit（`q*128+128`），scale 仍 f32。
3. **高斯集合不同**：`save_gs_ply` 按**最大尺度的 98% 分位**砍掉最大的 2%（大雾团）→ 757,904；`.splat` 不过滤 → 773,024。**两个文件不是同一份数据**，`.splat` 反而多 15,120 个高斯。
4. `.splat` 还按可见性排序（`−Σexp(scale)·α` 从大到小），给流式/渐进加载的 web 查看器用；PLY 不排序。

**同一份 3DGS 还能再转的容器**（原生 `SplatToFile3D` 的三选一，tooltip 原文）：

| 格式 | 节点原文 | 含义 |
|------|----------|------|
| `ply` | standard 3D Gaussian Splat with **full spherical harmonics** | 最全最大 |
| `ksplat` | mkkellogg SplatBuffer（level 0, uncompressed）, base color only | 居中 |
| `spz` | Niantic gzip-compressed（**~10× smaller**）, base color only | 最小最糙（24.7MB → 约 2.5MB 级） |

**网格格式**：`MeshToFile3D` 只出 GLB；`SaveGLB` / `Save3DAdvanced` 吃 mesh 或任意 3D 文件（`GLB/GLTF/OBJ/FBX/STL/USDZ/PLY/SPLAT/SPZ/KSPLAT`）。**0034 已无网格节点，这些只在你另开图时才有。**

⚠️ **类型不通，是接原生导出节点的前提**：HYWM2 出的是自定义 `HYWM2_GAUSSIANS` / `HYWM2_POINTS`，原生 `SplatToFile3D` / `SaveGaussianSplat` 吃的是 ComfyUI 的 `SPLAT` / `FILE_3D_*`。要用后者必须先用 `Load3D` 把产物读回来（而 `Load3D` 只扫 `input\3d\`，两段式，见 §7.4-2）。

**看着像导出、其实没落盘的**：`HYWM2Reconstruct` 的 depth / normal 是 IMAGE 输出（图里故意不接）；相机内外参只在内存里传；只有接了 `SaveGaussianSplat` / `Save3DAdvanced`（带 `viewport_state` + 宽高）才会额外落一份**渲染缩略图 PNG + 机位元数据** —— 0034 没接。

**选用建议**：`.ply` 当母版（有 SH 槽位 + f32，喂 Blender / SuperSplat / 后续加工）。
**现状（三改后）：产物目录只有一个 PLY** —— `0034_世界模型_世界3DGS.ply`（**79,161,121 B / 1,164,128 个高斯**），
由 `WorldRefinePLY` 在图内产出：`eff=504` 前馈 + 2% 尺度过滤 + 外观精修（`reg_opac=0.5`，PSNR 24.46 → 29.48 dB）。
早先脚本单独产的那份同名 PLY 已归档到 `backups\backup-0034-脚本重复产物-20260927\`。

### 7.7 为什么把重建从图内节点挪进 `WorldRefinePLY`（读源码定案，2026-09-27）

**约束**：精修要 `gsplat`，而 `gsplat` 只存在于 `comfy-env` 的 `hywm2-nodes` 环境里（主 venv 是
torch 2.13+cu130，装不了 cu128 的 gsplat）。所以"精修节点"必须跑在那个环境里。

**读 `comfy_env==0.3.89` 得到的两个硬事实**：

1. 环境名由**目录名**推导：`get_env_name(plugin_dir, config_path)` = `<插件去 comfyui 前缀、去分隔符>-<配置所在子目录>`
   （`comfy_env/environment/cache.py:52`），且 **一个环境一个 worker 进程**
   （`isolation/wrap.py:522`，worker 以 env 目录为 key）。⇒ 我自己的插件**必然落到另一个环境**，
   和 HYWM2 的节点不在一个进程里；跨进程传张量这套是支持的（`isolation/tensor_utils.py` 会递归处理
   dict/tensor，CUDA 走 IPC handle），但要新建第二个 pixi 环境（torch+gsplat ≈2.5–3GB）。
2. **要命的顺序**：`HYWM2Reconstruct` 先 `mm.load_models_gpu([patcher])` 把 WorldMirror 装进显存
   （`nodes/reconstruct.py:248`），**然后**才 `mm.get_free_memory()` 算分辨率 token 预算（:263）；
   而 `get_free_memory` = 真实空闲 + torch 缓存（`comfy/model_management.py:1814-1820`）。
   脚本 `refine_0034_gs.py` 是在 `from_pretrained` **之前**测空闲 ⇒ 实测 `free=6.94GB → eff=504`；
   图内节点测到的是模型已占 3.3GB 之后的量 ⇒ **406**。

第 2 条决定了：**想让图内也吃到 504，必须改 HYWM2 插件代码**（第三方子模块，本仓不动）。
于是选第三条路 —— 把"重建 + 精修"整体交给一个**编排节点**：

- 节点落在**自有插件** `ComfyUI-FallingTS\world-refine\`（`custom_nodes\ComfyUI-FallingTS\world-refine\`，
  **故意不放 `comfy-env.toml`** ⇒ 节点在主进程里跑，不需要新环境）；节点 id 仍是 `WorldRefinePLY`，
  注册走 `plugin.py` 的 `NODE_CLASS_MAPPINGS`（目录名含连字符，经 `importlib` 按名加载）。
- 节点 `WorldRefinePLY(images, steps, mode, reg_opac, refresh) -> STRING`：
  ① 把上游 8 张图按批序落成 `ComfyUI\temp\worldrefine\<内容哈希>\00..07.png`；
  ② 用隔离解释器跑 `custom_nodes\ComfyUI-FallingTS\world-refine\refine_0034_gs.py`（504 前馈 + 外观精修 + 尺度过滤）；
  ③ 从脚本 stdout 的 `[OUT] <path>` 取回 PLY 路径，交给下游视口。
- 图里因此**只有一次前馈**，不会出现"图内 worker 与新进程各装一份 WorldMirror 抢 8GB 显存"。
- 缓存按**8 张图的内容哈希**分层，换图必然重算；`refresh=True` 强制忽略缓存。

**代价（要认）**：0034 里不再有 HYWM2 原生节点，重建逻辑通过脚本执行；
`WorldRefinePLY` 依赖两个外部绝对路径（隔离解释器 `hywm2-nodes\python.exe` 与精修脚本），
生成器已加存在性校验（连节点源文件 `world-refine\nodes.py` 一起校验）。
另：**改这个节点后必须重启 ComfyUI** 才会注册（本轮重启过一次，`/object_info` 已确认注册），
`images=None` 时按插件约定"回放上次产出的 PLY"（无产出则输出空串，下游视口会显示 not found 而不崩）。

---

## 8. 0034 画质：前馈之后再精修一段（2026-09-27）

### 8.1 先量，不猜

| 查的东西 | 结果 |
|---|---|
| 8 张输入是不是一组自洽 360 | **是**。门在 `右后/后面/后左` 连续出现，挂钟跟着门走，窗在 `前面/前右/左前`，抽屉柜在 `前面/前右/右面`，书架在 `右面/右后/后面`。参考板没问题 |
| 有没有更高清母版可重抽帧 | **没有**。`00001_书房旋镜视频.mp4` 就是 **832×480 / 243 帧 / 10.125s**，抽出的 8 帧已是原生长边 |
| 用**模型自己预测的相机**渲染 8 视图对 GT 算 PSNR | **24.46 dB**（逐视图 21.70–27.47）⇒ 模型对输入**自洽**，不是"几何崩了" |

真正的三个瓶颈（都是模型/预算侧，不是参数没调对）：

1. **ViT 分辨率被显存 token 预算压到 504×294/视图。** `reconstruct.py` 的 `_auto_target_size()`：`budget_tokens = free_gb×1500`、`eff = 14·√(budget/views)`。实测 8 视图、6.94GB 空闲 → **504**，而 `compute_adaptive_target_size` 给的上限是 **826**。注意力对 token 是平方级，总量就是被 8GB 卡死的 —— 与视图数怎么分无关（8 视图×504² ≈ 16 视图×354² ≈ 同一预算）。
2. **SH degree = 0。** `worldmirror.py` 写死 `sh_degree=0`，`sh` 形状是 `[N,1,3]` ⇒ 颜色**物理上不可能**有视角依赖；导出 `decode_gaussians` 还只取 SH 的 DC 项当 RGB。
3. **opacity 中位数只有 0.194。** 半透明大量叠加 → 发灰发白，这是"糊"的主因，不是几何问题。

### 8.2 精修：光栅化渲染不吃 token 预算

ViT 阶段受 token 预算限制，但**渲染不受** —— 所以可以按 **826×476 全分辨率**监督，这是唯一能把被丢掉的分辨率找回来的通道。脚本 `custom_nodes\ComfyUI-FallingTS\world-refine\refine_0034_gs.py`（在隔离 env `hywm2-nodes` 里跑，cwd = 插件目录）：前馈 → 用预测相机算基线 PSNR → Adam 精修 → 落 PLY + 对拍图。

| 配置 | PSNR | 新视角体检 |
|---|---|---|
| 基线（前馈输出） | 24.46 dB | — |
| 外观-only（800 步，无信任域，旧默认） | 30.48 dB | 干净 |
| **外观-only + 不透明度信任域 `--reg-opac 0.5`（现默认）** | **29.48 dB** | **干净，且远机位无雾**（见 §8.5） |
| 几何+外观（800 步，无正则） | 35.77 dB | ❌ 门边"梳齿"、抽屉柜"蠕虫" |
| 几何+外观（reg=3.0 信任域） | 32.69 dB | ⚠️ 轻微梳齿 |

**结论：默认外观-only + `reg_opac=0.5`。** 比无信任域少 1.0 dB，但把不透明度中位从 0.194→0.366 压回 0.194→0.218 ——
远看那层灰雾因此不会加重。几何精修虽多 2.2 dB，但会把高斯撑成对准 8 个训练机位的形状 —— **在没见过的角度上崩**，故降级为可选项。这里必须强调：**8 个训练视角的 PSNR 高 ≠ 3D 资产好**，所以每轮都跑"相邻训练机位之间插值"的新视角体检，另加 §8.5 的远机位体检。

用法（幂等，可重复跑；预测结果缓存 85MB 到 `scripts\_cache-0034-preds.pt` 以免重复前馈）：

```powershell
cd D:\AI\Comfy\custom_nodes\ComfyUI-HYWM2
& 'C:\Users\zghyu\AppData\Local\Programs\comfy-env\.pixi\envs\hywm2-nodes\python.exe' D:\AI\Comfy\custom_nodes\ComfyUI-FallingTS\world-refine\refine_0034_gs.py
```

产物：`media\七纹刻印\0034_世界模型\0034_世界模型_世界3DGS.ply`（**1,164,128 高斯 / 79.2 MB**，标准 3DGS 布局：x,y,z + nx,ny,nz + f_dc_0..2 + opacity + scale_0..2 + rot_0..3；`scale_0..2` 是自然对数、`opacity` 是 logit）—— **三改后这个文件由图内的 `WorldRefinePLY` 直接产出**。对拍与体检图留在 `scripts\_out-0034-refine\`（`cmp_refined.png` 三行＝原图/前馈/精修；`novel_views.png` 两行＝前馈/精修 的新视角；`four_way.png`＝§8.5 的远机位四方对照），**不写进产物目录**（保持本条链路零图片输出）。

### 8.3 已做：节点化（走"编排节点"，不建新环境）

原计划是写一个吃 `HYWM2_GAUSSIANS` 的精修节点插在 `HYWM2Reconstruct` 与导出之间。
读 `comfy_env` 源码后放弃了这个形状（原因见 §7.7）：精修要 gsplat ⇒ 必须跑在 `hywm2-nodes` 环境里，
而我自己的插件按目录名必然落到**另一个**环境（一个环境一个 worker 进程），要么新建第二个 pixi 环境
（≈2.5–3GB），要么让图内 worker 与新进程各装一份 WorldMirror 抢 8GB 显存 —— 两个都不划算。

最终做成了 **自有插件 `ComfyUI-FallingTS\world-refine` 里的 `WorldRefinePLY`**：主进程节点只负责
"落临时 PNG → 调隔离解释器跑 `custom_nodes\ComfyUI-FallingTS\world-refine\refine_0034_gs.py` → 转发 PLY 路径"，
**不新建环境、不跨进程传高斯、图里只有一次前馈**，并且顺带吃到了 504（图内节点只能 406）。
0034 的三改结构见 §7.2，代价见 §7.7。
（该节点最初写成独立插件 `ComfyUI-WorldRefine`，同日按用户要求**并入 FallingTS**；
节点 id 未变，因此 0034 的工作流 JSON 与生成器无需改结构。并入后已强制重算验收：
`refresh=True` 走完整链路 55 s、`free=6.94GB → _auto_target_size=504`、产物 1,164,128 高斯 / 79.2 MB、
目录内仍只有一个文件。）

**未做**：把精修做成"吃图内 `HYWM2_GAUSSIANS` 的真节点"（需要那个第二环境）；以及几何精修
（`mode=all`，会出"梳齿/蠕虫"，只作为可选参数留着）。

### 8.4 还没解决的

- **书架的蠕虫状浮点、挂钟重影**是**前馈几何本身**的缺陷（基线里就有），外观精修不动几何所以照样在。要压掉得做「带信任域的几何精修 + 浮点剪枝」，且必须用新视角体检 —— 否则只是把伪影换个位置。
- 输入素材"相邻面不闭合"那条仍然成立（当前这批是从 H3 旋转视频抽的帧）；要更实，换真机环绕实拍或 Qwen 多视角 LoRA。

### 8.5 远机位体检：那层雾的真凶是**上游 `save_gs_ply` 的批次坑**，不是精修（2026-09-27 实测定案）

上一轮我按"精修版远看更雾"推断"外观精修把高斯推多推软"，**这个归因是错的**。拆开变量重测后真相如下。

**关键事实**

- 脚本的前馈跑在 `eff=504`（用 `torch.cuda.mem_get_info` 自己算），而图内节点被 `mm.get_free_memory`
  压到 `eff=406`；高斯数与像素数成正比 ⇒ 504 是 **1,185,408** 个、406 是 **773,024** 个。
  所以"精修版高斯多 53%"**根本不是精修造成的**，是分辨率不同。
- **`save_gs_ply` 的尺度过滤在批次张量上会静默失效**：它用
  `quantile(scales.max(-1), 0.98, dim=0)` 算阈值，只在 **unbatched `[N,3]`** 时得到标量；
  传 **`[1,N,3]`** 时 `dim=0` 是 batch 维 → 逐元素返回自身 → 掩码恒 True → **一个都不砍**。
  节点路径传的是 `[N,3]`（正常砍掉最大 2%，`scale_max` 0.3008 → 0.0098）；
  我的精修脚本原先把 `scales.unsqueeze(0)` 传进去（`scale_max` 保持 0.3008）—— 那 2% 的
  **0.3 尺度巨型雾团**就这样留在 PLY 里。⇒ **"远看一圈雾"= 缺尺度过滤**。

**四变体对照**（`custom_nodes\ComfyUI-FallingTS\dev\_compare-0034-ply.py`，隔离 env 内用 gsplat 直接读 PLY 渲染，
三个变体共用**同一相机/同一分辨率**，避免 ComfyUI 的 Load3D 文件下拉缓存与节点缓存干扰）：

| 变体 | 高斯 | `scale_max` | 训练机位 | 房间外远机位 |
|------|------|-------------|----------|--------------|
| A 图内母版 eff406 | 757,904 | 0.0098 | 清晰 | 干净 |
| B 脚本基线 eff504（**修好落盘后**） | 1,164,128 | 0.0087 | 偏平 | 干净 |
| C 旧精修 eff504（未过滤） | 1,185,408 | 0.3008 | 偏平 | ❌ **一圈大雾** |
| E **精修 eff504（过滤 + `reg_opac=0.5`）** | 1,164,128 | 0.0087 | **最清晰、细节最多** | 干净 |

对拍图 `scripts\_out-0034-refine\four_way.png`（行 A/B/C/E，列 训练机位0 / 远机位）。

**定案**：`..._世界3DGS_精修.ply` = 504 前馈 + 2% 尺度过滤 + 外观精修（`reg_opac=0.5`，24.46 → **29.48 dB**），
远机位无雾、训练视角最清楚，**是这条链路目前质量最高的 PLY**。旧的未过滤版已留档到
`backups\backup-0034-旧未过滤精修-20260927\`。

**教训**：`save_gs_ply` 的入参必须是**非批次**的 `[N,3]`/`[N,4]`/`[N]`；批次调用不会报错，
只会安静地少砍那 2%，而肉眼要到**房间外**才看得出来。

渲染脚本：`custom_nodes\ComfyUI-FallingTS\dev\_render-0034-ply.py`（`Load3D → File3DToSplat → RenderSplat`，中性参数；
⚠️ `Load3D.image` 是 `LOAD_3D` 控件，API 里必须传 **dict** 而不是路径字符串；
⚠️ `Load3D` 只认启动时扫描到的文件，且**节点缓存只看路径字符串** —— 换掉文件内容仍会命中缓存拿到旧图，
所以 PLY 之间的严格对比要走 `_compare-0034-ply.py`，别用 ComfyUI 那条路），
对拍图落在 `scripts\_out-0034-render\`（不写进产物目录）。

### 8.6 `f_dc` 双变换：参考图的颜色为什么没进世界模型（2026-09-28 定案）

**症状**：图里 `HYWM2PLYAdvancedGaussianViewer`（以及核心 `Load3D → File3DToSplat → RenderSplat`）
打开产出的世界模型，整间书房是**一片中灰发白**：深蓝灰的墙是白的、暖木地板是灰的、深棕木门也是浅的。
几何/布局是对的（门、窗、挂钟、书架、柜子都在对的位置），只有颜色不对。

**量化**（`custom_nodes\ComfyUI-FallingTS\dev\_diag-0034-ply-color.py`，直接读 PLY 的 `f_dc`）：

| | R | G | B | 饱和度中位 | 亮度中位 |
|---|---|---|---|---|---|
| 8 张参考图 | 0.165 | 0.136 | 0.101 | 0.047 | 0.141 |
| 修复前 PLY 解码色 | 0.556 | 0.546 | 0.535 | 0.016 | 0.548 |
| 修复后 PLY 解码色 | 0.183 | 0.151 | 0.113 | 0.049 | 0.169 |

**根因（一个字符级的错）**：`refine_0034_gs.py` 的 `dump_ply` 把 `sh[:,0,:] * C0 + 0.5`（已经变成 RGB 了）
当成 `save_gs_ply` 的 `rgbs` 实参传了进去，而 `_build_gs_ply_data` 是把这个实参**原样**写进 `f_dc_*` 的 ——
`f_dc_*` 在 3DGS PLY 里的定义是 **SH 的 DC 系数**，所有读取端都要再算一次 `0.5 + C0*f_dc`：

- 本插件自己的 `save_utils.process_ply_to_splat`：`0.5 + SH_C0 * v["f_dc_0"]`；
- 浏览器视口（mkkellogg，`web\ply_advanced_gaussian\viewer.html`，`sphericalHarmonicsDegree=0`）同口径；
- 核心 `RenderSplat` 同口径。

于是变换做了两遍：`0.5 + C0*(0.5 + C0*x)` ≈ 0.64 + 0.08x —— 全部颜色被压向 0.5 附近的中灰，
饱和度被乘了 `C0=0.282`（实测 0.047 → 0.016，正好 1/3.5）。**前馈/精修本身没算错**：
同一份缓存里模型输出的 DC 解码色是 `[0.178,0.148,0.112]`，与参考图的 `[0.165,0.136,0.101]` 基本一致 ——
错在最后落盘那一步，所以"参考图的颜色没渲染进世界模型"。

**修复**：落盘写**原始** DC 系数 `sh[:,0,:]`（均值约 -1.14），不做 `C0` 变换。同一坑的第二个实例是
`--dump-baseline` 与 §8.5 那四个对照变体（都走同一个 `dump_ply`），一并修好。
⚠️ 上游 `decode_export.py` 的 `HYWM2ExportGaussiansPLY` 也是把 `(sh_dc*C0+0.5)` 当 `rgbs` 传的
（同源不一致），**那是第三方代码，不修改** —— 只是不要用它出的 PLY 做颜色判据。

**同时新增/暴露的参数**（节点 `WorldRefinePLY`，`custom_nodes\ComfyUI-FallingTS\world-refine\refine_0034_gs.py` 对应新增 `--target/--gt/--prune-opac/--reg-color`）：

| 控件 | 默认 | 作用 |
|---|---|---|
| `前馈长边` `--target` | 952（自适应后实测 504） | 几何/布局细节上限，会被空闲显存压低 |
| `颜色监督长边` `--gt` | 826（= 输入原生长边） | 精修对参考图做光度监督的分辨率 |
| `剪枝阈值` `--prune-opac` | 0 | 落盘前剪低不透明度高斯（减远看雾气） |
| `颜色信任域` `--reg-color` | 0.5 | 压住"为凑单个视角把 DC 撑成彩虹色"的极值高斯 |

`--reg-color` 是这一轮唯一动到观感的调参：每步只监督 1 个视角，只在少数视角可见的高斯会被撑成极值，
DC-only 渲染（视口/核心渲染都只看 DC）里就是**墙角上的粉/绿彩色噪点**。实测：

| `reg_color` | 训练视角 PSNR | 参考机位 DC-only PSNR | 与参考图色差 L1 | 饱和度 >0.3 的高斯 |
|---|---|---|---|---|
| 0 | 29.48 dB | 25.51 dB | 0.019 | 3.07% |
| 0.1 | 29.34 dB | — | — | 2.15% |
| 0.5（现在的默认） | 29.10 dB | **27.17 dB** | **0.015** | **1.58%** |

即：训练视角 PSNR 掉了 0.38 dB，但**按读者口径（DC 单色）反而涨了 1.66 dB**、噪点少了一半 ——
与 §8.2 里 `reg_opac` 的取舍同一逻辑（8 个训练视角的 PSNR 高 ≠ 3D 资产好）。

**验收口径（可复跑）**：`custom_nodes\ComfyUI-FallingTS\dev\_verify-0034-color.py <ply> <preds.pt> <out.png>`（隔离环境解释器、
`cwd=ComfyUI-HYWM2`）—— 从 PLY 字段还原高斯、按读取端口径解码 `f_dc`，用前馈预测的 8 个机位渲一遍，
与 8 张参考图并排落成一张对拍图。修复后的对拍图：8 个面**颜色与布局都对上**参考图
（`scripts\_out-0034-refine\dc_verify_rc05.png`；修复前同口径图带粉/绿彩噪）。

---

### 8.7 "影像重叠"不是透明问题：上游推理不做跨视图融合（2026-09-28 定案）

**症状**：视口里门框 / 挂钟 / 墙角各有两个，天花板一道 X 形折痕，整体像"半透明重影"。

**第一步先把变量拆开（不透明度三档对照）**：同一份 PLY、同一批机位，把 α 改成
0.20 / 0.56（视口原样）/ 0.99 三档渲染 —— 重影**一模一样**，连全不透明都不消失
⇒ 与透明度无关，是几何上真有两层表面。（对照图 `scripts\_out-0034-refine\ghost_zoom.png`，
脚本 `custom_nodes\ComfyUI-FallingTS\dev\_diag-0034-ghost.py`）

**根因（读上游源码 + 计数核对）**：

- `rasterization.py:240-242` 在 `is_inference` 时直接 `return predictions`，把紧接着的
  `prune_gs(voxel_size=0.002)`（`:248`）和 `apply_confidence_filter`（`:295-346`）**短路掉**；
  上游 CLI 那条 `save_results` 路径有 mask + 体素合并 + 500 万上限，ComfyUI 节点**从不调用它**。
- 每个视图用**自己的**深度 + **自己预测的**位姿反投影（`position_from="gsdepth+predcamera"`，
  `rasterization.py:522-528`），输出就是 `S × H × W` 的**直接拼接**；本次 1,164,128 ÷ 8 ≈ 14.5 万/视图，
  一个像素一个高斯，零去重。
- 8 个视图视场天然互相覆盖 ⇒ 每个可见表面都有 2 层以上、彼此差几厘米的壳；位姿只有 4 步
  camera-token 精修、没有任何跨视图一致性校正，误差会让整张视图的壳**整体平移**。
- 所以这是**结构性**的（"总是"会发生）；而 `WorldRefinePLY` 原先的 `mode=appearance`
  冻结 means / 四元数 / log 尺度 ⇒ 修不掉。

**修法：`mode=all` + 几何信任域**（节点参数 2026-09-28 起默认 `all` / `reg=3.0`）

| 配置（800 步，同一份缓存） | 8 视图 PSNR | 视口口径 4 机位 | 观感 |
|---|---|---|---|
| 前馈 baseline | 24.46 dB | — | 双层壳 |
| appearance（旧默认） | 29.10 dB | 25.77 dB | 鬼影明显 |
| all `reg=0` | 33.94 dB | 27.50 dB | 鬼影消失，门框/墙角明显"烧焦"暗斑 |
| all `reg=1` | 31.98 dB | 26.48 dB | 有焦边 |
| **all `reg=3`（新默认）** | **31.35 dB** | **26.20 dB** | **轻微焦边，已去鬼影** |
| all `reg=5` | 31.07 dB | 26.09 dB | 很轻 |
| all `reg=10` | 30.63 dB | 25.99 dB | 最干净 |

- **连 `reg=10` 都能把壳收掉** ⇒ 两层壳间距本来就不大，不需要大幅移动几何。
- 训练视角 PSNR 高 ≠ 3D 资产好：`reg=0` 最高，那是把高斯掰成对准这 8 个机位换来的；
  判定必须用**插值新机位**（`custom_nodes\ComfyUI-FallingTS\dev\_diag-0034-novel.py`），实测 reg=1~10 的新机位都没有退化。
- 反面尝试：naive 体素合并（合并后不放大 scale）会产生规则点阵 / 摩尔纹，PSNR 掉到 15~17 dB
  （`custom_nodes\ComfyUI-FallingTS\dev\_diag-0034-fuse.py`）—— 要做合并必须同时膨胀尺度，本轮未采用。

**顺带查实、尚未修**：`opacity` 约定。模型输出的 `opacities` 已经 sigmoid 过
（`act_gs.py:19` → `rasterization.py:497`），却被**原样**写进 `opacity` 字段（`save_utils.py:170`），
读取端按 logit 再 sigmoid 一次 ⇒ 视口里每个高斯的 α 被抬到 **0.50~0.69，没有一个是暗的**
（模型本意 0.008~0.78、中位 0.19），视口口径 vs 真实 α 口径的 PSNR 差 1.5 dB。
修它更"忠实"但画面会更透，**与去鬼影无关，故本轮不动**。

**验收口径（可复现）**：

```text
正式产物: media\七纹刻印\0034_世界模型\0034_世界模型_世界3DGS.ply
          1,161,699 高斯 / 78,995,949 B / sha256 9949067637d9ac92
          (mode=all reg=3.0, 800 步, 图内一次跑完 65s)
对拍(隔离解释器, cwd = custom_nodes\ComfyUI-HYWM2):
  _diag-0034-geo-cmp.py "旧=backups\backup-0034几何重叠-20260928\0034_世界模型_世界3DGS.before_geom_refine.ply" "新=<产物>"   → geo_zoom.png
  _diag-0034-novel.py   同上                                                                                                  → novel_cmp.png
```

`WorldRefinePLY` 的控件因此从 8 个变 9 个（新增 `reg`，`mode` 默认 `all`）⇒ **必须重启 ComfyUI**
让 `/object_info` 更新，0034 生成器据此重算 `widgets_values`；全仓只有 0034 用这个节点，
其它工作流不受影响。改完工作流文件后浏览器要 **F5**。

## 9. 参考链接

- HY-World 2.0 权重仓 <https://huggingface.co/tencent/HY-World-2.0>｜代码 <https://github.com/Tencent-Hunyuan/HY-World-2.0>｜技术报告 arXiv:2604.14268
- WorldStereo-2 权重 <https://huggingface.co/hanshanxue/WorldStereo>
- ComfyUI-HYWM2（★2）<https://github.com/PozzettiAndrea/ComfyUI-HYWM2>
- ComfyUI-HunyuanWorld-Mirror（★52）<https://github.com/cedarconnor/ComfyUI-HunyuanWorld-Mirror>
- comfyui-hunyuan-world（★0）<https://github.com/krmahil/comfyui-hunyuan-world>
- ComfyUI 启动参数语义本机文件：`ComfyUI\comfy\cli_args.py`（`--fast-disk` L182、`--async-offload` L178、`--cache-ram` L140）
- 配套：`docs\开源生成式世界模型调研-2026-09-27.md`、`docs\开源生成式世界模型排名-2026-09-27.md`
