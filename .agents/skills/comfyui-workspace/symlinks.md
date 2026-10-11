# 软链接映射

共 8 个,全部为相对路径 SymbolicLink;2026-08-07 建,08-10 插件收敛为目录级链接,08-13 加 Claude Code 兼容链接,09-20 加 Obsidian 插件安装位,09-22 安装位改「聚合目录 + 单层软链」,插件本体为聚合目录内的真实子模块。

全部为 **相对路径**符号链接,**项目根目录整体移动后不失效**(不依赖具体文件系统/平台)。

## A. 基础链接(4 个)

| ComfyUI 内路径 | 类型 | 相对目标 | 实际指向 |
|------|------|------|------|
| `ComfyUI\input` | SymbolicLink | `..\media\七纹刻印` | `media\七纹刻印`(当前项目) |
| `ComfyUI\output` | SymbolicLink | `..\media\七纹刻印` | `media\七纹刻印`(当前项目) |
| `ComfyUI\models` | SymbolicLink | `..\models` | `models`(模型实际存放处) |
| `ComfyUI\user\default\workflows` | SymbolicLink | `..\..\..\workflows` | `workflows`(用户工作流实际存储处) |

## B. custom_nodes 目录级链接 + H3ReferenceSuite 子链接(2 个)

| ComfyUI 内路径 | 类型 | 相对目标 | 实际指向 |
|------|------|------|------|
| `ComfyUI\custom_nodes` | SymbolicLink(目录级) | `..\custom_nodes` | 根 `custom_nodes`(插件聚合目录,45 插件 + H3ReferenceSuite 链接) |
| `custom_nodes\H3ReferenceSuite` | SymbolicLink(子链接) | `..\refs\minimax-h3-guide\custom_nodes\H3ReferenceSuite` | `refs\minimax-h3-guide\custom_nodes\H3ReferenceSuite`(2026-09-30 由 `h3\` 迁来;盘上必须写**反斜杠**目标 —— 实测 reparse 目标里的正斜杠解析失败 WinError 123,而 git 入库时会统一规范成正斜杠 `../refs/...`) |

- 根 `custom_nodes` 由**根仓库**跟踪:45 个插件以 gitlink 形式登记(全仓共 54 个子模块:`ComfyUI` 1 + `custom_nodes\` 45 + `refs\` 7 + `stories\plugins\Obsidian-Comfy` 1;`.gitmodules` 条目数同为 54,2026-09-30 搬迁后复核一致 —— 其中 `ComfyUI-HYWM2` 是 2026-09-28 新登记的,`refs\` 7 个是 2026-09-30 由 `docs\`(5)+`h3\`(2)迁入的),`H3ReferenceSuite` 为符号链接;本地文件 `example_node.py.example`、`websocket_image_save.py` 被根 `.gitignore` 排除(保留磁盘副本供加载)。`ComfyUI\custom_nodes` 是目录级符号链接,其目标内容不受 ComfyUI 子模块 git 影响
- `ComfyUI\temp\`(真实目录,非链接):运行中生成的临时文件/预览图(如 `ComfyUI_temp_*.png`),可随时清理
- ⚠️ **`ComfyUI\input\`(用户上传)与 `output\`(生成结果)是真实数据所在(经软链落入 `media\<项目>\`):严禁整体删除、移动或批量清理**;只有 `temp\` 可清理

## C. 根目录 Claude Code 兼容链接(1 个)

| 根内路径 | 类型 | 相对目标 | 实际指向 |
|------|------|------|------|
| `.claude` | SymbolicLink(目录级) | `.agents` | 根 `.agents`(技能聚合目录,Claude Code 兼容垫片,2026-08-13 建) |

## D. stories Obsidian 插件安装位(1 个软链 + 1 个插件子模块,**入库跟踪**;2026-09-22 改为「聚合目录 + 单层软链」)

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
- **建链只能用 Python `os.symlink`**:PowerShell `New-Item` 会把相对 target 按 cwd 解析(建出 `D:\media\...` 之类错误目标)。本组软链只建 `.obsidian\plugins` 这**一条**(不再生成 Obsidian-Comfy 安装位软链),由一次性 Python 脚本建立(**幂等**,可重复执行;脚本不落盘,经 stdin 就地执行)。验证口径:`(Get-Item <路径>).LinkType` 为 `SymbolicLink`、`Target` 为相对串、且经链接能读到 `main.js`
- ⚠️ **移动 git 子模块时慎用 `git mv`,且搬运前先关掉会占用它的程序**(实测 2026-09-22:Obsidian 开着时移 `stories\Obsidian-Comfy` 报 `Permission denied`,随后 `Move-Item` 只完成一半 —— 工作树连 `.git` 目录一起被搬走,旧位置只留一个**空** `.git` 目录,而 `.git/modules/stories/<name>` 已不存在,子模块暂时"内联"成独立仓库,`git status` 因该空壳报 `not recognized as a git repository`)。完整修复三步:① `Move-Item <新位置>\.git` → `.git/modules/stories/plugins/<name>`(其 config 通常**没有** `core.worktree`,不必改;默认按 gitdir 反推 worktree 恰好正确);② 写回 `.git` **文件**(内容 `gitdir: ../../../.git/modules/stories/plugins/<name>`,无 BOM);③ 同步 `.gitmodules` 与根 `.git/config` 里该子模块的 **name 与 path**。完成后 `git submodule status` 显示 ` <hash> <path> (heads/<分支>)`(前导空格 = 已初始化且与 index 一致)
