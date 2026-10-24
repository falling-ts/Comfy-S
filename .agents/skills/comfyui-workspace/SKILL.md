---
name: comfyui-workspace
description: "How the D:\\AI\\Comfy workspace itself is organized — the repo map (which directory holds what), the 8 relative symlinks that wire ComfyUI to models/media/workflows/custom_nodes, the numbered workflow catalogue (0011~0070) with its data-table and link chains, the Qwen-Image 2.1 workflow variants, the workflow↔md-table↔media output-directory convention, the dev and git-submodule submission rules, and the known working-tree state. Use when orienting in the repo, deciding where a file belongs, adding or moving a workflow/plugin/skill, wiring or debugging a symlink, understanding which workflow does what, or committing at the repo root. Not for running workflows (comfyui-workflow-runner), operating FallingTS buttons (comfyui-headless-control), or prompt authoring (stories / h3-prompt-writing)."
---

# ComfyUI 本地工作区(仓库导航)

ComfyUI 及自定义节点的本地开发工作区。下文路径均相对项目根目录,不绑定特定操作系统或 shell;文中命令示例按当前本机环境给出,部署到其它平台时按实际环境替换路径分隔符/可执行文件位置即可。

**相关技能**:本机环境与版本/machine 事实见 `comfyui` 技能的 `workspace-env.md` 与 `machine.md`;布局规范见 `comfyui` 技能的 `workflow-layout.md`;跑工作流见 `comfyui-workflow-runner`;操作 FallingTS 按钮见 `comfyui-headless-control`;提示词规范见 `stories`。

## 目录结构(展开至第二级)

| 路径 | 说明 |
|------|------|
| `ComfyUI` | ComfyUI 主程序(git submodule,detached HEAD 跟随上游 release tag,当前 `v0.39.2`):源码/入口在本目录;`models`/`input`/`output`/`user\default\workflows`/`custom_nodes` 均为相对软链接(见「软链接映射」);`blueprints\` 内置 116 个蓝图;其余结构遵循上游官方布局,不再逐一展开 |
| **`custom_nodes`** | **插件聚合目录**:45 个插件子模块 + `H3ReferenceSuite` 链接集中于此,`ComfyUI\custom_nodes` 为目录级相对软链接指向它(§B)。按功能归类: |
| └ 自有插件 | `ComfyUI-FallingTS`:通用工具节点集(共 **22 节点** + 27 个前端增强,已开源);另含**世界模型三节点**:`world-panorama` 的 `WorldSurroundPanorama`(**360° 环绕视频 → 横向展开长图**(等距圆柱条带, 上行=天、无黑边、无重影): 自动定抽帧步长 + 一圈闭环吸附 + ORB/RANSAC 纯偏航单应与「重叠区稠密光度一致性」联立定焦距 + 逐像素 winner-take-all(从不帧间平均), 真 equirect 视频可直接抽帧; 2026-09-28 v2 重做同时修掉 v1 的「长图倒立 + 上下各 30% 黑边 + 帧间平均糊掉细节(拉普拉斯锐度差 4.3 倍)」)、`WorldPanoramaViews`(长图 → 视角批 + **每视角精确 w2c 外参/内参**, 外参口径与 HYWM2 `SamplePanorama` 一致; 等距圆柱竖直朝向按世界地图口径修正, 多 `v_range`/`v_center` 竖向范围), 以及 `world-refine` 的 `WorldRefinePLY`(视角批(可接相机先验) → 504 前馈 + 3DGS **全参数**精修(mode=all + 几何信任域) → 一个 PLY; 接上 `extrinsics/intrinsics` 时把位姿作为先验注入前馈 `cond_flags=[cam,0,intr]`, 从源头消掉上游推理不做跨视图融合留下的多视图双重曝光/重影。2026-09-28 并入并扩到「360 视频进、PLY 出」) |
| └ H3 生态(5 插件 + 链接) | `ComfyUI-Spectrum-MiniMax-H3`(加速)、`ComfyUI-SolAttn_triton`(注意力加速)、`ComfyUI-ReservedVRAM`(显存预留)、`ComfyUI-Qwen3-TTS`(H3 语音)、`h3-latent-upscaler`(latent 放大)、`H3ReferenceSuite`(软链接,见 `refs`) |
| └ 放大/修复/局部重绘 | `ComfyUI-SeedVR2_VideoUpscaler`(视频高清修复)、`ComfyUI-SUPIR`(超分放大)、`ComfyUI_UltimateSDUpscale`(分块重绘)、`ComfyUI-Impact-Pack`(Detailer 局部精修)、`ComfyUI_LayerStyle`(图层/遮罩)、`ComfyUI-Inpaint-CropAndStitch`(裁剪贴回) |
| └ 视频 | `ComfyUI-VideoHelperSuite`、`ComfyUI-WanVideoWrapper`、`ComfyUI-Frame-Interpolation`(补帧)、`ComfyUI-qwenmultiangle`(Qwen 多镜头) |
| └ 3D/世界模型 | `ComfyUI-HYWM2`(HY-World 2.0 世界重建: 8 视图 → 统一世界坐标三维场景 → 3DGS/点云/网格 + PLY 视口; 权重在 `models\hywm2`(3.05GB, 已按槽位约定 gitignore); 隔离环境 `hywm2-nodes`, gsplat 在那 ⇒ 0034 的 `WorldRefinePLY` 借它跑精修。2026-09-27 装, **2026-09-28 登记为 git 子模块**(`[submodule "ComfyUI-HYWM2"]`, branch main, 指针 `93d060e`); ⚠️ `nodes/comfy-env.toml` 有**故意不提交**的本地补丁(`requests` + `comfy-kitchen==0.2.35`), **没留档** —— `backups\` 已于 2026-09-30 清空, 而 `submodule update` 会覆盖它 ⇒ 更新前先自己复制一份该文件) |
| └ 图像/编辑/生成 | `ComfyUI-Easy-Use`、`ComfyUI_IPAdapter_plus`、`ComfyUI-ReActor`(换脸)、`ComfyUI-RMBG`、`ComfyUI-segment-anything-2`、`comfyui_controlnet_aux`、`ComfyUI-IC-Light`、`ComfyUI-DepthAnythingV2`、`Comfyui-QwenEditUtils`、`ComfyUI-Florence2`、`ComfyUI-post-processing-nodes`(后期处理)、`ComfyUI-LNL`(图层/图像合成扩展: 即 LayerStyle Next Level; ⚠️ 声明 `opencv-python~=4.12.0`, 是 numpy 卡在 2.2.x 的约束来源) |
| └ 工具/其它 | `ComfyUI-GGUF`(GGUF 量化加载)、`ComfyUI-KJNodes`(KJ 工具包)、`rgthree-comfy`、`ComfyUI-Custom-Scripts`、`ComfyUI-Detail-Daemon`、`ComfyUI-Crystools`、`ComfyUI-MultiGPU`、`ComfyUI-LogicUtils`、`ComfyUI-Inspire-Pack`、`cg-use-everywhere`、`audio-separation-nodes-comfyui`、`ComfyUI_essentials`、`ComfyUI_LinkFX`(连线动画)、`ComfyUI-AnimatedLinks`(连线动画) |
| `docs` | 本地参考文档:纯 44 个分类 md。⚠️ **原在此的 5 个 git 子模块 + 1 个本地目录(`Qwen-Image-Edit-Skills`)已于 2026-09-30 全部迁往根 `refs\`** |
| └ 分类 md | 启动参数参考、KSampler 采样器指南、SageAttention 参数配置、Qwen 国漫 LoRA 清单、节点输入类型总表、插件注册表、模型调研报告、H3 提示词格式调研、FallingTS 分段执行机制、视频音频分析工具链(读产物全链 + 工具源码)、H3 参考图尺寸与 match/max 口径(源码级复算)、2752×1536 参考图的 max/match 成本收益(源码级复算)等 |
| **`refs`** | **参考类资料聚合目录**(2026-09-30 建:7 个 git 子模块 + 1 个本地目录,由 `docs\` 的 5 个子模块与 1 个本地目录 + 已删除的 `h3\` 的 2 个并入),子模块目录名即线上仓库名。gitdir 形态两种并存:3 个**内联**(`.git` 是目录:`ComfyUI-Docs`/`MiniMax-H3`/`minimax-h3-guide`)、4 个**分离**(`.git` 文件 + `.git\modules\refs\<name>`,其 config 里 `worktree = ../../../../refs/<name>`) |
| └ `ComfyUI-Docs` | ComfyUI 官方文档仓库本地克隆(Comfy-Org/docs,子模块;原 `docs\`) |
| └ `Obsidian-Dev-Docs` | Obsidian 官方开发者文档(插件开发参考,子模块;原 `docs\`) |
| └ `Obsidian-API` | Obsidian API 类型定义(`obsidian.d.ts`/`publish.d.ts`,子模块;原 `docs\`) |
| └ `Qwen-Image-2.1` | Qwen-Image 2.1 官方仓库(提示词规范原文,子模块;原 `docs\`) |
| └ `qwen-image-2.1-skill` | Qwen-Image 2.1 提示词 Skill(含校验器 `validate_prompt.py`,子模块;原 `docs\`) |
| └ `MiniMax-H3` | MiniMax H3 官方模型仓库(自带 9 个官方 Skills,子模块;原 `h3\`) |
| └ `minimax-h3-guide` | H3 参考加载套件(其 `H3ReferenceSuite` 由根 `custom_nodes` 子链接指向,子模块;原 `h3\`) |
| └ `Qwen-Image-Edit-Skills` | Qwen-Image-Edit 官方 Skills 源码参考(`aliyun-image-skill\` 阿里云百炼 API 版 + `comfyui-agent-kit\` 的 comfyui skill 知识文件,共 67 文件)。⚠️ **本地目录、非子模块** —— 由**根仓库以普通文件(非 gitlink)跟踪**,故搬移只需 `git add .` 记重命名,不涉及 gitdir/`.gitmodules`;原 `docs\` |
| **`workflows`** | **用户工作流实际存储处**(前端保存即在此,可经 `GET /userdata?dir=workflows` 读取),共 35 个,按编号-用途分组(详见下方「工作流编号体系」) |
| `models` | 模型实际存放处(`ComfyUI\models` 软链接指向);**40 个顶层目录**(39 个标准槽位各带 `.gitignore`(内容 `*`+`!.gitignore`)忽略模型文件、仅占位入库;另 1 个运行时缓存 `.cache`,无 `.gitignore`、不入库)。当前合计约 **263.5 GB**。已就绪模型见 `comfyui` 技能的 `workspace-env.md` |
| └ 核心生成 | `diffusion_models` / `text_encoders` / `vae` / `loras` / `checkpoints` / `upscale_models` / `background_removal`(已就绪) |
| └ 语音 | `TTS`(Qwen3-TTS 五变体 + SenseVoiceSmall)/ 空槽位 `ASR` / `speaker_models` / `audio_encoders` |
| └ 其余已就绪槽位 | `controlnet` / `facerestore_models` / `clip_vision` / `embeddings`(H3 动作嵌入 10 个)/ `model_patches`(H3 fun-controlnet)/ `latent_upscale_models`(H3 latent 放大)/ `geometry_estimation`(Depth-Anything-3)/ `vae_approx`(`taeh3`)/ `hywm2`(HY-World 2.0 权重 3.05GB)/ `configs` |
| └ 标准空槽位 | 其余 **21 个**槽位目录尚无模型:`clip` / `unet` / `detection` / `reactor` / `SEEDVR2` / `ultralytics` / `yolo` / `diffusers` / `style_models` / `frame_interpolation` / `optical_flow` / `gligen` / `hypernetworks` / `photomaker` / `mesh2motion` / `nlf` / `LLM` / `classifiers` / `ASR` / `speaker_models` / `audio_encoders` |
| `media` | 输入/输出文件(`ComfyUI\input`、`output` 软链接到 `media\七纹刻印`):按**项目**分目录——`template\`(模板, 入库占位)+ 各故事库目录(如 `七纹刻印\`, 实际产物, 不入库);input/output 指向哪个项目, 产物就落在哪个项目目录下 |
| `templates` | ComfyUI 官方模板库本地缓存(**833 个工作流 JSON**,2026-10-10 随模板包 0.11.78 更新):14 个分类子目录——官方核心 598 个分 11 类(`图像`198/`视频`197/`图像工具`46/`3D模型`43/`音频`33/`视频工具`25/`LLM`20/`角色与时尚`12/`产品与广告`11/`品牌与设计`8/`节点基础`5),另有 `自定义节点\`218 个(按插件分子目录)+ `快速开始\`10 个、`矢量\`7 个(本地补遗);`workflow-templates-list.md` 为索引,由模板拉取工具从运行中的服务重建(2026-08-09 曾归档的个人工作流已迁回 `workflows\`) |
| `webs` | 三方网站调研聚合目录(已入库跟踪):三个调研源 |
| └ `RunningHub` | RunningHub 调研:`RunningHub-API读取指南.md` + `workflows-list.md` + `workflows\`(**4571 个**收集工作流,按 **24 个**分类子目录:图像/视频/音频/数字人/室内外设计/风格化/插件 等) |
| └ `Bilibili` | B 站教程调研:`B站教程调研.md` + `Qwen-Image-Edit-镜头控制与360度视角-教程调研-2026-08-09.md` + `工作流大全\`(**474 个**配套工作流) |
| └ `AutoDL` | 云端 GPU 调研:`AutoDL-GPU选型-2026-08-06.md` + `api.md`(云模型库接口)+ `models.md`(**5377 条**模型文件记录 / 4072 个唯一实例路径,2026-10-10 抓取)+ `models-link-report.md`(链接核对报告) |
| `stories` | Obsidian 故事写作工作区(自带 `.obsidian\` 配置 + 插件安装位相对软链,见「软链接映射 §D」):**`plugins\`**(插件聚合目录,与 ComfyUI 侧 `custom_nodes` 同构:含 `Obsidian-Comfy` 一个插件子模块,目录名即线上仓库名;该插件自带文件浏览器「编号分层」排序)+ `template\`(新建故事模板)+ 用户自定义故事库目录(库名随写作项目而定,以盘上实际为准) |
| `logs` | ComfyUI 运行日志(`comfyui*.log`/`comfyui-console*.log`,已 gitignore;可随时清空,保留 `.gitignore` 占位) |
| `backups` | **工作流/重要文件的修改前备份**(2026-08-04 起):`backup-<文件名>-<YYYYMMDD>-<说明>.*` 命名;**纯本地暂存目录** —— `.gitignore` 忽略全部内容(只有 `.gitignore` 本身入库), **可随时整体清空、不承担归档职责**:环境快照(pip-freeze/conda export)、本地 wheel、文档归档一律不留档, 需要时现场重建(`pip freeze`/重新下载);2026-09-30 已全清一次(1646 文件 / 372.8 MB 直接删除),此后又累积了数份(2026-10-11 现存 **5 份**备份: 2 份 `0020_场景首帧` + 1 份 `0031_首帧场景` + 2 份 `0044_参考视频`, 均为 2026-10-11 的「卧室凌晨三点」改稿, 可随时清) |
| `.agents` | 技能聚合目录(Skill 定义, 每个技能一个子目录含 `SKILL.md` + 附件);`.claude` 软链接指向它(§C)。当前 **15 个**技能:`comfyui`/`comfyui-headless-control`/`comfyui-workflow-runner`/`comfyui-workspace`、`stories`(故事库总纲与全集, 2026-10-11 由原名 `stories-*` 五个技能合并)、`qwen-image-2-1-prompting`、`h3-prompt-writing`、`aliyun-image`、`3d-animation-short-generator` 等各类视频生成器技能 |
| `.claude` | SymbolicLink → `.agents`(Claude Code 兼容垫片,技能聚合目录,见「软链接映射 §C」) |
| `README.md` / `README.cn.md` / `LICENSE` | 项目说明(中英双份)与许可 |
| `.gitmodules` | 子模块登记(git submodule) |
| `comfy-server.sh` | **统一**后台服务式启动脚本(跨平台: Linux + Windows Git Bash;杀 8188 旧进程 → 静默后台启动 → 等待端口就绪,日志默认写调用时所在目录 `comfy-server-8188.log`;Windows 等价 `python main.py --enable-manager --disable-pinned-memory --fast-disk`,Linux 用 conda 环境 comfy + `--reserve-vram 22`;覆盖 `PORT`/`WAIT`/`PY_BIN`/`LOG`/`RESERVE_VRAM`) |
| `sync-server.sh` | Syncthing 双机同步的**统一**后台启动脚本(与 `comfy-server.sh` 同风格: 停旧服务 → 后台启动 → 等端口;默认 API 端口 `8384`、日志写调用时所在目录 `sync-server-<port>.log`;Windows 默认 `C:\Program Files\Syncthing\syncthing.exe`,Linux 回退 PATH;覆盖 `PORT`/`WAIT`/`SYNCTHING`/`LOG`)。方案与 Git 侧同步约定见 `docs\双机同步-Syncthing实时文件同步与Git代码同步-2026-08-19.md`;⚠️ 当前 8384 **未在监听**(Syncthing 未运行) |

> ⚠️ **2026-10-11 结构精简**:根 `scripts\`(临时脚本目录)、根 `input\`(本地测试素材约 11MB:HYWM2 示例场景 eth_courtyard/kitchen/workspace + 全景图)、根 `temp\`(验证用 db) **已全部删除**。临时脚本不再落盘进项目 —— 一次性逻辑用 stdin 就地执行(`.venv\Scripts\python.exe - <<'PY' ... PY`),需落盘时用系统临时目录;要能复跑的工具链统一放 `custom_nodes\ComfyUI-FallingTS\dev\`。⚠️ **注意区分**:`ComfyUI\input\`(用户上传)与 `ComfyUI\temp\` 是 ComfyUI 运行时的真实目录/软链,**不受本次调整影响**,`ComfyUI\input\`(软链→`media\<项目>\`)是真实数据严禁删。

## 工作流编号体系(35 个)

`workflows\` 共 35 个,按编号-用途分组:

| 组 | 工作流 |
|----|--------|
| `001x` 万物 | `0011_万物建模`(主线主流程)/ `0010_灰度遮罩` / `0012_万物变化` / **`0013_首图建模`(H3 I2VA,仿 `0031`)/ `0014_参考建模`(H3 REF2VA,仿 `0032`)/ `0015_建模截帧`(仿 `0035`)** —— 2026-10-07 新增的「H3 视频 → 抽帧 → 反推人物资产」一致性链,目标是跨**全部景别**(特写/近景/中景/全景)锁脸;数据表 `stories\七纹刻印\0013_首图建模.md` / `0014_参考建模.md`(0015 无表,自带加载节点);生成器 `custom_nodes\ComfyUI-FallingTS\dev\_build-0013-0015-modeling.py`(幂等,带表格与布局自检);提示词规范见技能 `stories` |
| └ `001x` 万物(拆分) | **`0016_建模拆图`(2026-10-07 新增, 无 md 数据表)**: **两套完全独立的节点流, 各一个 `FallingTSLoadImage`**(源图/序列号/名称/文件名前缀互不相干) —— 流一(四宫, 序列号 00001) `easy imageSplitGrid`(row/column 直接给**格数**) 2×2 → 4 个 `ImageFromBatch`(batch_index=i, length=1) → 4 个 `AutoSaveImage`(后缀 左上/右上/左下/右下); 流二(九宫, 序列号 00002) 3×3 → 9 个 `ImageFromBatch` → 9 个 `AutoSaveImage`(后缀 左上/上边/右上/左边/中间/右边/左下/下边/右下); 各流的文件名前缀取**自己**的加载节点 prefix 输出 ⇒ `00001_陈落_左上.png` 与 `00002_陈落_左上.png` 并存不互相覆盖(⚠️ 两个加载节点同目录, 「刷新序列号」取的都是该目录最大编号+1, 默认会拿到同一个号, 存档里已预置 00001/00002 错开, 要真错开请手改); 产物目录退回工作流名; 生成器 `custom_nodes\ComfyUI-FallingTS\dev\_build-0016-modeling-split.py`(幂等, 30 节点 / 41 连线, 连通分量恰为 2(10+10), 自带六规范 + 连线回填自检) |
| └ `001x` 万物(细节) | **`0017_建模细节`(2026-10-10 新增)**: 0016 拆图后的**局部细节精修** —— `FallingTSMarkDownTable`(原图 + 主-正词/主-负词)→ `ImageCropV2` 框选细节区域 → `LayerUtility: ImageScaleByAspectRatio V2` 放大到工作分辨率(长边 1024)→ Qwen-Image-Edit 一遍优化采样(4步/20步切换)→ `PreviewImageSave` 保存/预览 → `ImageCompare` 对比;结构克隆自 `0022_场景推镜`(顺带修掉 0022 的两处连线未回填 + 一处同列上下游违规 + 三处 <50px 边距);数据表 `stories\七纹刻印\0017_建模细节.md`(字段: ID / 原图(IMAGE) / 主-正词(TEXT) / 主-负词(TEXT); 原图引用 `@{0016_建模拆图/ID}`);生成器 `custom_nodes\ComfyUI-FallingTS\dev\_build-0017-modeling-detail.py`(幂等, 布局六规范 + 连线回填自检)。链路: 0011 万物建模 → 0016 建模拆图 → **0017 建模细节**(逐块精修) |
| `001x` 万物 QI2.1 | `00110_万物建模_QI2.1` / `00120_万物变化_QI2.1`(Qwen-Image 2.1 版,**共用 `001x` 的表**;见「Qwen-Image 2.1 工作流」) |
| `002x` 场景镜头 | `0020_场景首帧` / `0021_场景拉镜` / `0022_场景推镜` / `0023_场景旋镜` |
| `002x` 场景镜头 QI2.1 | `00200_场景首帧_QI2.1` / `00220_场景推镜_QI2.1`(Qwen-Image 2.1 版,**共用 `002x` 的表**) |
| `003x` 场景生成 | `0030_文生场景`(H3 T2VA,仅画面)/ `0031_首帧场景`(I2V)/ `0032_参考场景`(R2V 多图多视频参考)/ `0035_场景截帧`(**加载视频 → 截帧 → 8 单图 + 四图/八向合成自动保存**[2026-10-05 起十个保存节点统一为 `AutoSaveImage`]; 用自有插件新节点 `FallingTSLoadVideo`(加载视频: 来自输出 + 截帧 + 序列号/名称 + 保存帧 + 文件名前缀输出; **截帧不要求先跑过本节点** —— 帧缓存只在进程内存里, 缓存为空时(重启 ComfyUI / 刚选好或上传视频还没执行)截帧与保存帧路由按节点上选中的视频现场拆帧建缓存[懒解码]), 布局照 `0030_文生场景` 的「预览视频往后的所有节点」; 端口(视频/音轨/前缀)、十个保存节点的前缀分发(以及它们的 `AutoSaveImage` 归一)由 `custom_nodes\ComfyUI-FallingTS\dev\build-decompose-workflows.py` 的 `fix_0035()` 归一, 节点布局由同脚本的 `layout_0035()` 归一(四列网格: 加载 → 8 单图保存 → 2 合成 → 2 合成预览, 同列左对齐、行距 60、列距 80, 并参与六规范自检), 幂等 —— 原「从 0030 尾部搬运」的 `make-0035-scene.py` 已随 0030 清理尾部而退休) |
| └ `003x` 世界模型 | `0034_世界模型`(**360° 环绕视频 → 一个最高质量 3DGS PLY**;2026-09-28 由「md 表 8 图」改版为「md 表 360 视频」):`FallingTSMarkDownTable`(360环绕视频列)→ `WorldSurroundPanorama`(视频→**横向展开长图**(上行=天/无黑边/无重影) + valid_band + v_center; 2026-09-28 v2: 按画面位移自适应抽帧 + **自适应补密(治不均匀转速: 静止段/甩镜段)**、一圈闭环吸附(需首末帧几何重合)、逐像素 winner-take-all、近静止直接报错; 转速谱系 17 用例实测与四个已修静默缺陷见 `docs\360视频横向展开长图-v2实现-2026-09-28.md` §8)→ `PreviewImageSave`(长图预览支路)**与** `WorldPanoramaViews`(长图→视角批 + 精确 w2c 外参/内参, `v_range`/`v_center` 接长图元信息)→ `WorldRefinePLY`(视角批 + 相机先验 → 504 前馈 + 3DGS 全参数精修 mode=all reg=3.0, `gt=952`)→ `HYWM2PLYAdvancedGaussianViewer`;产物 `media\<项目>\0034_世界模型\0034_世界模型_世界3DGS.ply`。数据表 `stories\七纹刻印\0034_世界模型.md`;生成/改版脚本 `custom_nodes\ComfyUI-FallingTS\dev\_build-0034-world360.py`(幂等, 带六条布局规范自检), 验收脚本 `custom_nodes\ComfyUI-FallingTS\dev\_verify-0034-360.py` |
| `004x` 视频生成 | `0040_文生视频` / `0041_首帧视频` / `0042_首尾视频` / `0043_关键帧视频`(AddGuide 锚定任意帧)/ `0044_参考视频`。**2026-10-02 起这 5 个工作流的 PreviewVideo 之后的处理尾部全部清空** —— 截帧链(首帧/关键帧/尾帧 `PreviewImageSave`)、截音链(`FallingTSAudioTrim` + 三个 `PreviewAudioSave`)与分发文件名前缀的 `Reroute` 都已删除, 预览视频只留 `video` 输出、文件名前缀改由 MD 表 `ID` 直连(与 `0030`~`0032` 同口径); 拆帧/拆音各自归口到 `0050`/`0051` |
| `005x` 拆解 | `0050_视频截帧` / `0051_视频拆音`。**2026-10-02 起这两个工作流不要 md 数据表节点**(自带的加载节点下拉就是"起始的加载"): `0050` = `FallingTSLoadVideo`(下拉手选原视频, 也可用 `video_in`) → 截帧 → 三个 `AutoSaveImage`(图片自动保存, 执行即落盘、无「保存」按钮; 后缀区分首帧/关键帧/尾帧); `0051` = 同一个加载视频节点的 `audio` 输出(**拆音不需要截帧**, 不受「完成」门控) → `FallingTSAudioTrim` 波形截段 → 三个 `PreviewAudioSave`。文件名前缀一律取加载节点的 `prefix` 输出(「序列号_名称」, 一条线分发给本图所有预览/保存节点), 保存节点再用后缀区分(如 `00007_书房_首帧.png`); 因无 md 表, 产物目录退回工作流名。两个工作流都由 `custom_nodes\ComfyUI-FallingTS\dev\build-decompose-workflows.py` 生成(幂等, 连 0070 一起重建), 验收脚本 `_verify-005x-decompose.py` |
| `006x` 音频生成 | `0060_背景音乐` / `0061_环境音效` / `0062_效果音效` / `0063_文生人声` / `0064_参考人声` |
| `007x` 截取 | `0070_截取声音`(`FallingTSLoadAudio` 下拉手选音频(也可用 `audio_in`) → `FallingTSAudioTrim`「截取音频」波形截段 → 三个「截取音频预览」)。**2026-10-02 起去掉 md 数据表节点**: 文件名前缀 = 加载音频的 `prefix` 输出(「序列号_名称」), 一条线分发给截取音频与三个预览, 保存节点再用后缀区分; 产物目录退回工作流名。旧版的 `时长=结束-开始` + `TrimAudioDuration` + `PreviewAudio` + `SaveAudioAdvanced` 已由这条链取代(2026-10-02) |

## 数据流约定(工作流 ↔ md 表 ↔ 产物目录)

- **数据表**是工作流的参数来源:`FallingTSMarkDownTable` 节点读 `stories\<故事库>\<表名>.md`,按行 ID 取参数;`md_path` 指向具体表文件。
- **产物目录取表文件名**(优先):保存类节点用工作流的 **md 表文件名**(去 `.md`)作子目录,落 `media\<项目>\<表名>\`,如 `media\七纹刻印\0011_万物建模\`;工作流**没有 md 表节点**时退回**工作流名**。
- **跨表引用**写 `@{<表文件名>/<ID>}`,走**严格命中**(前缀即表文件名 = 产物目录名),不递归兜底。Qwen-Image 2.1 版与 1.x 版**共用**同一批表,故落同一目录、同 ID 产物**互相覆盖**只留一份。

## Qwen-Image 2.1 工作流(2026-09-21 建)

2.1 是 7B 统一"生成+编辑"模型(2026-09-20 发布), 与 2511/2512 **架构不兼容**(文本编码器换 Qwen3-VL 8B、VAE 换 64 通道 RGBA), 故旧 LoRA 全部不可用, 另建 4 个工作流并存而非替换原版:

| 工作流 | 对应原版 | 链路 |
|--------|----------|------|
| `00110_万物建模_QI2.1` | `0011_万物建模` | 两阶段: 文生图 → 带图编辑优化 |
| `00120_万物变化_QI2.1` | `0012_万物变化` | 单阶段: 图1/2/3 多图参考编辑 + 灰度遮罩局部重绘 |
| `00200_场景首帧_QI2.1` | `0020_场景首帧` | 两阶段: 文生场景 → 编辑优化 |
| `00220_场景推镜_QI2.1` | `0022_场景推镜` | 单阶段: 框选放大 → 编辑精修 |

⚠️ **2026-09-24 起这 4 个工作流与 1.x 版共用同一批数据表**:原 `00110/00120/00200/00220_*.md` 4 张表已删除,工作流内 `md_path` 一律指向 `0011_万物建模.md` / `0012_万物变化.md` / `0020_场景首帧.md` / `0022_场景推镜.md`。同名工作区分只靠文件名后缀 `_QI2.1`。**产物目录取表文件名**(2026-09-24 起保存类节点优先用工作流的 md 表文件名作子目录),故 4 个 QI2.1 工作流与各自 1.x 版**落同一个目录**(如 `media\七纹刻印\0011_万物建模\`)—— 同一行 ID 的产物互相覆盖,只保留一份;原 4 个 QI2.1 旧目录已于 2026-09-24 **改名并入**对应基础目录(`media\七纹刻印\0011_万物建模\` / `0012_万物变化\` / `0020_场景首帧\` / `0022_场景推镜\`),工作区内不再有任何带 QI2.1 的目录(各旧目录只含 1 个 PNG,且并入时基础目录尚不存在,故为纯改名、零冲突);`0044_参考视频.md` 里 3 处 `@{*_QI2.1/…}` 引用同步改为表名前缀。`0011_万物建模.md` 的现行版式见技能 `stories`（2026-10-17 起人物为「左脸部特写 + 右上三视图 + 右下手部特写」三块、1px 黑线分割；生物/物品仍三视图并排；尺寸固定 1920×1088，编辑链 ×1 直通）。

**关键差异(改这些工作流时注意)**:
- **不加载任何 LoRA**。2.1 无 4 步蒸馏 LoRA(LightX2V 的 Day-0 支持是框架级 fp8 优化, 不是 LoRA), 故步数按官方域设 **标准 30 步 / 加速 15 步**, cfg 固定 1.0; 原版"4 步 Lightning 档"已不存在
- 文本编码统一用 **`TextEncodeQwenImage21`** 一个节点同时产出 positive/negative(带参考图编码), 取代原版两个 `TextEncodeQwenImageEditPlus`; 其 `resolution` 默认 1024 控制参考图缩放
- 新增 **`QwenImage21Cache`**(接在 UNETLoader 之后)复用 KV 前缀, 编辑任务提速明显; 参数 `device=auto` / `dtype=default`
- latent 是 **64 通道**(旧版 16), 用 `EmptyLatentImage` 即可: `comfy/sample.py` 的 `fix_empty_latent_channels` 会把空 latent 自动扩展到模型通道数并按 `spacial_downscale_ratio`(16)修正分辨率
- 数据表与 1.x 版**共用**(不另建表):`stories\七纹刻印\0011_万物建模.md` 等 4 张;跨表引用写 `@{0011_万物建模/ID}`、`@{0020_场景首帧/ID}`(前缀是**表文件名**,也就是产物目录名 —— 保存类节点优先用工作流的 md 表文件名建子目录,引用因此走**严格命中**而非递归兜底)
- 布局由一套**幂等**的生成脚本产出(拓扑分层 + 双向重心法 + 差分约束求列偏移),4 个工作流各有入口;改完重跑即可,自检函数会校验六条布局规范。(⚠️ 这些生成脚本是可复跑工具,已随根 `scripts\` 临时目录一并移除,需要时现场重建)

## 官方文档与分类文档

- `refs\ComfyUI-Docs` 为官方文档本地克隆(在线源码 GitHub `Comfy-Org/docs`;2026-09-30 由 `docs\` 迁入 `refs\`);专题资料见 `webs\Bilibili\B站教程调研.md`(含 H3 专题)与 `webs\RunningHub\`(API 读取指南 / workflows-list.md)

## 开发规范

- **临时脚本不落盘进项目**:一次性调研/修改/校验逻辑优先用 stdin 就地执行(`.venv\Scripts\python.exe - <<'PY' ... PY`;Node 用 `node - <<'JS' ... JS`),确需落盘的临时文件用系统临时目录(`tempfile`);严禁在项目根目录或其它目录遗留 `_*.py` 之类临时文件。**要能复跑的工具链**一律放 `custom_nodes\ComfyUI-FallingTS\dev\`
- **项目根目录本身是一个 git 仓库**(`main`),子模块经 `.gitmodules` 登记、以**指针提交**(gitlink,模式 `160000`)跟踪;子模块改动在**子模块目录内** commit/push 后,再回根仓库 `git add <子模块路径>` 提交指针更新;不要留着子模块脏工作树,也不要往根仓库混入无关文件
- 修改 ComfyUI 主程序时遵守 `ComfyUI\AGENTS.md` 上游规范:改动小且直接、尽量少改文件、不引入新依赖、核心代码不发网络请求(见其 "No Internet Requests")、保持节点/API/工作流兼容、删除死代码、代码须看起来像手写
- 节点注册(V1 `NODE_CLASS_MAPPINGS` / V3 `comfy_entrypoint()`)与 ComfyUI API 使用约定见各插件仓库及 `ComfyUI\AGENTS.md`;代码书写规范(卫语句优先、switch 代替 if-else、缩进)与网络/代理策略见全局 `~/.claude\CLAUDE.md`

## 常见任务

- 修改工作流或重要文件前,先备份到 `backups\`,命名 `backup-<文件名>-<YYYYMMDD>-<说明>.json`;**备份一律放 `backups`,不要再放 `.claude\`**
- 新增/修改自定义节点:直接改对应子项目,经软链接即时生效,无需复制到 custom_nodes
- 验证节点加载:启动后查日志中 custom node 加载输出,或访问 `/object_info` 检查节点是否注册
- 挑选/运行工作流:先核对「模型与蓝图」(见 `comfyui` 技能 `workspace-env.md`)确认组件就位,再开 `blueprints\`、`templates\`(官方子目录)、`webs\Bilibili\工作流大全\`、`webs\RunningHub\workflows\` 的 json
- 清理临时输出残留:删 `ComfyUI\temp\` 里 `ComfyUI_temp_*.png` 后,「资产 → 已生成」仍显示属正常(任务历史 `GET /history` 的引用)。清理:`POST /history` + `{"clear": true}` 全清,或 `{"delete": ["<prompt_id>",...]}` 定向删;验证归零后前端 F5。⚠️ 清空前确认 history 输出均为 `temp` 类型,勿误清 output/input 真实数据

## 工作树现状(已知事项)

- `ComfyUI` 工作树含已删除的占位文件(`models/*/put_*_here` 等),属安装后正常现象,不要恢复或提交
- `custom_nodes\websocket_image_save.py` 与 `example_node.py.example` 是本地文件,不属于任何仓库;`__pycache__` 不入库
- `models\.cache\huggingface\download\<槽位>\*.safetensors.metadata` 是 ComfyUI 下载器写的元数据缓存(7 个文件),既未被 gitignore 也不入库(`git status` 里不显示, 属上游行为),**不要手工清理**,删了会让已下模型被判定为"需重新下载"
- `media`(input/output 软链目标)按项目分目录:`template\`(模板)+ `七纹刻印\`(当前项目, 软链指向);部分旧工作流引用的输入文件可能仍缺失,运行前核对
- ⚠️ **2026-10-11 复核时根仓库有较多未提交改动**(文档/工作流/子模块指针混在一起, 尚未落盘):`AGENTS.md`、`README.md`/`README.cn.md`、`.gitignore`、`.agents\skills\` 6 个技能、`docs\` 11 篇、`stories\AGENTS.md`、`webs\` 3 处、`workflows\` 6 个 json、`stories\template\` 3 个 md, 以及 `ComfyUI`/`custom_nodes\ComfyUI-FallingTS`/`ComfyUI-HYWM2`/`ComfyUI-RMBG`/`ComfyUI-ReservedVRAM`/`ComfyUI_UltimateSDUpscale`/`refs\minimax-h3-guide`/`stories\plugins\Obsidian-Comfy` 8 个子模块指针;`scripts\.gitignore` 为已删除未提交。提交前先确认各子模块**自身仓库内**已 commit/push

## Git 提交规范

我的插件中, 严格按照 `git add .` `commit` 最后推送
项目根目录中, 严格按照 `git add .` `commit` 最后推送
子项目除了我的插件是我自己写的, 其它所有子项目不允许提交和修改代码, 或者推送
