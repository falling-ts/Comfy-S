# WorkBuddy:本工作区唯一的 agent

本工作区统一使用 **WorkBuddy**。除它以外的 agent(Claude Code / Codex / Gemini CLI / Qwen Code 等)一律不做适配,
也不提供多 agent 安装脚本;驱动 ComfyUI 的硬核部分对所有 agent 本来都是同一个 MCP server(`comfyui-mcp`)。

| 项目 | WorkBuddy 的对应做法 |
|---|---|
| 知识文件 | 本目录 `SKILL.md`(带 `name` + `description` frontmatter) |
| 项目级技能位置 | `<项目根>/.workbuddy/skills/comfyui/` |
| 用户级技能位置 | `~/.workbuddy/skills/comfyui/` |
| MCP 注册 | `~/.workbuddy/mcp.json` 的 `mcpServers` 段(改完需在连接器页面对新服务点「信任」才生效) |
| 技能加载方式 | 按需自动加载(渐进披露:先读 `SKILL.md`,再按需展开下面的专题 md) |

## 安装

1. 把本目录整体复制到上面任一技能位置(项目级或用户级),目录名保持 `comfyui`;
2. 需要 MCP 驱动层时,在 `~/.workbuddy/mcp.json` 里注册 `comfyui-mcp`
   (`"command": "npx"`, `"args": ["-y", "comfyui-mcp"]`),重启会话后在连接器页面确认「信任」;
3. 只想让 WorkBuddy 读懂工作区、不装 MCP 也可以——本目录的知识文件独立可用
   (本机实况见 `machine.md`,常见坑见 `KNOWN_ISSUES.md`)。

## 本目录知识文件导航

| 文件 | 内容 |
|---|---|
| `SKILL.md` | 唯一入口:何时用、按什么顺序读 |
| `MODELS.md` / `MODEL_INDEX.md` / `MODELS/` | 按模型查提示词配方 |
| `NODES.md` / `NODE_LIBRARY/` | 节点清单与用途 |
| `LAYERS.md` | 四层安装结构 |
| `BOOTSTRAP.md` | 首次上机环境准备 |
| `ADVANCED.md` / `TASKS.md` / `workflow-layout.md` | 进阶用法、任务范式、工作流排版规范 |
| `LTX2_TRAINING.md` | LTX-2 训练流程 |
| `UPDATING.md` | 模型与 bug 的周期性更新 |
| `KNOWN_ISSUES.md` / `machine.md` / `workspace-env.md` | 已知问题、本机实况、工作区环境 |
