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

六条硬性规范(优先级:**方向 > 不重叠 > 紧凑美观**):**① 输出在左、输入在右**(每条连线 `A.x+A.宽 ≤ B.x`,上下游严禁同列);**② 上下按端口顺序排,输入线/输出线不交叉**;**③ 节点不重叠,相邻边距落在开区间 (50,100)px**;④ 连线尽量直线;⑤ 节点群按正向大区域分区;⑥ 从起点逐个向右下推进、定好即锁定。

⚠️ **`FallingTSMarkDownTable` 节点独占一列**(整条垂直方向正下方禁放任何节点)。

⚠️ **改完工作流必须让前端重新加载**:前端标签页里的内存副本会把改动**整份写回磁盘**覆盖脚本结果 —— 先用脚本改前**关掉该工作流标签页**,改完再打开(或 F5 强刷);布局脚本必须**幂等**。

六条全文、判定口径与前端覆盖陷阱的完整复盘 → **`comfyui` 技能的 `workflow-layout.md`**;工具 `workflow_layout.py` 同目录。

## Git 提交规范

- 我的插件(ComfyUI-FallingTS)与项目根目录:严格 `git add .` → `commit` → 推送
- **其它所有子项目**:不允许提交、修改代码或推送(上游子模块只更新不推送)

## 详细资料去哪儿看

| 要看什么 | 加载哪个技能 / 文件 |
|---------|-------------------|
| 目录结构全表、软链接映射、工作流编号体系、QI2.1 工作流、常见任务、工作树现状 | 技能 **`comfyui-workspace`**(全表)/ `symlinks.md`(软链细节) |
| 本机版本/依赖/模型清单/升级流程/网络代理 | 技能 **`comfyui`** 的 `workspace-env.md` |
| 工作流布局六规范全文 + 前端覆盖陷阱 | 技能 **`comfyui`** 的 `workflow-layout.md` |
| 本机安装事实快照(路径/GPU/启动命令) | 技能 **`comfyui`** 的 `machine.md` |
| 无头跑工作流(JSON→API prompt→提交→验证) | 技能 **`comfyui-workflow-runner`** |
| 无头操作 FallingTS 按钮(保存/截帧/完成/继续闸门、读写 md 表) | 技能 **`comfyui-headless-control`** |
| 视频/音频产物分析工具链 | 技能 **`comfyui-workflow-runner`** 的 `references/media-analysis-toolchain.md`;完整源码 `docs\视频音频分析工具链.md` |
| 故事库资源表规范、画面术语、尺寸、H3 提示词、镜头语言 | 技能 **`stories`** |
| Qwen-Image 2.1 / MiniMax H3 提示词工程 | 技能 **`qwen-image-2-1-prompting`** / **`h3-prompt-writing`** |
| 三方工作流素材 | `webs\Bilibili\工作流大全\`、`webs\RunningHub\workflows\`、`templates\` |
