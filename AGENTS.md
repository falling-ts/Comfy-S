# ComfyUI 本地工作区

ComfyUI 及自定义节点的本地开发工作区。下文路径均相对项目根目录,不绑定特定操作系统或 shell;命令示例按本机环境给出,部署到其它平台时替换路径分隔符/可执行文件位置即可。

**本文件只保留「每次都必须知道」的核心**;低频细节已拆入技能,按需加载(见文末「详细资料去哪儿看」)。

## 技术栈与运行(速查)

- **环境**:项目内 `.venv`(Python 3.13.13 / torch 2.13.0+cu130 / CUDA 13.0 / RTX 4060 8GB),**一律用 `.venv\Scripts\python.exe`**(类 Unix `.venv/bin/python`),禁用系统 Python 与 conda
- **ComfyUI v0.39.2**(submodule,detached HEAD 跟随上游 tag);前端 1.53.10 / 模板包 0.11.78;模型合计约 263.5 GB
- **启动**:`cd ComfyUI && python main.py --enable-manager`,或直接 `.venv\Scripts\python.exe main.py --enable-manager`,或项目根 `bash comfy-server.sh`;前端 `http://127.0.0.1:8188`
- 改自定义节点代码后**重启 ComfyUI 生效**(经软链接即时加载,无需复制)
- ⚠️ **重启前先确认真能杀掉旧进程**:提权启动的进程在同权限会话外会 `Access is denied`,而 `comfy-server.sh` 会吞掉失败、且"端口已监听"被判据**旧进程**满足 ⇒ 打印就绪却仍跑旧代码。判据:对比 `Get-NetTCPConnection -LocalPort 8188 -State Listen` 的 PID 与启动前是否一致
- **官方日志**:`ComfyUI\user\comfyui_<port>.log`(非 `logs\`);排查请求/插件问题优先看它

版本细则、依赖清单、升级/插件更新/模板库更新流程、模型与蓝图全表、网络代理 → **`comfyui` 技能的 `workspace-env.md`**。

## 关键路径

| 路径 | 说明 |
|------|------|
| `ComfyUI` | 主程序(submodule);`models`/`input`/`output`/`workflows`/`custom_nodes` 均为**相对软链接**外挂 |
| `custom_nodes` | 插件聚合目录(45 插件子模块 + `H3ReferenceSuite` 链接);自有插件 **ComfyUI-FallingTS** |
| `models` | 模型实际存放处(40 个顶层槽位,空槽位仅占位) |
| `workflows` | 用户工作流实际存储处(35 个,编号 0010~0070) |
| `stories` | Obsidian 故事库工作区(`七纹刻印` 为当前项目;`plugins\` 为插件聚合目录) |
| `media` | input/output 软链目标,按**项目**分目录(`七纹刻印\` 为当前项目,真实产物) |
| `docs` | 本地参考文档(44 篇专题 md) |
| `refs` | 参考资料聚合(7 个子模块 + `Qwen-Image-Edit-Skills` 本地目录) |
| `templates` | 官方模板库缓存(833 个 JSON)/ `webs` 三方调研 / `backups` 修改前备份(本地暂存) |
| `scripts` | 可复跑工具链脚本(自动定位仓根、幂等): `wf_layout_all.py` 全量布局重排等,见 `comfyui` 技能 |
| `.agents` | 技能聚合目录(`.claude` 软链指向它) |

目录逐条说明、8 条软链接映射(A~D)、工作流编号体系、Qwen-Image 2.1 工作流 → **`comfyui-workspace` 技能**。

## MiniMax H3 加速 LoRA ↔ shift 配对表(改 H3 工作流前必查)

**铁律:shift 是 LoRA 自带的训练配方,不是口味偏好。** 蒸馏 LoRA 只对它训练时那条 sigma 网格成立;
配错 shift = 换了采样计划,**不会有任何报错**,只会画面/音频结构性崩坏。换 LoRA 必须同步改
`MiniMaxH3SigmaShift.shift_video` / `shift_audio`。

### 权威配对表

| LoRA 文件(comfyui_bf16) | 任务 | 训练分辨率档 | **shift (video/audio)** | 蒸馏 NFE | 推荐步数 | width/height |
|---|---|---|---|---|---|---|
| `minimax_h3_fl2v_turbo_4step_v0.1_comfyui_bf16` | FL2VA | **544p 档**(≈0.5 MP,混合宽高比) | **12 / 3** | 4 | 4 | 任意合法 canvas |
| `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16` | FL2VA | **768p 档**(1344×768) | **6 / 3** | 4 | 4 | 1344×768 |
| `minimax_h3_fl2v_turbo_4step_v1.1_768p_comfyui_bf16` | FL2VA | **768p 档**(1344×768) | **6 / 3** | 4 | 4 | 1344×768 |
| `minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16` | FL2VA | **768p 档**(1344×768) | **6 / 3** | 4 | 4 | 1344×768 |
| `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16` | FL2VA | **544p 档**(≈0.5 MP,混合宽高比) | **12 / 3** | 8 | 8 或 4 | 任意合法 canvas |
| `minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16` | FL2VA | **768p 档**(1344×768) | **6 / 3** | 8 | 8 | 1344×768 |
| `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16` | **Ref2VA** | **544p 档**(≈0.5 MP,混合宽高比) | **12 / 3** | 4 | 4(实需 6–8) | 任意合法 canvas |
| `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16` | **Ref2VA** | **768p 档**(1344×768) | **12 / 3** ⚠️ | 8 | 8 | 1344×768 |

### 「544p」到底是什么(≠ 832×480)

⚠️ **`544p` 是官方 README 表格的原文训练档标签,指「短边 544、混合宽高比」,不是一个固定尺寸。**
不要把本机的 `832×480` 当成「544p」——**那是两个不同档位**:

| 叫法 | 短边 | 代表尺寸 | 面积 | 官方示例用途 |
|---|---|---|---|---|
| **0.4 MP 档**(480p) | 480 | **832×480** / 864×480 | 0.40 MP | I2VA 示例(`864×480`) |
| **544p 档**(0.5 MP) | 544 | **960×544** / 864×544 | 0.52 MP | T2VA 与 Ref2VA 示例(`960×544`) |
| **768p 档** | 768 | **1344×768** | 1.03 MP | 768p 系 LoRA 训练分辨率 |

- 官方三个 example workflow 的实际默认是 **960×544(T2VA、Ref2VA)** 与 **864×480(I2VA)**
  —— 也就是 **0.5 MP 与 0.4 MP**,**不是** 1344×768。
- 所以「544p 系 LoRA」跑 `832×480` 是**可以的**(它在合法 canvas 内,且属于同量级低分档),
  两者并不冲突;但要知道**它们不是同一个数字**,别把 480 当成 544。
- 本机 `stories` 技能里「H3 视频只支持 480p 与 768p 两档」是**本机资源表的收窄约定**
  (为速度与显存只取两档),并非 ComfyUI 的硬限制 —— 硬限制只有下面三条。

**canvas 硬约束(ComfyUI `nodes_minimax_h3.py` 实测)**:

- `MAX_PIXELS = 768 × 1344 = 1 032 192` = **1.0322 MP**(⚠️ 不是 0.98 MP;这是本机硬上限)
- 短边 ≤ 768;每轴必须是 **32 的倍数**(VAE 16× 空间步长 × DiT 2× patch)
- 超限**不会被自动纠正**(与官方 `adapt_canvas` 只在 `width`/`height` 走 `Resolution Selector` 时生效不同)
- 例:`1344×768` ✓、`960×544` ✓、`832×480` ✓;`1664×960` ❌(1.60 MP 超限)、
  `1376×768` ❌(1.057 MP 超限)

### ⚠️ 两个最容易搞错的点

1. **Ref2VA 不随分辨率改 shift。** Ref2VA 的两个 LoRA —— 4step v0.1(544p)与 8step v1.0 **768p** ——
   官方推荐**都是 12/3**。768p 文件名只说明训练分辨率,**不蕴含** shift 6。
   官方 HF 公告原话:「Steps: 8 · **Video shift: 12** · Audio shift: 3 · Sampler: Euler · Resolution: Up to 768p」
   (<https://huggingface.co/lightx2v/Minimax-h3-Turbo/discussions/51>)。评论区亦印证:Ref2VA 推荐值 12/3
   **正是 ComfyUI 默认值**,故默认工作流不给 shift 节点。
2. **`6/3` 只属于 FL2VA 的 768p 系。** 根源是 FL2VA 768p 蒸馏换过 sigma 网格。
   **不要用「文件名带 768p ⇒ 6/3」这条通则去推 Ref2VA。** 官方 README 的 `Model specs` 表
   **根本没有 Ref2VA 8-step 这一行**(表格最后更新 2026-08-27,而该 LoRA 发布于 09-04),
   这也正是第三方资料(comfyui-wiki、vpipe 等)把它误记为 6/3 的原因 —— vpipe 已自承是
   「从 768p 谱系继承推断」,而非实测。

### 采样器与步数经验

- **采样器**:turbo LoRA 一律 **euler**(官方 8 处公告/回复口径一致);scheduler `simple`。
  非蒸馏档(20 步)走 `res_multistep`。
- **步数**:4 步是**下限**;6–8 步锐度与细节明显更好,超过 8 步反而出现过锐伪影。
  社区普遍反映「4 步档在实际使用中需要 6–8 步」。两段式 hires 二遍可用 4 步档 +
  低 `denoise`(≈0.25–0.35)少步(<https://huggingface.co/lightx2v/Minimax-h3-Turbo/discussions/52>)。
- **分辨率**:每轴必须是 **32 的倍数**;768p LoRA 训练于 1344×768;硬上限
  `MAX_PIXELS = 768×1344 = 1.0322 MP`(短边 ≤ 768)。低分档另配(官方示例:t2v 960×544、
  i2v 864×480、ref2v 960×544)。**注意 `832×480` 属 0.4 MP 档,与官方 544p 档(960×544)
  不是同一个数字**(见上文「544p 到底是什么」)。
- **LoRA 强度**:多数情况保持 `1.0`;v1.1 768p 有用户实测 1.20–1.30 更锐。
- **参考图 resize**:官方蒸馏用 `match` 策略(`MiniMaxH3ReferenceToVideo` 的 `ref_image_size_mode`),
  与训练一致,官方明确推荐。

### 已知质量事实(调参时别重复踩)

- **768p 系整体不如 544p 稳**,社区实测反馈「过饱和塑料感、音频差、提示词跟随弱、动作幅度小」
  (<https://huggingface.co/lightx2v/Minimax-h3-Turbo/discussions/27>,该帖已 closed)。
  官方 Roadmap 亦将「提升 Ref2VA / FL2VA 的质量与一致性」列为待办。
- **Ref2VA 普遍弱于 FL2VA**:达到同等音视频质量,Ref2VA 常需 8–10 步(FL2V 仅 4 步)。
- **8-step 768p 与低分辨率不兼容**:官方回复明确「Does not work well with other Loras,
  and at lower screen resolutions (lower than 768p)」。**分辨率必须与档位绑定**。

### 元数据现实

`models/loras/` 下这些 LoRA 的 safetensors `__metadata__` **不含 shift**
(只有 `base_model`/`training_rank`(128)/`training_alpha`/`training_scale`/`qkv_fusion`/
`swi_glu_mapping`/`source_format`/`target_format`)。**唯一权威依据是上游官方公告与规格表**,
不能指望从权重文件里读出来。

### 权威来源(按可信度排序)

1. <https://github.com/ModelTC/Minimax-H3-Turbo> 的 `README.md` §1 `Model specs` 表(FL2VA 全部)
2. <https://huggingface.co/lightx2v/Minimax-h3-Turbo/discussions/51> Ref2VA 8-step v1.0 768p 公告(**12/3**)
3. <https://huggingface.co/lightx2v/Minimax-h3-Turbo/discussions/48> FL2VA 8-step v1.0 768p 公告(6/3)
4. <https://huggingface.co/lightx2v/Minimax-h3-Turbo/discussions/42> FL2VA 4-step v1.1 768p 公告(6/3, euler)
5. 官方示例工作流 <https://github.com/ModelTC/MiniMax-H3-Turbo/tree/main/example_workflows>
   (`ref2v` 图实测 `MiniMaxH3SigmaShift` = `[12, 3]`)
6. ⚠️ **第三方(comfyui-wiki、vpipe 等)不可作为 shift 依据** —— 它们对 Ref2VA 8-step 768p 记的是
   错误的 6/3。

## 数据流约定(工作流 ↔ md 表 ↔ 产物目录)

- `FallingTSMarkDownTable` 节点按 `md_path` 读 `stories\<故事库>\<表名>.md`,按行 ID 取参数
- **产物目录优先取 md 表文件名**(去 `.md`)→ `media\<项目>\<表名>\`;工作流**无 md 表节点**时退回**工作流名**
- **跨表引用**写 `@{<表文件名>/<ID>}`,走**严格命中**(前缀即表文件名 = 产物目录名)
- QI2.1 版与 1.x 版**共用表** ⇒ 落同一目录、同 ID 产物**互相覆盖**

## 三条铁律(本机全局约定)

① 全程只用**简体中文**思考与输出;② 改文件只能用 `edit`/`write`,命令与脚本只做**只读校验**;③ 校验脚本经 **stdin 就地执行**,不落地临时文件(需落盘时写 `.agents/tmp/`)。

## 开发规范

- **临时脚本不落盘进项目**:一次性逻辑经 stdin 就地执行(`.venv\Scripts\python.exe - <<'PY' ... PY`;Node 用 `node - <<'JS' ... JS`);确需落盘用系统临时目录;**能复跑的工具链**一律放 `custom_nodes\ComfyUI-FallingTS\dev\`
- **超大文件例外**:修改超大文件、添加超多内容,实在没法用编辑工具(`edit`/`write`)时,才允许写脚本代劳;脚本文件**只能放根目录 `temp\`**(该目录已 git 忽略),用完即删
- **根目录是 git 仓库**(`main`),子模块经 `.gitmodules` 以**指针提交**(gitlink)跟踪:子模块内先 commit/push,再回根仓库 `git add <路径>`;不要留子模块脏工作树,也不要混入无关文件
- 改 ComfyUI 主程序遵守 `ComfyUI\AGENTS.md`:改动小且直接、少改文件、不引入新依赖、核心代码不发网络请求、保持节点/API/工作流兼容、删死代码、代码须像手写
- 修改工作流/重要文件前先备份到 `backups\`(`backup-<文件名>-<YYYYMMDD>-<说明>.json`);备份只放 `backups`

## 工作流布局规范(改/建工作流必守)

九条硬性规范(冲突仲裁链,从高到低:**方向(①) > 不重叠/净距(③) > 继续屏障(⑨) > 分区块(⑥) > 阶梯(⑧) > 端口序(②) > 连线最短(④⑤) > 紧凑美观**;第①条不可让步。**凡需要「列内微调 y」的规则一律排在不重叠之后**):**① 输入在左、输出在右**(即上游在左、下游在右;每条连线 `A.x+A.宽 ≤ B.x`,上下游严禁同列);**② 上下按端口顺序排,输入线/输出线不交叉**;**③ 节点不重叠,相邻边距落在开区间 (50,100)px**;**④ 单条输出线必须最短**(只有一条出线时,下游纵向居中对齐上游,垂直中心偏差趋近 0);**⑤ 多条输出线时第一条最短、其余允许更长**(以 `outputs` 下标最小的已连端口为基准对齐,其它线不要求水平);**⑥ 功能区块按连线关系划区、同区块节点必须聚在一起**(主数据图上做社区发现,参数节点/MD/note 不参与;同区块在同一列内只许连续成段,不得被别的区块切断);⑦ 节点群按正向大区域分区;**⑧ 列间纵向阶梯**:从左往右每列比左邻列**抬高一个节点高度**(取左邻列首节点高度)的 **30%**,累积超过本列自身高度时**回绕归零**成锯齿台阶,避免多条连线挤成水平带、人眼分不清谁连谁;**阶梯仅对功能列生效** —— `MarkdownNote` 与 `FallingTSMarkDownTable` 不参与抬高,它们的 `y` 必须等于**左侧第一个功能列的列首 y**(即 `y = Y0`),与第一列完美横向并行、可并排对照阅读;若出现 `y<0` 统一平移回 `Y0`。**⑨ 二段流程归位(权重链:继续节点 > 一段结果节点 > 连线长度)**(注:本段 ①~⑨ 是摘要序号,与技能文档里的「第 N 条」**不是同一套编号**;详细定义以 `.agents/skills/comfyui/workflow-layout.md` 为准): **整体形态是输入在左、输出后的节点向右推进、从左往右呈台阶式向上**。有二段时,**仅二段相关节点**(其全部消费者都在继续节点下游闭包内,含二段专用的 `UNETLoader`/`VAELoader`/`CLIPLoader`/`LTXICLoRALoaderModelOnly`/`LTXVConditioning`/`KSamplerSelect` 等准备节点,**哪怕与一段有间接关系**)**必须在继续节点右侧**;一段侧节点(在继续节点上游闭包内)不得被推走,尤其**一段自己的结果/预览节点**(如一段 `PreviewVideo`)可能被二段 `AutoSaveImage` 当素材源拉走,但它属于一段,**不得被屏障推走**。无继续节点时,基准改为**一段结果节点的右缘**:二段相关全部节点都应在其右侧。**继续节点权重高于一段结果节点**;两者冲突时以继续节点为准。第① 条(方向)是基底不参与权重链且不可让步,屏障右移遇阻时整体右移屏障列及其右侧、而非放弃屏障。

⚠️ **实现层两条硬约束**(脚本已遵守,重写布局逻辑必须照搬):**列内必须紧凑堆叠(净距恒 60px),对齐只能在「整列平移」上取舍,禁止列内局部位移** —— 旧实现把各节点放到其对上游的理想 y 再推挤,净距会雪崩到 4000~7000px(`0032` 最大 7075px),且**只查列内相邻净距会漏掉病根**(`gap_bad` 全 0 但列首高度逐列累积下沉,`0032` 最高列 4820px 而整图 9550px),故必须同时查**各列首 y 跨度**;**拆列切段必须按 y 实际顺序,不能按端口序**(否则同列出现上千像素空档,`0043` 实测 1100px),x 推进也必须按每个子列实际最大宽逐个推进(否则横向净距被拉到 140~200px、列间空白最大 9600px)。

⚠️ **第 ④⑤ 条是列内 y 轴排序的硬依据**:不再按节点 id 堆叠,而是「下游对齐上游」——单出线必须对齐,多出线只有第一条对齐。

⚠️ **第 ⑥ 条是列内 y 轴排序的主键**:区块带号优先于短线对齐 —— 宁可让某条线长一点,也不能把同一区块的节点拆散到别的区块中间。参数节点(`PrimitiveInt`/`PrimitiveFloat`/`RandomNoise`/`KSamplerSelect` 等)不参与划区,按「消费者最多的那个区块」并入宿主区块。

⚠️ **`FallingTSMarkDownTable` 节点独占一列**(整条垂直方向正下方禁放任何节点)。

⚠️ **改完工作流必须让前端重新加载**:前端标签页里的内存副本会把改动**整份写回磁盘**覆盖脚本结果 —— 先用脚本改前**关掉该工作流标签页**,改完再打开(或 F5 强刷);布局脚本必须**幂等**。

九条全文、判定口径与前端覆盖陷阱的完整复盘 → **`comfyui` 技能的 `workflow-layout.md`**;工具 `workflow_layout.py` 同目录。

## Git 提交规范

- 我的插件(ComfyUI-FallingTS)与项目根目录:严格 `git add .` → `commit` → 推送
- **其它所有子项目**:不允许提交、修改代码或推送(上游子模块只更新不推送)

## 详细资料去哪儿看

| 要看什么 | 加载哪个技能 / 文件 |
|---------|-------------------|
| 目录结构全表、软链接映射、工作流编号体系、QI2.1 工作流、常见任务、工作树现状 | 技能 **`comfyui-workspace`**(全表)/ `symlinks.md`(软链细节) |
| 本机版本/依赖/模型清单/升级流程/网络代理 | 技能 **`comfyui`** 的 `workspace-env.md` |
| 工作流布局八规范全文 + 前端覆盖陷阱 | 技能 **`comfyui`** 的 `workflow-layout.md` |
| 本机安装事实快照(路径/GPU/启动命令) | 技能 **`comfyui`** 的 `machine.md` |
| 无头跑工作流(JSON→API prompt→提交→验证) | 技能 **`comfyui-workflow-runner`** |
| 无头操作 FallingTS 按钮(保存/截帧/完成/继续闸门、读写 md 表) | 技能 **`comfyui-headless-control`** |
| 视频/音频产物分析工具链 | 技能 **`comfyui-workflow-runner`** 的 `references/media-analysis-toolchain.md`;完整源码 `docs\视频音频分析工具链.md` |
| 故事库资源表规范、画面术语、尺寸、H3 提示词、镜头语言 | 技能 **`stories`** |
| Qwen-Image 2.1 / MiniMax H3 提示词工程 | 技能 **`qwen-image-2-1-prompting`** / **`h3-prompt-writing`** |
| 三方工作流素材 | `webs\Bilibili\工作流大全\`、`webs\RunningHub\workflows\`、`templates\` |
