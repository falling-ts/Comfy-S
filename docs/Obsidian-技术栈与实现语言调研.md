# Obsidian 技术栈与实现语言调研

> 对象：本机已安装且**正在运行**的 Obsidian **1.13.7**
> （`C:\Program Files\Obsidian\Obsidian.exe`，FileVersion/ProductVersion = 1.13.7）
> 取证日期：2026-09-18 · 方法：asar 静态逆向 + 可执行文件版本串扫描
> 配套文档：`Obsidian-MD表格渲染机制.md`（表格渲染深入）、`Obsidian表格渲染实现调研-1.13.7取证附录.md`（原始取证）
> ⚠️ 根 `scripts\` 临时目录已于 2026-10-11 移除，下文的 `scripts\obsidian-*.py` 仅作历史记录

---

## 1. 结论速览

| 层 | 实现语言 | 关键证据 |
|---|---|---|
| **应用源码** | **TypeScript**（编译为 JavaScript） | 4 种 TS 降级 helper 注入 |
| 运行时 | Electron **43.3.0** / Chromium **150.0.7871.212** / Node.js **24.18.1** | `Obsidian.exe` 内嵌版本串 |
| 渲染进程 UI | **HTML + CSS + 原生 JavaScript**（**零框架**） | React / Vue / Svelte devtools hook 全 0 命中 |
| 主编辑器 | JavaScript（**CodeMirror 6**） | `EditorView`/`StateField`/`ViewPlugin` |
| 语法高亮层 | JavaScript（**CodeMirror 5 + HyperMD**） | `defineMode("hypermd")`，`HyperMD` 56 处 |
| **md 解析** | **JavaScript**（remark-parse v8 时代 tokenizer） | `tokenizeInline`/`blockTokenizers` |
| **md → hast** | **JavaScript**（`mdast-util-to-hast`） | 源码内原始字符串 |
| HTML 消毒 | JavaScript（DOMPurify） | `FORBID_TAGS`/`RETURN_DOM_FRAGMENT` |
| 公式 / 图表 / 高亮 | JavaScript（MathJax / Mermaid / Prism） | 独立 `lib/*.min.js` |
| **唯一非 JS 部分** | **C++ / Objective-C++** | 2 个 `binding.node` + `fontsMac.mm` |

**一句话**：Obsidian 是一个**几乎纯 JavaScript 的 Electron 应用**——源码用 TypeScript 写、编译成 JS 跑在 Chromium 里；**渲染 Markdown 的全部环节都是 JavaScript，没有任何原生/Rust/WASM 加速参与**（整个包里唯一的 `.wasm` 是 PDF.js 附带的 `openjpeg.wasm`，用于 JPEG2000 解码，与 md 无关）。

---

## 2. 运行时版本（实测）

从 `Obsidian.exe`（225,470,224 字节）整块 latin-1 解码后正则取得：

| 组件 | 版本 |
|---|---|
| Electron | **43.3.0** |
| Chromium | **150.0.7871.212** |
| Node.js | **24.18.1** |

⚠️ 版本串**不在** `app.js` 里：`app.js` 只在运行期读 `process.versions.electron`（offset 685,045），未硬编码任何版本号；`%APPDATA%\obsidian\obsidian.log` 也只记录应用版本（1.13.7），不含 Electron 版本。**必须扫描主可执行文件才能拿到。**

安装目录含完整 Chromium 运行时：`LICENSES.chromium.html`(20.3 MB)、`icudtl.dat`、`v8_context_snapshot.bin`、`snapshot_blob.bin`、`chrome_100/200_percent.pak`、`dxcompiler.dll`(25.6 MB)、`d3dcompiler_47.dll`、`libEGL/libGLESv2.dll`、`vk_swiftshader.dll`。

`%APPDATA%\obsidian\` 出现 `DawnGraphiteCache` / `DawnWebGPUCache` → **渲染进程启用了 WebGPU（Dawn 后端）**，不只是 WebGL。

---

## 3. 源码语言是 TypeScript（4 个 helper 钉死）

TypeScript 编译器在把 `async/await`、`for...of`、装饰器等向下编译到低版本目标时，会**在产物里注入具名 helper**。这些 helper 名是**属性名/函数名，压缩器不会改**，因此是判定"源码是否为 TS"的可靠锚点。

在 `app.js` 中命中：

| helper | 命中数 | 字符偏移 | 说明 |
|---|---|---|---|
| `__createBinding` | 1 | 33,702 | TS 命名空间/`import *` 降级 |
| `__spreadArray` | 1 | 50,057 | 数组展开降级 |
| `__awaiter` | 1 | 223,935 | `async` 降级 |
| `__generator` | 1 | 224,251 | 同上（状态机） |

**判读**：

- `__awaiter` 与 `__generator` 相距仅 316 字符 → 同一段 helper 块，典型 TS 输出形态；
- `tslib` **0 命中** → 不是 `importHelpers` 从 tslib 引入，而是按 TS 默认行为**内联注入**；
- 尽管源码是 TS，产物里**找不到** `TypeScript`、`.d.ts` 字样（类型在编译期被完全擦除）；
- ⚠️ 这证明的是**源码语言**，不是"Obsidian 用了某个 TS 版本"——无法从产物反推 TS 版本。

**旁证**：
- `refs\Obsidian-API\obsidian.d.ts` 是官方发布的插件 API 类型定义（8,498 行），说明插件生态以 TS 为一等公民；
- `lib/readability.d.ts` 随第三方库一起打包；
- `electron-main.js`（Electron 主进程，13,407 字符）是**未压缩、可读的 CommonJS**，tab 缩进、`let` + `require` 风格——与渲染进程一次成型的手写风格一致。

---

## 4. 渲染 Markdown 的语言：全部是 JavaScript

**没有任何一层是 C++ / Rust / WASM。** 完整链路（承 `Obsidian-MD表格渲染机制.md`）：

```
markdown 文本
  ↓  remark-parse v8 时代 tokenizer        ← JavaScript
     tokenizeInline 17 处 / blockTokenizers 8 处 / inlineTokenizers 15 处
  ↓  mdast（抽象语法树）
  ↓  mdast-util-to-hast                     ← JavaScript
  ↓  hast（HTML 抽象语法树）
  ↓  HTML 序列化
  ↓  DOMPurify（FORBID_TAGS / RETURN_DOM_FRAGMENT）
  ↓  DocumentFragment → importNode → DOM
```

### 4.1 解析层为何判定为 remark-parse v8 时代架构

`tokenizeInline`、`blockTokenizers`、`inlineTokenizers` 是 **remark-parse v8 及更早**的 tokenizer 架构特征；现代 micromark 体系不会有 `tokenizeInline`。实测：

| 关键词 | 命中 |
|---|---|
| `tokenizeInline` | 17 |
| `blockTokenizers` | 8 |
| `inlineTokenizers` | 15 |
| `micromark` | **0** |
| `markdown-it` | **0** |
| `unified` | **0** |
| `remark` | **0** |

⚠️ **`unified`/`remark` 0 命中不代表没用**：包名只存在于 `package.json`，代码里不会出现。真实情况是 Obsidian 把这些库**内联（vendored）进 app.js**，只保留方法名与属性名。

### 4.2 `mdast-util-to-hast` 已被直接证实

`app.js` offset 1,348,768 处存在该库的**原始源码片段**（webpack 模块化的 `n(9650)` 风格，非 Obsidian 自研）：

```js
console.warn("mdast-util-to-hast: deprecation: `allowDangerousHTML` is nonstandard, use `allowDangerousHtml` instead")
```

配套证据：
- `mdast-util-definitions expected node`（offset 202,386）
- `allowDangerousHtml` **6 处**（18,064 / 18,547 / 1,348,843 / 1,348,882 …）
- 同段落含 `mustUseProperty`、`attributes`/`properties` 构造、`footnoteById`/`footnoteOrder`/`hProperties` → property-information 的 schema 组合

⚠️ 这条**推翻**了上一轮报告把 mdast→hast 归入"只能推断"的保守表述：**转换库身份现在是实证**。但"新旧两个选项名同时被处理"只能说明版本早于该选项彻底改名（约 v10 前后），**具体版本号仍无法从产物反推**。

⚠️ 反向教训：`property-information`、`hast-util`、`stringify-entities`、`html-void-elements`、`space-separated-tokens`、`comma-separated-tokens` 全部 **0 命中**，但 offset 202,386 的上下文里**明明就是 property-information 的代码**。⇒ **"字符串 0 命中" ≠ "库不存在"**，必须结合上下文取证。

### 4.3 消毒层

| 关键词 | 命中 | 偏移 |
|---|---|---|
| `DOMPurify` | 3 | 1,723,147 / 2,398,481 / 3,808,868 |
| `FORBID_TAGS` | 3 | 1,714,499 / 1,714,524 / 1,723,405 |
| `RETURN_DOM_FRAGMENT` | 2 | 1,714,817 / 1,723,382 |

`FORBID_TAGS: ["style"]` 正是内联 `<style>` 会被剥离、样式只能走 CSS 变量的原因。

---

## 5. 前端展示层：HTML + CSS + 原生 JS，零框架

### 5.1 没有前端框架

| 探测点 | 命中 |
|---|---|
| `__REACT_DEVTOOLS_GLOBAL_HOOK__` | **0** |
| `__VUE_DEVTOOLS_GLOBAL_HOOK__` | **0** |
| `svelte` | **0** |

⇒ Obsidian 的 UI 是**命令式原生 DOM 操作**（自研 `createEl`/`createDiv` 一类封装），不是声明式组件树。这也解释了为什么插件 API 直接暴露 `HTMLElement` 与 `createEl`。

### 5.2 入口 `index.html`（1.4 KB，全量脚本加载顺序）

```html
<meta http-equiv="Content-Security-Policy"
      content="style-src 'unsafe-inline' 'self' https://fonts.googleapis.com">
<body class="theme-dark">
  lib/codemirror/codemirror.js → overlay.js → markdown.js → cm-addons.js → vim.js → meta.min.js
  lib/moment.min.js → lib/pixi.min.js → lib/i18next.min.js → lib/scrypt.js → lib/turndown.js
  enhance.js → i18n.js → app.js
```

**关键判读**：

- **CodeMirror 5 是启动期同步加载的**（6 个文件），即 HyperMD 高亮层先行就绪；
- `mermaid` / `mathjax` / `prism` / `pdfjs` **都不在 `index.html` 里** → 它们**按需动态加载**（用到才拉），这是首屏体积控制手段；
- CSP 只放宽了 `style-src`（允许内联样式），`script-src` 未放宽 → 插件脚本走 Obsidian 自己的加载器。

### 5.3 双编辑器栈并存

| | CodeMirror 5 | CodeMirror 6 |
|---|---|---|
| 位置 | `lib/codemirror/*.js`（独立文件，390.8 KB 核心 + 549.5 KB modes + 243.4 KB vim） | **打包进 `app.js`** |
| 证据 | `defineMode(`1、`defineMIME(`1、`CodeMirror.getMode`5、`HyperMD`**56** | `EditorView`3、`EditorState`2、`StateField`1、`ViewPlugin`1、`Decoration`1、`syntaxTree`2、`EditorSelection`2、`StateEffect`2 |
| 角色 | 语法高亮 / 装饰（`HyperMD-table-row` 等类名来源） | 主编辑器内核（含表格 widget 的 ViewPlugin） |

⚠️ CM6 相关标识高度集中于 offset **245,000–248,000**（库本体）＋ 300,871 / 472,130 / 474,341（Obsidian 自用点），符合"vendored 库 + 少量调用"的分布。

⚠️ `runMode` / `overlayMode` 在 `app.js` 中 0 命中，但在 CM5 核心文件 `lib/codemirror/codemirror.js` 中 `runMode` 有 3 处 —— **按文件分工定位，比全局计数更可靠**。

### 5.4 样式

`app.css` **622.2 KB / 21,708 行**，**未压缩**（可读的选择器与 `--` 变量），是获取类名与设计意图最快的入口（见主报告 §6）。

---

## 6. 打包内第三方库清单（按体积）

`obsidian.asar` 共 **358 个文件 / 25,787,463 字节**：

| 体积 | 文件 | 用途 |
|---|---|---|
| 3.7 MB | `app.js` | 主程序（TS 编译产物，已压缩） |
| 2.8 MB | `lib/mermaid.min.js` | Mermaid 图表 |
| 1.3 MB | `lib/mathjax/tex-chtml-full.js` | **MathJax** 公式（**非 KaTeX**：`KaTeX` 0 命中） |
| 1.1 MB | `lib/pdfjs/pdf.worker.min.mjs` | PDF 渲染 worker |
| 732.6 KB | `lib/defuddle.full.js` | 网页正文提取（剪藏） |
| 622.2 KB | `app.css` | 全部样式 |
| 563.0 KB | `lib/prism.min.js` | 代码块高亮 |
| 553.4 KB | `lib/pdfjs/pdf.min.mjs` | PDF 主库 |
| 549.5 KB | `lib/codemirror/modes.min.js` | CM5 语言模式 |
| 477.4 KB | `lib/pdfjs/pdf.viewer.min.mjs` | PDF 查看器 |
| 475.7 KB | `lib/pixi.min.js` | PixiJS（Canvas/WebGL 2D） |
| 430.5 KB | `starter.js` | 首次启动引导 |
| 390.8 KB | `lib/codemirror/codemirror.js` | **CM5 核心** |
| 368.5 KB | `help.js` | 帮助面板 |
| 366.3 KB | `lib/moment.min.js` | 日期 |
| 251.3 KB | `lib/pdfjs/wasm/openjpeg.wasm` | **包内唯一 `.wasm`**（JPEG2000 解码） |
| 233.7 KB | `worker.js` | Web Worker |
| 195.0 KB | `main.js` | 渲染进程引导 |
| 129.9 KB | `i18n.js` + `i18n/*.txt` × 48 | 国际化（i18next 运行时 40.4 KB） |
| 31.8 KB | `lib/readability.js` + `.d.ts` | Readability（剪藏） |
| 17.5 KB | `lib/scrypt.js` | 本地加密 |
| 10.4 KB | `lib/turndown.js` | HTML → Markdown（剪藏） |

另有 `sandbox/*.md` ×3（新建库引导文档）、`index.html`/`starter.html`/`help.html`、`icon.png`。

**旁证**：`lib/.DS_Store`(8.0 KB) 被打进了 macOS 构建产物，且 `app.js` 里有大量 `"darwin" === process.platform` 特判 → **主力开发平台是 macOS**。

---

## 7. 唯一的非 JavaScript 部分

| 模块 | 文件 | 语言 |
|---|---|---|
| `btime` | `binding.node`(151,312 B) + `index.js` | **C++**（Node-API 原生插件） |
| `get-fonts` | `binding.node`(157,456 B) + `index.js` | **C++** |
| `get-fonts` | `fontsMac.mm`(761 B) | **Objective-C++**（macOS 本地字体枚举） |
| `node-addon-api` | `napi.h`/`napi-inl.h`/`*.gypi` | C++ 头文件与 node-gyp 构建配置 |

总量约 **300 KB，仅 2 个模块**，且都与**文件系统时间戳**和**系统字体枚举**有关——**渲染链路完全不经过它们**。

这些 `.node` 同时出现在 `resources\app.asar`（打包索引内）与 `resources\app.asar.unpacked\`（真实落盘副本），因为 Node 原生插件无法从 asar 内直接 `dlopen`，必须解包。

`app.asar` 自身：40 个文件 / 480,000 字节（解压 732.8 KB），含 `@electron/remote`（`remote.initialize()` 启用旧版 remote 模块）与上述原生模块。

---

## 8. 取证方法与坑

### 8.1 可靠锚点

1. **属性名 / 方法名 / 类名 / 字符串常量**——压缩器只改**局部标识符**，这些不动。本次全部关键结论都建立在此；
2. **包名不可靠**：只出现在 `package.json`，代码里通常没有（见 §4.2 的反向教训）；
3. **版本号不在 JS 里**：Electron/Chromium/Node 版本必须扫主可执行文件；
4. **`app.css` 未压缩**：类名与 CSS 变量的最佳入口；
5. **`electron-main.js` 未压缩**：主进程逻辑可直接阅读。

### 8.2 本次踩到的坑

| 坑 | 现象 | 规避 |
|---|---|---|
| 短搜索词 + 大小写不敏感 | grep `lezer` 命中 CM5 的 `enableZeroWidthBar`（`enab**leZer**oWidthBar` 小写化后含 "lezer"） | 用更长的模式，或核对上下文 |
| 数字量词当版本号 | 搜 `CodeMirror 6` 得 0，误以为没有 CM6 | 改搜属性名（`EditorView` 等） |
| 输出截断丢掉路径行 | `Select-Object -Last 3` 把 `### 文件:行` 行截掉，导致无法判断命中在哪个文件 | 保留路径行，或改用按文件精确计数 |
| 全局计数掩盖文件分工 | `runMode` 在 app.js 为 0，在 CM5 文件为 3 | 按文件分别探测 |
| 二进制版本文本不在文件头部 | 扫 exe 前 20 MB 找 `Electron/` 得 0 | 整文件扫描（latin-1 解码 + 正则） |
| 「缓存文件无用」的想当然 | 曾判 `%APPDATA%\obsidian\obsidian-1.13.7.asar` 为可删的更新包缓存 | 读 `obsidian.log` 才发现 `Loaded updated app …` —— **它才是实际被加载的那个 asar** |

### 8.3 脚本

| 脚本 | 作用 |
|---|---|
| `scripts\obsidian-asar.py` | asar 归档 `list` / `extract` / `grep` |
| `scripts\obsidian-ctx.py` | 按字符偏移取窗口（压缩单行文件的唯一可读方式） |
| `scripts\obsidian-lang-probe.py` | 技术栈标识批量计数（本报告主探针，含 CM5/CM6/md 链/TS helper/框架探测） |
| `scripts\obsidian-electron-version.py` | 扫主可执行文件取 Electron/Chromium/Node 版本 |

> `scripts\` 被 gitignore 且随时可能清空，**源码以文档为准**（本报告与主报告 §12 均内嵌脚本源码）。

---

## 9. 对既有结论的修正

| # | 原结论 | 修正 |
|---|---|---|
| 1 | `%APPDATA%\obsidian\obsidian-1.13.7.asar` 是"更新包缓存，现已无用途，可清理" | **错**。`obsidian.log` 明确记录 `Loaded updated app <该文件>` —— Obsidian 自动更新流程是「下载 asar 到 userData → 下次启动加载它」。**不可删**。 |
| 2 | md → hast 的转换（`mdast-util-to-hast`）"版本号只能推断" | 库**身份**已实证（源码内原始警告字符串）；但**版本号**仍反推不出，仅能判断早于 `allowDangerousHtml` 彻底改名之前。 |
| 3 | 解析层"自研解析器 / micromark 体系"（更早一轮） | 已修正为 **remark-parse v8 时代 tokenizer 架构**（`tokenizeInline` 等 40 处）。 |

---

## 10. 仍未证实 / 不要过度断言

- **打包工具**：`esbuild`/`webpack`/`rollup`/`vite` 字符串全 **0 命中**，但代码呈 webpack 风格模块系统（`n(9650)`、`e.exports`、数字模块 ID）⇒ **只能推断为 webpack 系**，不能断言。
- **hast → HTML 的序列化库身份**：`hast-util`/`stringify-entities` 等 0 命中，不排除是同名被压缩或自研序列化 ⇒ **未证实**。
- **TypeScript 版本**：类型已擦除，无从反推。
- **`app.asar` 与 `%APPDATA%` 两个 1.13.7 asar 的字节级一致性**：两者 size 均为 25,787,463 B，但未做哈希比对。
- **移动端**（iOS/Android）未纳入本次取证范围。
- 上一轮主报告 §11 列出的其余存疑项（HyperMD 与 Obsidian 的渊源、`nO` 字段身份、行内代码内 `|`、中文按码元算宽、列表内表格、其它 post-processor、Catalyst 1.14 差异）**仍然有效**。
