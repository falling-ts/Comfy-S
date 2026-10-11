# ComfyUI 本地工作区

ComfyUI 及自定义节点的本地开发工作区。下文路径均相对项目根目录,不绑定特定操作系统或 shell;文中命令示例按当前本机环境给出,部署到其它平台时按实际环境替换路径分隔符/可执行文件位置即可。

## 目录结构(展开至第二级)

| 路径 | 说明 |
|------|------|
| `ComfyUI` | ComfyUI 主程序(git submodule,detached HEAD 跟随上游 release tag,当前 `v0.39.2`):源码/入口在本目录;`models`/`input`/`output`/`user\default\workflows`/`custom_nodes` 均为相对软链接(见「软链接映射」);`blueprints\` 内置 116 个蓝图;其余结构遵循上游官方布局,不再逐一展开 |
| **`custom_nodes`** | **插件聚合目录**:45 个插件子模块 + `H3ReferenceSuite` 链接集中于此,`ComfyUI\custom_nodes` 为目录级相对软链接指向它(§B)。按功能归类: |
| └ 自有插件 | `ComfyUI-FallingTS`:通用工具节点集(共 **22 节点** + 27 个前端增强,已开源);另含**世界模型三节点**:`world-panorama` 的 `WorldSurroundPanorama`(**360° 环绕视频 → 横向展开长图**(等距圆柱条带, 上行=天、无黑边、无重影): 自动定抽帧步长 + 一圈闭环吸附 + ORB/RANSAC 纯偏航单应与「重叠区稠密光度一致性」联立定焦距 + 逐像素 winner-take-all(从不帧间平均), 真 equirect 视频可直接抽帧; 2026-09-28 v2 重做同时修掉 v1 的「长图倒立 + 上下各 30% 黑边 + 帧间平均糊掉细节(拉普拉斯锐度差 4.3 倍)」)、`WorldPanoramaViews`(长图 → 视角批 + **每视角精确 w2c 外参/内参**, 外参口径与 HYWM2 `SamplePanorama` 一致; 等距圆柱竖直朝向按世界地图口径修正, 多 `v_range`/`v_center` 竖向范围), 以及 `world-refine` 的 `WorldRefinePLY`(视角批(可接相机先验) → 504 前馈 + 3DGS **全参数**精修(mode=all + 几何信任域) → 一个 PLY; 接上 `extrinsics/intrinsics` 时把位姿作为先验注入前馈 `cond_flags=[cam,0,intr]`, 从源头消掉上游推理不做跨视图融合留下的多视图双重曝光/重影。2026-09-28 并入并扩到「360 视频进、PLY 出」) |
| └ H3 生态(6 插件 + 链接) | `ComfyUI-Spectrum-MiniMax-H3`(加速)、`ComfyUI-SolAttn_triton`(注意力加速)、`ComfyUI-ReservedVRAM`(显存预留)、`ComfyUI-Qwen3-TTS`(H3 语音)、`h3-latent-upscaler`(latent 放大)、`ComfyUI-OrbitSheets`(场景/角色参考板:锚点图 + H3 多视角运镜 + 视觉选帧拼网格图,2026-08-17 装)、`H3ReferenceSuite`(软链接,见 `refs`) |
| └ 放大/修复/局部重绘 | `ComfyUI-SeedVR2_VideoUpscaler`(视频高清修复)、`ComfyUI-SUPIR`(超分放大)、`ComfyUI_UltimateSDUpscale`(分块重绘)、`ComfyUI-Impact-Pack`(Detailer 局部精修)、`ComfyUI_LayerStyle`(图层/遮罩)、`ComfyUI-Inpaint-CropAndStitch`(裁剪贴回) |
| └ 视频 | `ComfyUI-VideoHelperSuite`、`ComfyUI-WanVideoWrapper`、`ComfyUI-Frame-Interpolation`(补帧)、`ComfyUI-qwenmultiangle`(Qwen 多镜头) |
| └ 3D/世界模型 | `ComfyUI-HYWM2`(HY-World 2.0 世界重建: 8 视图 → 统一世界坐标三维场景 → 3DGS/点云/网格 + PLY 视口; 权重在 `models\hywm2`(3.05GB, 已按槽位约定 gitignore); 隔离环境 `hywm2-nodes`, gsplat 在那 ⇒ 0034 的 `WorldRefinePLY` 借它跑精修。2026-09-27 装, **2026-09-28 登记为 git 子模块**(`[submodule "ComfyUI-HYWM2"]`, branch main, 指针 `93d060e`); ⚠️ `nodes/comfy-env.toml` 有**故意不提交**的本地补丁(`requests` + `comfy-kitchen==0.2.35`), **没留档** —— `backups\` 已于 2026-09-30 清空, 而 `submodule update` 会覆盖它 ⇒ 更新前先自己复制一份该文件) |
| └ 图像/编辑/生成 | `ComfyUI-Easy-Use`、`ComfyUI_IPAdapter_plus`、`ComfyUI-ReActor`(换脸)、`ComfyUI-RMBG`、`ComfyUI-segment-anything-2`、`comfyui_controlnet_aux`、`ComfyUI-IC-Light`、`ComfyUI-DepthAnythingV2`、`Comfyui-QwenEditUtils`、`comfyui-mixlab-nodes`、`ComfyUI-Florence2`、`ComfyUI-post-processing-nodes`(后期处理) |
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
| **`workflows`** | **用户工作流实际存储处**(前端保存即在此,可经 `GET /userdata?dir=workflows` 读取),共 35 个,按编号-用途分组: |
| └ `001x` 万物 | `0011_万物建模`(主线主流程)/ `0010_灰度遮罩` / `0012_万物变化` / **`0013_首图建模`(H3 I2VA,仿 `0031`)/ `0014_参考建模`(H3 REF2VA,仿 `0032`)/ `0015_建模截帧`(仿 `0035`)** —— 2026-10-07 新增的「H3 视频 → 抽帧 → 反推人物资产」一致性链,目标是跨**全部景别**(特写/近景/中景/全景)锁脸;数据表 `stories\七纹刻印\0013_首图建模.md` / `0014_参考建模.md`(0015 无表,自带加载节点);生成器 `custom_nodes\ComfyUI-FallingTS\dev\_build-0013-0015-modeling.py`(幂等,带表格与布局自检);提示词规范见技能 `stories-video-prompts`。<br>**`0016_建模拆图`(2026-10-07 新增, 无 md 数据表)**: **两套完全独立的节点流, 各一个 `FallingTSLoadImage`**(源图/序列号/名称/文件名前缀互不相干) —— 流一(四宫, 序列号 00001) `easy imageSplitGrid`(row/column 直接给**格数**) 2×2 → 4 个 `ImageFromBatch`(batch_index=i, length=1) → 4 个 `AutoSaveImage`(后缀 左上/右上/左下/右下); 流二(九宫, 序列号 00002) 3×3 → 9 个 `ImageFromBatch` → 9 个 `AutoSaveImage`(后缀 左上/上边/右上/左边/中间/右边/左下/下边/右下); 各流的文件名前缀取**自己**的加载节点 prefix 输出 ⇒ `00001_陈落_左上.png` 与 `00002_陈落_左上.png` 并存不互相覆盖(⚠️ 两个加载节点同目录, 「刷新序列号」取的都是该目录最大编号+1, 默认会拿到同一个号, 存档里已预置 00001/00002 错开, 要真错开请手改); 产物目录退回工作流名; 生成器 `custom_nodes\ComfyUI-FallingTS\dev\_build-0016-modeling-split.py`(幂等, 30 节点 / 41 连线, 连通分量恰为 2(10+10), 自带六规范 + 连线回填自检) |
| └ `001x` 万物(细节) | **`0017_建模细节`(2026-10-10 新增)**: 0016 拆图后的**局部细节精修** —— `FallingTSMarkDownTable`(原图 + 主-正词/主-负词)→ `ImageCropV2` 框选细节区域 → `LayerUtility: ImageScaleByAspectRatio V2` 放大到工作分辨率(长边 1024)→ Qwen-Image-Edit 一遍优化采样(4步/20步切换)→ `PreviewImageSave` 保存/预览 → `ImageCompare` 对比;结构克隆自 `0022_场景推镜`(顺带修掉 0022 的两处连线未回填 + 一处同列上下游违规 + 三处 <50px 边距);数据表 `stories\七纹刻印\0017_建模细节.md`(字段: ID / 原图(IMAGE) / 主-正词(TEXT) / 主-负词(TEXT); 原图引用 `@{0016_建模拆图/ID}`);生成器 `custom_nodes\ComfyUI-FallingTS\dev\_build-0017-modeling-detail.py`(幂等, 布局六规范 + 连线回填自检)。链路: 0011 万物建模 → 0016 建模拆图 → **0017 建模细节**(逐块精修) |
| └ `001x` 万物 QI2.1 | `00110_万物建模_QI2.1` / `00120_万物变化_QI2.1`(Qwen-Image 2.1 版,**共用 `001x` 的表**;见「Qwen-Image 2.1 工作流」) |
| └ `002x` 场景镜头 | `0020_场景首帧` / `0021_场景拉镜` / `0022_场景推镜` / `0023_场景旋镜` |
| └ `002x` 场景镜头 QI2.1 | `00200_场景首帧_QI2.1` / `00220_场景推镜_QI2.1`(Qwen-Image 2.1 版,**共用 `002x` 的表**) |
| └ `003x` 场景生成 | `0030_文生场景`(H3 T2VA,仅画面)/ `0031_首帧场景`(I2V)/ `0032_参考场景`(R2V 多图多视频参考)/ `0033_OrbitSheets场景`(Location Sheet 参考板:锚点图+H3 多视角选帧拼板)/ `0035_场景截帧`(**加载视频 → 截帧 → 8 单图 + 四图/八向合成自动保存**[2026-10-05 起十个保存节点统一为 `AutoSaveImage`]; 用自有插件新节点 `FallingTSLoadVideo`(加载视频: 来自输出 + 截帧 + 序列号/名称 + 保存帧 + 文件名前缀输出; **截帧不要求先跑过本节点** —— 帧缓存只在进程内存里, 缓存为空时(重启 ComfyUI / 刚选好或上传视频还没执行)截帧与保存帧路由按节点上选中的视频现场拆帧建缓存[懒解码]), 布局照 `0030_文生场景` 的「预览视频往后的所有节点」; 端口(视频/音轨/前缀)、十个保存节点的前缀分发(以及它们的 `AutoSaveImage` 归一)由 `custom_nodes\ComfyUI-FallingTS\dev\build-decompose-workflows.py` 的 `fix_0035()` 归一, 节点布局由同脚本的 `layout_0035()` 归一(四列网格: 加载 → 8 单图保存 → 2 合成 → 2 合成预览, 同列左对齐、行距 60、列距 80, 并参与六规范自检), 幂等 —— 原「从 0030 尾部搬运」的 `make-0035-scene.py` 已随 0030 清理尾部而退休) |
| └ `003x` 世界模型 | `0034_世界模型`(**360° 环绕视频 → 一个最高质量 3DGS PLY**;2026-09-28 由「md 表 8 图」改版为「md 表 360 视频」):`FallingTSMarkDownTable`(360环绕视频列)→ `WorldSurroundPanorama`(视频→**横向展开长图**(上行=天/无黑边/无重影) + valid_band + v_center; 2026-09-28 v2: 按画面位移自适应抽帧 + **自适应补密(治不均匀转速: 静止段/甩镜段)**、一圈闭环吸附(需首末帧几何重合)、逐像素 winner-take-all、近静止直接报错; 转速谱系 17 用例实测与四个已修静默缺陷见 `docs\360视频横向展开长图-v2实现-2026-09-28.md` §8)→ `PreviewImageSave`(长图预览支路)**与** `WorldPanoramaViews`(长图→视角批 + 精确 w2c 外参/内参, `v_range`/`v_center` 接长图元信息)→ `WorldRefinePLY`(视角批 + 相机先验 → 504 前馈 + 3DGS 全参数精修 mode=all reg=3.0, `gt=952`)→ `HYWM2PLYAdvancedGaussianViewer`;产物 `media\<项目>\0034_世界模型\0034_世界模型_世界3DGS.ply`。数据表 `stories\七纹刻印\0034_世界模型.md`;生成/改版脚本 `custom_nodes\ComfyUI-FallingTS\dev\_build-0034-world360.py`(幂等, 带六条布局规范自检), 验收脚本 `custom_nodes\ComfyUI-FallingTS\dev\_verify-0034-360.py` |
| └ `004x` 视频生成 | `0040_文生视频` / `0041_首帧视频` / `0042_首尾视频` / `0043_关键帧视频`(AddGuide 锚定任意帧)/ `0044_参考视频`。**2026-10-02 起这 5 个工作流的 PreviewVideo 之后的处理尾部全部清空** —— 截帧链(首帧/关键帧/尾帧 `PreviewImageSave`)、截音链(`FallingTSAudioTrim` + 三个 `PreviewAudioSave`)与分发文件名前缀的 `Reroute` 都已删除, 预览视频只留 `video` 输出、文件名前缀改由 MD 表 `ID` 直连(与 `0030`~`0032` 同口径); 拆帧/拆音各自归口到 `0050`/`0051` |
| └ `005x` 拆解 | `0050_视频截帧` / `0051_视频拆音`。**2026-10-02 起这两个工作流不要 md 数据表节点**(自带的加载节点下拉就是"起始的加载"): `0050` = `FallingTSLoadVideo`(下拉手选原视频, 也可用 `video_in`) → 截帧 → 三个 `AutoSaveImage`(图片自动保存, 执行即落盘、无「保存」按钮; 后缀区分首帧/关键帧/尾帧); `0051` = 同一个加载视频节点的 `audio` 输出(**拆音不需要截帧**, 不受「完成」门控) → `FallingTSAudioTrim` 波形截段 → 三个 `PreviewAudioSave`。文件名前缀一律取加载节点的 `prefix` 输出(「序列号_名称」, 一条线分发给本图所有预览/保存节点), 保存节点再用后缀区分(如 `00007_书房_首帧.png`); 因无 md 表, 产物目录退回工作流名。两个工作流都由 `custom_nodes\ComfyUI-FallingTS\dev\build-decompose-workflows.py` 生成(幂等, 连 0070 一起重建), 验收脚本 `_verify-005x-decompose.py` |
| └ `006x` 音频生成 | `0060_背景音乐` / `0061_环境音效` / `0062_效果音效` / `0063_文生人声` / `0064_参考人声` |
| └ `007x` 截取 | `0070_截取声音`(`FallingTSLoadAudio` 下拉手选音频(也可用 `audio_in`) → `FallingTSAudioTrim`「截取音频」波形截段 → 三个「截取音频预览」)。**2026-10-02 起去掉 md 数据表节点**: 文件名前缀 = 加载音频的 `prefix` 输出(「序列号_名称」), 一条线分发给截取音频与三个预览, 保存节点再用后缀区分; 产物目录退回工作流名。旧版的 `时长=结束-开始` + `TrimAudioDuration` + `PreviewAudio` + `SaveAudioAdvanced` 已由这条链取代(2026-10-02) |
| `models` | 模型实际存放处(`ComfyUI\models` 软链接指向);38 个标准槽位子目录,每个目录带 `.gitignore`(内容 `*`+`!.gitignore`)忽略模型文件、仅占位入库。已就绪模型见「模型与蓝图」 |
| └ 核心生成 | `diffusion_models` / `text_encoders` / `vae` / `loras` / `checkpoints` / `upscale_models` / `background_removal`(已就绪) |
| └ 语音 | `TTS`(Qwen3-TTS 五变体 + SenseVoice)/ `ASR` / `speaker_models` / `audio_encoders` |
| └ 标准空槽位 | 其余 25 个标准槽位目录(如 `controlnet` / `clip` / `clip_vision` / `unet` / `embeddings` / `detection` / `SEEDVR2` / `ultralytics` 等,多数尚未放置模型) |
| `media` | 输入/输出文件(`ComfyUI\input`、`output` 软链接到 `media\七纹刻印`):按**项目**分目录——`template\`(模板, 入库占位)+ 各故事库目录(如 `七纹刻印\`, 实际产物, 不入库);input/output 指向哪个项目, 产物就落在哪个项目目录下 |
| `templates` | ComfyUI 官方模板库本地缓存(**833 个工作流 JSON**,2026-10-10 随模板包 0.11.78 更新):14 个分类子目录——官方核心 598 个分 11 类(`图像`198/`视频`197/`图像工具`46/`3D模型`43/`音频`33/`视频工具`25/`LLM`20/`角色与时尚`12/`产品与广告`11/`品牌与设计`8/`节点基础`5),另有 `自定义节点\`218 个(按插件分子目录)+ `快速开始\`10 个、`矢量\`7 个(本地补遗);`workflow-templates-list.md` 为索引,由 `scripts\pull-templates.py` 重建(2026-08-09 曾归档的个人工作流已迁回 `workflows\`) |
| `webs` | 三方网站调研聚合目录(已入库跟踪):三个调研源 |
| └ `RunningHub` | RunningHub 调研:`RunningHub-API读取指南.md` + `workflows-list.md` + `workflows\`(2522 个收集工作流,按 21 个分类子目录:图像/视频/音频/数字人/室内外设计/风格化/插件 等) |
| └ `Bilibili` | B 站教程调研:`B站教程调研.md` + `工作流大全\`(474 个配套工作流) |
| └ `AutoDL` | 云端 GPU 调研:`AutoDL-GPU选型-2026-08-06.md` + `api.md`(云模型库接口)+ `models.md`(4887 条模型清单) |
| `stories` | Obsidian 故事写作工作区(自带 `.obsidian\` 配置 + 插件安装位相对软链,见「软链接映射 §D」):**`plugins\`**(插件聚合目录,与 ComfyUI 侧 `custom_nodes` 同构:含 `Obsidian-Comfy` 一个插件子模块,目录名即线上仓库名;该插件自带文件浏览器「编号分层」排序)+ `template\`(新建故事模板)+ 用户自定义故事库目录(库名随写作项目而定,以盘上实际为准) |
| `scripts` | **纯临时目录**(被 `scripts\.gitignore` 忽略:`*` + `!.gitignore`,仅存本地不入库):一次性调研/探针/校验脚本、实验产物、缓存、prompt 转储等,**随时可整体清空**(2026-09-30 已清空一次:71 项 / 983.5 MB 进回收站)。⚠️ **要能复跑的工具链不放这里** —— 2026-09-30 起这类脚本已迁入 `custom_nodes\ComfyUI-FallingTS\dev\`(47 个:0034 世界模型生成/验收、world-panorama 展开的合成真值/转速谱系/方位对拍、运行前命令自检、0050/0051/0070/0035 的生成与验收);插件的**运行期硬依赖**则放在使用它的节点旁边(`custom_nodes\ComfyUI-FallingTS\world-refine\refine_0034_gs.py`) |
| `logs` | ComfyUI 运行日志(`comfyui*.log`/`comfyui-console*.log`,已 gitignore) |
| `backups` | **工作流/重要文件的修改前备份**(2026-08-04 起):`backup-<文件名>-<YYYYMMDD>-<说明>.*` 命名;**纯本地暂存目录** —— `.gitignore` 忽略全部内容(只有 `.gitignore` 本身入库), **可随时整体清空、不承担归档职责**:环境快照(pip-freeze/conda export)、本地 wheel、文档归档一律不留档, 需要时现场重建(`pip freeze`/重新下载);2026-09-30 已全清一次(1646 文件 / 372.8 MB 直接删除) |
| `.claude` | SymbolicLink → `.agents`(Claude Code 兼容垫片,技能聚合目录,见「软链接映射 §C」) |
| `README.md` / `LICENSE` | 项目说明与许可 |
| `.gitmodules` | 子模块登记(git submodule) |
| `comfy-server.sh` | **统一**后台服务式启动脚本(跨平台: Linux + Windows Git Bash;杀 8188 旧进程 → 静默后台启动 → 等待端口就绪,日志默认写调用时所在目录 `comfy-server-8188.log`;Windows 等价 `python main.py --enable-manager --disable-pinned-memory --fast-disk`,Linux 用 conda 环境 comfy + `--reserve-vram 22`;覆盖 `PORT`/`WAIT`/`PY_BIN`/`LOG`/`RESERVE_VRAM`) |

## 软链接映射(重要,共 8 个,全部为相对路径 SymbolicLink;2026-08-07 建,08-10 插件收敛为目录级链接,08-13 加 Claude Code 兼容链接,09-20 加 Obsidian 插件安装位,09-22 安装位改「聚合目录 + 单层软链」,插件本体为聚合目录内的真实子模块)

全部为 **相对路径**符号链接,**项目根目录整体移动后不失效**(不依赖具体文件系统/平台)。

### A. 基础链接(4 个)

| ComfyUI 内路径 | 类型 | 相对目标 | 实际指向 |
|------|------|------|------|
| `ComfyUI\input` | SymbolicLink | `..\media\七纹刻印` | `media\七纹刻印`(当前项目) |
| `ComfyUI\output` | SymbolicLink | `..\media\七纹刻印` | `media\七纹刻印`(当前项目) |
| `ComfyUI\models` | SymbolicLink | `..\models` | `models`(模型实际存放处) |
| `ComfyUI\user\default\workflows` | SymbolicLink | `..\..\..\workflows` | `workflows`(用户工作流实际存储处) |

### B. custom_nodes 目录级链接 + H3ReferenceSuite 子链接(2 个)

| ComfyUI 内路径 | 类型 | 相对目标 | 实际指向 |
|------|------|------|------|
| `ComfyUI\custom_nodes` | SymbolicLink(目录级) | `..\custom_nodes` | 根 `custom_nodes`(插件聚合目录,45 插件 + H3ReferenceSuite 链接) |
| `custom_nodes\H3ReferenceSuite` | SymbolicLink(子链接) | `..\refs\minimax-h3-guide\custom_nodes\H3ReferenceSuite` | `refs\minimax-h3-guide\custom_nodes\H3ReferenceSuite`(2026-09-30 由 `h3\` 迁来;盘上必须写**反斜杠**目标 —— 实测 reparse 目标里的正斜杠解析失败 WinError 123,而 git 入库时会统一规范成正斜杠 `../refs/...`) |

- 根 `custom_nodes` 由**根仓库**跟踪:45 个插件以 gitlink 形式登记(全仓共 54 个子模块:`ComfyUI` 1 + `custom_nodes\` 45 + `refs\` 7 + `stories\plugins\Obsidian-Comfy` 1;`.gitmodules` 条目数同为 54,2026-09-30 搬迁后复核一致 —— 其中 `ComfyUI-HYWM2` 是 2026-09-28 新登记的,`refs\` 7 个是 2026-09-30 由 `docs\`(5)+`h3\`(2)迁入的),`H3ReferenceSuite` 为符号链接;本地文件 `example_node.py.example`、`websocket_image_save.py` 被根 `.gitignore` 排除(保留磁盘副本供加载)。`ComfyUI\custom_nodes` 是目录级符号链接,其目标内容不受 ComfyUI 子模块 git 影响
- `ComfyUI\temp\`(真实目录,非链接):运行中生成的临时文件/预览图(如 `ComfyUI_temp_*.png`),可随时清理
- ⚠️ **`ComfyUI\input\`(用户上传)与 `output\`(生成结果)是真实数据所在(经软链落入 `media\<项目>\`):严禁整体删除、移动或批量清理**;只有 `temp\` 可清理

### C. 根目录 Claude Code 兼容链接(1 个)

| 根内路径 | 类型 | 相对目标 | 实际指向 |
|------|------|------|------|
| `.claude` | SymbolicLink(目录级) | `.agents` | 根 `.agents`(技能聚合目录,Claude Code 兼容垫片,2026-08-13 建) |

### D. stories Obsidian 插件安装位(1 个软链 + 1 个插件子模块,**入库跟踪**;2026-09-22 改为「聚合目录 + 单层软链」)

与 ComfyUI 侧 `custom_nodes` 同构:vault 内 `.obsidian\plugins` 只是一个**指向聚合目录的链接**,插件本体是 `stories\plugins\` 下的**真实 git 子模块**(目录名与线上仓库名一致;⚠️ Obsidian 认的是插件 `manifest.json` 里的 `id`,**与目录名无关**,故 `Obsidian-Comfy\` 内 `manifest.json` 的 `id` 仍是小写 `obsidian-comfy`,`community-plugins.json` 里也照旧写小写 id)。

| 根内路径 | 类型 | 相对目标 | 实际指向 |
|------|------|------|------|
| `stories\.obsidian\plugins` | SymbolicLink(目录级) | `..\plugins` | `stories\plugins`(插件聚合目录) |

- **聚合目录内容**(`stories\plugins\`,**单个真实子模块,内无软链**):`Obsidian-Comfy`(远程 `falling-ts/Obsidian-Comfy`,2026-09-22 由 `stories\Obsidian-Comfy` 直接移入,同日目录名首字母改为大写以与线上仓库名对齐;同日接管文件浏览器排序)
- ⚠️ **2026-09-22 卸载了第三方排序插件 custom-sort**:`SebastianMC/obsidian-custom-sort` 3.2.0(最新版)在 Obsidian 1.13.7 上解析 `sortspec.md` 的 YAML frontmatter 失败并自动挂起(ribbon 显示红图标 `ICON_SORT_SUSPENDED_SYNTAX_ERROR`),根因是 Obsidian 把块标量内容**连同缩进**交给插件,而它对 `target-folder:` 行要求前导零空格;`|` 块标量写法与官方文档示例的 1 空格缩进写法**均失败**。子模块已 deinit + rm,`.gitmodules` / 根 `.git/config` / `.git/modules` 均无残留,`community-plugins.json` 只剩 `obsidian-comfy`;vault 根的 `sortspec.md` 亦一并删除(其内容要点已并入本节)
- **为什么只要一层软链**:Obsidian 只从 vault 的 `.obsidian\plugins\<id>\` 加载插件,而插件源码本就放在同级的 `stories\plugins\` —— 把 `.obsidian\plugins` 指向它即可,插件目录**直接就是子模块本体**(与 `custom_nodes\` 里各插件完全同构);再给 `Obsidian-Comfy` 套一层安装位软链是多余的(源码与聚合目录同层,不存在跨目录引用)
- **入库方式**(与 A、B 组不同,本组**入库跟踪**):`stories\.gitignore` 首行 `*` 通配后逐条放行 —— `!.obsidian/plugins`(整目录软链)、`!plugins/`、`!plugins/Obsidian-Comfy`(子模块);另按「Obsidian 维护的用户数据不入库」忽略 `.obsidian/workspace.json` 与 `.obsidian/bookmarks.json`。⚠️ 放行**目录本身**即可:子模块内部文件由各自仓库管理,不递归放行。根仓库入库的相对软链共 **3** 个:`.claude`、`custom_nodes\H3ReferenceSuite`、本组一条(mode `120000`)
- **文件浏览器排序**(2026-09-22 起由自有插件 `Obsidian-Comfy` 接管):`main.js` 的 `setupExplorerSort()` 替换 FileExplorer 原型上的 `getSortedFolderItems`,保留 Obsidian 原实现的「文件夹优先 + 从 `this.fileItems` 取回渲染项」骨架,只换比较器 —— 故不依赖 items 内部结构,视图重建也不会掉。规则是**编号分层**(`compareNumberedName`):开头数字串按**字符串**比较(短的优先),于是 `0011_万物建模` → `00110_万物建模_QI2.1` → `0012_万物变化`,5 位编号恰好插在它所属的 4 位编号之后。⚠️ **纯逐字节做不到这个顺序**:字符串比较里 `_`(0x5F) 大于 `1`(0x31),会把 `00110` 排到 `0011` **前面**。开关在插件设置页「文件浏览器排序」(编号分层 / 纯逐字节 / 关闭),改完即时生效,无需重启(排序规则的完整说明见本节)
- ⚠️ **clone 端约束 —— `core.symlinks` 是本地配置、不入库,新机器必须自己配**:
  - Windows:`git config core.symlinks true`,**且该机要有建链权限**(开发者模式或管理员);否则 git 会把链接检出成写着 `..\plugins` 的**普通文本文件**,Obsidian 认不出插件。本机 local 已设 `true`(原 local 为 `false`,会覆盖 global 的 `true`;system 亦为 `false`)
  - Linux/macOS:默认 `core.symlinks=true`,无需配置
  - 子模块需初始化:`git submodule update --init stories/plugins/Obsidian-Comfy`,否则插件目录为空(git 层面仍正确,只是插件无源码)
- 相对目标以**链接自身所在目录**为基准解析,故仓库 clone 到任意绝对路径都直接生效;git 存储时统一规范为正斜杠(`../plugins`),checkout 时转回平台分隔符
- **建链只能用 Python `os.symlink`**:PowerShell `New-Item` 会把相对 target 按 cwd 解析(建出 `D:\media\...` 之类错误目标),同 `scripts\link-media-dirs.py` 注释所述。本组软链由 `scripts\link-obsidian-plugins.py` 建立(**幂等**,可重复执行;已改为只建 `.obsidian\plugins` 这**一条**,不再生成 Obsidian-Comfy 安装位软链)。验证口径:`(Get-Item <路径>).LinkType` 为 `SymbolicLink`、`Target` 为相对串、且经链接能读到 `main.js`
- ⚠️ **移动 git 子模块时慎用 `git mv`,且搬运前先关掉会占用它的程序**(实测 2026-09-22:Obsidian 开着时移 `stories\Obsidian-Comfy` 报 `Permission denied`,随后 `Move-Item` 只完成一半 —— 工作树连 `.git` 目录一起被搬走,旧位置只留一个**空** `.git` 目录,而 `.git/modules/stories/<name>` 已不存在,子模块暂时"内联"成独立仓库,`git status` 因该空壳报 `not recognized as a git repository`)。完整修复三步:① `Move-Item <新位置>\.git` → `.git/modules/stories/plugins/<name>`(其 config 通常**没有** `core.worktree`,不必改;默认按 gitdir 反推 worktree 恰好正确);② 写回 `.git` **文件**(内容 `gitdir: ../../../.git/modules/stories/plugins/<name>`,无 BOM);③ 同步 `.gitmodules` 与根 `.git/config` 里该子模块的 **name 与 path**。完成后 `git submodule status` 显示 ` <hash> <path> (heads/<分支>)`(前导空格 = 已初始化且与 index 一致)

## 版本与运行

- **Python 虚拟环境:项目内 `.venv`**(2026-08-16 由 conda 环境迁移而来,官方 `python -m venv` 基于系统 Python 3.13.13 创建;原 conda 专用环境已删除)。启动一律用 `.venv\Scripts\python.exe`(类 Unix 为 `.venv\bin/python`),不要用系统级 Python 或任何 conda 环境运行主程序
- **运行环境 `.venv`:Python 3.13.13 / torch 2.13.0+cu130(CUDA 13.0,RTX 4060 8GB VRAM)**,启动脚本与本文档均用它(`.venv\Scripts\python.exe`,类 Unix 为 `.venv\bin/python`);依赖安装顺序:torch(cu130 index)→ `ComfyUI\requirements.txt` → 插件 requirements → 加速依赖,迁移后与旧 conda 环境包版本对齐(当时的 conda/venv `pip freeze` 快照已随 `backups\` 清空, 要比对就现场 `pip freeze` 生成)
- 共享关键版本(均与核心 v0.39.2 `requirements.txt` 钉定版本一致):comfyui-frontend-package **1.53.10**、comfyui-manager **4.2.2**、comfyui-workflow-templates **0.11.78**、comfyui-embedded-docs **0.5.13**、comfy-aimdo **0.5.5**、comfy-kitchen **0.2.37**、sageattention **2.2.0**(cu130;本地 wheel 已不留档)、triton **3.7.1**、transformers 4.57.3、diffusers 0.39.0、numpy 2.2.6(受 opencv 4.12 依赖约束 `numpy<2.3`,勿升回 2.5.x)、opencv-python/opencv-contrib-python/opencv-python-headless 4.12.0.88(ComfyUI-LNL 声明 `opencv-python~=4.12.0`)、onnxruntime-gpu 1.29.0、safetensors 0.8.0
- **核心升级流程**(2026-09-21 由 v0.36.0 → v0.37.0 实践; 2026-10 已升至 **v0.39.2**):`git -C ComfyUI fetch --tags` → 查最新 tag → `git checkout <tag>`(detached;工作树里被删的上游占位文件不受影响,不会冲突) → 按 `requirements.txt` 差异补装依赖 → 重启 → `custom_nodes\ComfyUI-FallingTS\dev\_check-workflow-node-compat.py` 验证工作流用到的节点类型全部仍注册 → 根仓库提交子模块指针。升级前先 `pip freeze` 备份到 `backups\`
- **升级兼容性判据**:前端内置节点(`Note`/`MarkdownNote`/`Reroute`/`PrimitiveNode`)与前端注册的 UUID 型 API 节点**不出现**在后端 `/object_info` 里,比对时须白名单排除(脚本已内置),否则每次升级都会误报缺失
- **插件更新流程**(2026-09-21 实践,44 个插件仓库):逐个 `git -C custom_nodes/<插件> fetch --tags --prune` → `git rev-list --count HEAD..origin/<默认分支>` 看落后数 → 在分支上的 `git merge --ff-only origin/<分支>`,**detached HEAD 的** `git checkout <默认分支>`(自动建跟踪分支并到位) → `git diff <旧> <新> -- requirements.txt` 判断是否补装依赖 → 含 `.gitmodules` 的插件(`ComfyUI-Easy-Use`/`ComfyUI-Impact-Pack`/`ComfyUI_UltimateSDUpscale`)再 `git submodule update --init --recursive` → 重启 → 跑 `_check-workflow-node-compat.py`。⚠️ **只更新本地,不推送**(上游子项目禁止提交/推送);更新前先确认各插件 `Ahead=0`,否则会覆盖本地提交
- **模板库更新**:跑 `scripts\pull-templates.py`,它从**运行中的服务**拉 `GET /templates/index.zh.json`(官方核心,按中文 `title` 归入 `templates\<分类>\`)+ `GET /api/workflow_templates`(插件模板 → `自定义节点\<插件>\`),增量写入并重建 `workflow-templates-list.md`;版本号由 `/system_stats` 与 pip 包**动态读取**(勿再硬编码)。脚本**不删除**已下线文件,只在末尾列出供人工判断(2026-09-21 遇到 `图像工具/api_flux_vto.json` 已从索引移除,备份到 `backups\` 后删除)
- **pip 默认走清华镜像**(`pypi.tuna.tsinghua.edu.cn`,配置在 `%APPDATA%\pip\pip.ini`):上游刚发布的包镜像可能尚未同步(实测 `comfyui-workflow-templates-media-assets-02==0.1.3` 上传 19 小时后仍查不到,报 `No matching distribution found`),此时临时加 `--index-url https://pypi.org/simple` 走官方源直连即可
- 前端打包目录 = `<venv>/Lib/site-packages/comfyui_frontend_package/static/`:主入口 `index.html`,打包产物 `assets\`;插件 `web\js` 经 `GET /extensions` 运行时加载、**不参与前端打包**(重建 `assets\` 不影响扩展;`scripts\` 保留 `app.js`/`api.js` 等扩展 import 入口)
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

## 模型与蓝图(2026-08-19 现状)

模型实际存放在 `models\` 下(`ComfyUI\models` 为软链接),当前合计约 189.1 GB。已就绪:

| 目录 | 已就绪 |
|------|--------|
| diffusion_models | `qwen_image_2512_fp8_e4m3fn`、`qwen_image_fp8_e4m3fn`、`qwen_image_edit_2511_fp8mixed`、`qwen_image_2.1_bf16`(2.1 基座)、`flux-2-klein-9b-fp8`、`minimax_h3_fl2va_pruned_int8_convrot`、`minimax_h3_ref2va_pruned_int8_convrot` |
| text_encoders | `qwen_2.5_vl_7b_fp8_scaled`(Qwen-Edit)、`qwen3vl_8b_bf16`(Qwen-Image 2.1)、`qwen_3_8b_fp8mixed`(Klein)、`qwen3.5_2b_bf16`(音频)、`t5gemma_b_b_ul2`(音频)、`qwen3vl_32b_minimax_h3_nvfp4_awq`(H3 视频) |
| vae | `qwen_image_vae`、`qwen_image_2.1_vae_bf16`(2.1,64 通道 RGBA)、`full_encoder_small_decoder`(Klein/FLUX.2)、`minimax_h3_video_vae_fp16`、`minimax_h3_audio_vae_fp32` |
| loras | `Qwen-Image-2512-Lightning-4steps-V1.0-fp32`、`Qwen-Image-Lightning-4steps-V1.0`、`Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16`、`qwen-image-edit-2511-multiple-angles-lora`(多视角,配 `ComfyUI-qwenmultiangle` 插件)、`[Qwen-Edit]3DChineseStyle_25`、`Kook_Qwen_2512_真实幻想`、H3 加速三件:`minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16`(4 步 768p)/ `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16` / `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16` |
| checkpoints | `stable_audio_3_medium.safetensors`(音频) |
| upscale_models | `4xNomos8kDAT`(原 `4x-UltraSharp.pth`、`RealESRGAN_x4plus.pth` 已移除) |
| background_removal | `birefnet.safetensors` |
| controlnet | `Qwen-Image-InstantX-ControlNet-Inpainting`(InstantX Inpainting,扩图/局部重绘用) |
| facerestore_models | `GFPGANv1.4`、`GFPGANv1.3`、`codeformer-v0.1.0`、`GPEN-BFR-512`(人脸修复,Impact-Pack/ReActor 自动下载) |
| TTS | `TTS\Qwen\` 下 Qwen3-TTS-12Hz 五变体(0.6B-Base / 0.6B-CustomVoice / 1.7B-Base / 1.7B-CustomVoice / 1.7B-VoiceDesign,各含主模型 + speech_tokenizer);`TTS\SenseVoiceSmall`(ASR,`model.pt`) |

路线:Qwen-Image(国漫/中文更优)+ MiniMax H3(视频)+ FLUX.2-Klein(图像);曾清理 FLUX.2 全套、旧版 qwen_image、LTX-2.3/Wan 2.2、TripoSplat 等,后续按需重新引入(以表格为准)。`ComfyUI\blueprints\` 内置 116 个蓝图(位于 ComfyUI 目录内;除 Qwen 2511 外均缺模型)。

## Qwen-Image 2.1 工作流(2026-09-21 建)

2.1 是 7B 统一"生成+编辑"模型(2026-09-20 发布), 与 2511/2512 **架构不兼容**(文本编码器换 Qwen3-VL 8B、VAE 换 64 通道 RGBA), 故旧 LoRA 全部不可用, 另建 4 个工作流并存而非替换原版:

| 工作流 | 对应原版 | 链路 |
|--------|----------|------|
| `00110_万物建模_QI2.1` | `0011_万物建模` | 两阶段: 文生图 → 带图编辑优化 |
| `00120_万物变化_QI2.1` | `0012_万物变化` | 单阶段: 图1/2/3 多图参考编辑 + 灰度遮罩局部重绘 |
| `00200_场景首帧_QI2.1` | `0020_场景首帧` | 两阶段: 文生场景 → 编辑优化 |
| `00220_场景推镜_QI2.1` | `0022_场景推镜` | 单阶段: 框选放大 → 编辑精修 |

⚠️ **2026-09-24 起这 4 个工作流与 1.x 版共用同一批数据表**:原 `00110/00120/00200/00220_*.md` 4 张表已删除,工作流内 `md_path` 一律指向 `0011_万物建模.md` / `0012_万物变化.md` / `0020_场景首帧.md` / `0022_场景推镜.md`。同名工作区分只靠文件名后缀 `_QI2.1`。**产物目录取表文件名**(2026-09-24 起保存类节点优先用工作流的 md 表文件名作子目录),故 4 个 QI2.1 工作流与各自 1.x 版**落同一个目录**(如 `media\七纹刻印\0011_万物建模\`)—— 同一行 ID 的产物互相覆盖,只保留一份;原 4 个 QI2.1 旧目录已于 2026-09-24 **改名并入**对应基础目录(`media\七纹刻印\0011_万物建模\` / `0012_万物变化\` / `0020_场景首帧\` / `0022_场景推镜\`),工作区内不再有任何带 QI2.1 的目录(各旧目录只含 1 个 PNG,且并入时基础目录尚不存在,故为纯改名、零冲突);`0044_参考视频.md` 里 3 处 `@{*_QI2.1/…}` 引用同步改为表名前缀。`0011_万物建模.md` 已用 2.1 的「写实三维CG + 单一视角」内容覆盖(原 1.x 的「国漫CG + 三视图」违反现行规范)。

**关键差异(改这些工作流时注意)**:
- **不加载任何 LoRA**。2.1 无 4 步蒸馏 LoRA(LightX2V 的 Day-0 支持是框架级 fp8 优化, 不是 LoRA), 故步数按官方域设 **标准 30 步 / 加速 15 步**, cfg 固定 1.0; 原版"4 步 Lightning 档"已不存在
- 文本编码统一用 **`TextEncodeQwenImage21`** 一个节点同时产出 positive/negative(带参考图编码), 取代原版两个 `TextEncodeQwenImageEditPlus`; 其 `resolution` 默认 1024 控制参考图缩放
- 新增 **`QwenImage21Cache`**(接在 UNETLoader 之后)复用 KV 前缀, 编辑任务提速明显; 参数 `device=auto` / `dtype=default`
- latent 是 **64 通道**(旧版 16), 用 `EmptyLatentImage` 即可: `comfy/sample.py` 的 `fix_empty_latent_channels` 会把空 latent 自动扩展到模型通道数并按 `spacial_downscale_ratio`(16)修正分辨率
- 数据表与 1.x 版**共用**(不另建表):`stories\七纹刻印\0011_万物建模.md` 等 4 张;跨表引用写 `@{0011_万物建模/ID}`、`@{0020_场景首帧/ID}`(前缀是**表文件名**,也就是产物目录名 —— 保存类节点优先用工作流的 md 表文件名建子目录,引用因此走**严格命中**而非递归兜底)
- 布局由 `scripts\make_qwen21_common.py` 的布局引擎生成(拓扑分层 + 双向重心法 + 差分约束求列偏移), 生成脚本为 `scripts\make-00{110,120,200,220}.py`; 改完重跑即可(**幂等**), 自检函数会校验六条布局规范

## 官方文档与分类文档

- `refs\ComfyUI-Docs` 为官方文档本地克隆(在线源码 GitHub `Comfy-Org/docs`;2026-09-30 由 `docs\` 迁入 `refs\`);专题资料见 `webs\Bilibili\B站教程调研.md`(含 H3 专题)与 `webs\RunningHub\`(API 读取指南 / workflows-list.md)

## 开发规范

- **临时脚本(一次性调研/修改/校验用的 `.py`/`.ps1` 等)一律写入 `scripts\` 目录**,严禁散落在项目根目录或其它目录;用完即删或留存在 `scripts\` 内,不得在根目录遗留 `_*.py` 之类临时文件
- **项目根目录本身是一个 git 仓库**(`main`),子模块经 `.gitmodules` 登记、以**指针提交**(gitlink,模式 `160000`)跟踪;子模块改动在**子模块目录内** commit/push 后,再回根仓库 `git add <子模块路径>` 提交指针更新;不要留着子模块脏工作树,也不要往根仓库混入无关文件
- 修改 ComfyUI 主程序时遵守 `ComfyUI\AGENTS.md` 上游规范:改动小且直接、尽量少改文件、不引入新依赖、核心代码不发网络请求(见其 "No Internet Requests")、保持节点/API/工作流兼容、删除死代码、代码须看起来像手写
- 节点注册(V1 `NODE_CLASS_MAPPINGS` / V3 `comfy_entrypoint()`)与 ComfyUI API 使用约定见各插件仓库及 `ComfyUI\AGENTS.md`;代码书写规范(卫语句优先、switch 代替 if-else、缩进)与网络/代理策略见全局 `~/.claude\CLAUDE.md`

## 网络与代理

- 默认直连外网;直连失败(超时/403/TLS 被掐)时改用本机代理 `127.0.0.1:7890`(Clash Verge 混合端口,HTTP 与 SOCKS5 均可):
  - HTTP 代理:`http://127.0.0.1:7890`(curl `-x http://127.0.0.1:7890`、`HTTPS_PROXY`/`HTTP_PROXY` 环境变量)
  - SOCKS5:`socks5h://127.0.0.1:7890`(curl `-x socks5h://127.0.0.1:7890`)
- 注意:OpenAI 系域名等会被 Cloudflare/SNI 拦截,需走专用节点;huggingface 下载失败时优先直连、再带代理(国内可用 `hf-mirror.com` 镜像)

## 工作树现状(已知事项)

- `ComfyUI` 工作树含已删除的占位文件(`models/*/put_*_here` 等),属安装后正常现象,不要恢复或提交
- `custom_nodes\websocket_image_save.py` 与 `example_node.py.example` 是本地文件,不属于任何仓库
- `media`(input/output 软链目标)按项目分目录:`template\`(模板)+ `七纹刻印\`(当前项目, 软链指向);部分旧工作流引用的输入文件可能仍缺失,运行前核对

## 常见任务

- 修改工作流或重要文件前,先备份到 `backups\`,命名 `backup-<文件名>-<YYYYMMDD>-<说明>.json`;**备份一律放 `backups`,不要再放 `.claude\`**
- 新增/修改自定义节点:直接改对应子项目,经软链接即时生效,无需复制到 custom_nodes
- 验证节点加载:启动后查日志中 custom node 加载输出,或访问 `/object_info` 检查节点是否注册
- 挑选/运行工作流:先核对「模型与蓝图」确认组件就位,再开 `blueprints\`、`templates\`(官方子目录)、`webs\Bilibili\工作流大全\`、`webs\RunningHub\workflows\` 的 json
- 清理临时输出残留:删 `temp\` 里 `ComfyUI_temp_*.png` 后,「资产 → 已生成」仍显示属正常(任务历史 `GET /history` 的引用)。清理:`POST /history` + `{"clear": true}` 全清,或 `{"delete": ["<prompt_id>",...]}` 定向删;验证归零后前端 F5。⚠️ 清空前确认 history 输出均为 `temp` 类型,勿误清 output/input 真实数据

## 视频/音频分析工具链(产物必须真读, 2026-09-13 补)

生成视频/音频后**不能只看 `status: success`**: 画面要抽帧后用 `read_image` 逐张看, 音频要转成文字/特征/频谱图后再判断。**AI 没有听觉, 唯一"看"的通道是 `read_image`(只认图)** ⇒ 视频/音频必须先落成帧图/频谱图。**完整链路、能力边界、已知坑与两个工具的完整源码见 `docs\视频音频分析工具链.md`**(`scripts\` 是临时目录随时会被清空, 源码以该文档为准)。

全链四步(全部离线, 实测样本 = 0043 关键帧视频):

1. **定位产物**: `GET /history?max_items=N` → `outputs.<node>.{images,videos,audio,gifs}[].{filename,type}`; `type: temp` → `ComfyUI\temp\`, `type: output` → `media\<项目>\`(真实数据勿删; 保存类节点还会再建一层子目录 —— 优先用工作流的 md 表文件名, 没有 md 表节点才用工作流名, `filename` 不带该层级, 需从插件返回消息确认); `history.prompt[<n>]` 是当时的 API 图(可查节点数/mdtable `selected.id`)。同名前缀的 temp 文件会累积, 只用 mtime 最新那个。
2. **探针**: `ffprobe -v error -print_format json -show_format -show_streams <文件>`; 核对视频 宽高/fps/总帧数、音频 采样率/声道/**有没有音轨**(H3 无音轨多为 `overall_soundscape` 段没写对)。`总帧数 ÷ fps = 时长`(H3 固定 24 fps: 362 帧 = 15.083s)。
3. **画面**: `ffmpeg -y -i in.mp4 -ss 11.000 -frames:v 1 f011.png`(精确; `-ss` 放 `-i` 之前 = 快但可能偏几帧) + 联络表 `-vf "fps=1/2,scale=640:-1,tile=4x3" -frames:v 1 grid.png` → `read_image` 判读: 锚点主体在不在、数量/位置对不对、有没有被文字描述替换掉(实测: 提示词写"摊开的手稿", 中段笔记本就变成了摊开的书)。
4. **音频**: `ffmpeg -y -i in.mp4 -ac 1 -ar 16000 mono16k.wav` → **SenseVoiceSmall**(`models\TTS\SenseVoiceSmall`, funasr 加载, 传本地路径 + `disable_update=True` ⇒ 不发网络请求) 出 `<|语种|><|情绪|><|事件|>文本`, 即 转写(中/英/日/韩/粤)/情感(HAPPY·SAD·ANGRY·NEUTRAL)/事件(Speech·BGM·Applause·Laughter 等); 声学特征用 librosa + pyloudnorm(响度 LUFS/节奏 BPM/频谱质心/谱平坦度/F0); 频谱图与波形图用 `ffmpeg -lavfi "showspectrumpic=s=1024x512"` / `"showwavespic=s=1024x256"` 落 PNG 后再 `read_image` 看。

能力边界(**别承诺做不到的**): 转写/情绪/事件/响度/节奏/结构 ✅; **性别**仅"有人声时按 F0 中位数"启发式(纯音乐无效, 实测把贝斯基频判成了男声) ⚠️; 音色只能客观化描述(低沉/明亮/沙哑), 不能"像谁" ⚠️; **说话人分离、认出具体曲目、认人、主观听感(自然不自然/口音) ❌**(缺声纹与 diarization 模型, 曲目识别需联网指纹库, 听感需人耳)。可升级项(faster-whisper 权重 / pyannote·3D-Speaker / CLAP·AST / chromaprint)见该文档 §7。

坑: ① 脚本报 `exit code 1` 常是 torch `pynvml` FutureWarning 走 stderr 被 PowerShell 当 `NativeCommandError`, 判成功看业务输出不看退出码; ② funasr 与 ComfyUI 抢同一张 8 GB 卡, OOM 就改 `device="cpu"`; ③ 抽帧时间点别超 `duration`(ffmpeg 退出码 0 但不生成文件, 末帧用 `时长 - 1/fps`); ④ **图与数字必须一起看** —— 纯音乐时 `pyin` 的 F0、以及"低谱平坦度 ⇒ 没雨声"的推断都会骗人, 频谱图能纠正。

## 工作流布局规范(修改与创作必须遵守)

**布局目的**: 让工作流一眼可读、连线可追踪、节点群可辨识。以下六条为硬性要求, 修改或新建工作流时**逐条自检**; 彼此冲突时优先级为: **方向(第 1、2 条) > 不重叠(第 3 条) > 紧凑美观(第 4~6 条)**。

1. **左右方向: 严格「输出在左、输入在右」**
   - 全图严格按数据流方向从左往右推进: 任一节点的**所有**上游节点都必须完全在其左侧, **所有**下游节点都必须完全在其右侧; 起点(纯输出节点: 各类加载器、KSamplerSelect/RandomNoise/PrimitiveInt 等参数节点)落在最左, 终点(纯输入节点: Preview/Save 类)落在最右;
   - **严格判定口径**: 对每一条连线 `A → B` 必须满足 `A.x + A.宽 ≤ B.x`(A 的右缘不得越过 B 的左缘); **上下游同列、或上游在右下游在左, 一律算违规**, 必须重排;
   - 特别禁止把「加载器 → 它的后处理」这类上下游挤在同一个 x 列里(如 `UNETLoader → 采样前处理`、`模型/调度器选择器 → 切换器`), 这是最常见的错误;
   - 允许在一列里放**多个互不相邻**的节点(它们来自不同分支), 但**绝不允许同一列里出现上下游关系**。

2. **上下方向: 严格按端口上下顺序排列, 输入线不交叉、输出线不交叉**
   - 一个节点有**多个输入端口**时: 节点上输入端口的自上而下顺序(`inputs` 数组下标, 0 在最上; 连线里的 `target_slot` 即该下标), 必须与**这些端口各自上游节点的上下顺序完全一致** —— 接最上面输入端口的节点排最上, 依次往下; 于是进入该节点的多条输入线彼此**不交叉**;
   - 一个节点有**多个输出端口**时同理: 各输出端口(`outputs` 下标 / 连线里的 `origin_slot`)**自上而下对应的下游节点, 也必须自上而下依次排列**, 使离开该节点的多条输出线彼此**不交叉**;
   - **判定口径**: 对同一节点的任意两个已连端口 `p < q`, 必须满足 `y(对应上游节点)_p < y(对应下游节点)_q`(用节点垂直中心或端口实际 y 比较; 同一个节点同时占两个端口时视为无顺序约束; 某个端口未连线时跳过该端口, 但已连端口之间的相对顺序必须保持);
   - 该条**优先于「连线最短/最直」**: 宁可让某条线变长、让某一列出现空白, 也不允许端口顺序倒置造成交叉。

3. **节点不重叠与边距**
   - 节点之间**严禁重叠**;
   - **相邻节点(横向或纵向相邻)之间边距必须大于 50px 且小于 100px**: 50px 以下太挤、无法辨认连线归属, 100px 以上太散、同一条链路会被空白割断; 同列相邻节点纵向净间距、同排相邻节点横向净间距都按此区间执行(判定口径: 下限 `>50px`、上限 `<100px`, 即净间距落在开区间 (50, 100) 内; 落点默认取纵向 60px、横向 80px, 都留在区间中部);
   - 上限(<100px)是**紧凑性要求**, 优先级低于第 1、2 条: 若为满足端口上下顺序(第 2 条)必须拉开更大间距, **以第 2 条为准**, 但需在交付说明中列出这些被迫超限的相邻对(远距节点之间不判上限);
   - **`FallingTSMarkDownTable`(MD 数据表)节点在画布中单独占一列**: 其所在列的整条垂直方向(正下方无限延伸, 无像素限制)严禁放置任何节点——MD 节点会根据数据内容自动向下扩展高度, 同列下方有节点会被覆盖; 其他节点只能放在 MD 节点右侧的其他列(列间边距同样遵守 `>50px 且 <100px` 的区间), 与 MD 节点同列的任何位置均不得放置节点;

4. **连线走线(尽量直线)**
   - 整体按「向右向下推进」布局(见第 6 条)时, 连线天然从左上往右下正方向走, **理论上不会出现连线回折**, 无需单独校验回折;
   - 输出端口与对应输入端口**尽最大努力保持直线**: 同一功能链上的节点尽量同排/同列对齐, 让输出到下一输入基本水平(左→右);
   - 尽量避免长距离交叉串线; 有多个下游时优先保证主干直线。

5. **节点群按「正方向大区域」摆放**
   - 不同功能(加载器/采样/解码/后处理/条件)的节点群, 各自聚成**独立大区域**, 不要混排交错;
   - 整体流向保持**正向一致**: 模型/输入从左上或左侧进入, 处理链水平向右推进, 输出/保存落在右侧或右下;
   - 每个功能群内部节点紧凑对齐, 群与群之间留出明显空白带以区分。

6. **布局确定方式: 从起点开始逐个向右下推进, 定好即锁定**
   - 布局从**第一个节点**开始: 先定好它的起始位置, 再基于已定节点逐个计算后续节点的大小和位置, 一个一个确定;
   - 整体按**向右、向下**方向排列推进(新节点一般落在已定节点的右侧或右下);
   - 每确定一个节点的大小和位置后就**锁定, 不得再回头修改**; 后续节点只能适应已锁定节点, 不能反过来挪动已定节点;
   - 从开始往右下逐个确定, 直到**最后一个节点**确定完, 整套布局即视为完美定稿, 此时才允许统一修改写入文件。

**⚠️ 改完工作流文件必须让前端重新加载(否则改动会被浏览器覆盖)**
- 工作流在前端标签页里有一份**内存副本**: 只要该工作流还开在浏览器里, 前端的视图变化/编辑/保存都会把内存副本**整份写回磁盘**, 用脚本改好的布局会被旧副本覆盖(实测: 改完约 11 分钟后被写回);
- 正确顺序: 用脚本改之前先在浏览器**关掉该工作流的标签页**(或至少先别动它) → 脚本改完 → 再打开该工作流(或 **F5 强刷**页面让它重新从磁盘加载);
- 前端写回**只改 `extra.ds`(画布缩放/平移)与手动拖动过的节点位置**, 节点参数值与连线不会变; 若发现 `pos` 被打回旧布局, 重跑布局脚本即可(布局脚本必须是**幂等**的: 对已合规的布局再跑一次不改变结果)。


## Git 提交规范

我的插件中, 严格按照 `git add .` `commit` 最后推送
项目根目录中, 严格按照 `git add .` `commit` 最后推送
子项目除了我的插件是我自己写的, 其它所有子项目不允许提交和修改代码, 或者推送
