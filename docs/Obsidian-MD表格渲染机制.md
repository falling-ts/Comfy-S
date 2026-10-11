# Obsidian Markdown 表格渲染机制(逆向 1.13.7 / 1.12.4)

> **版本说明(重要)**: 本报告的核心结论已在本机**两个版本上逐项验证** ——
> ⚠️ 根 `scripts\` 临时目录已于 2026-10-11 移除，下文的 `scripts\obsidian-*.py` 仅作历史记录，源码以内嵌于本文档为准。
> **1.13.7**(当前运行版本, `C:\Program Files\Obsidian\resources\obsidian.asar`, 24.59 MB / 358 个文件)
> 与 **1.12.4**(取证时的版本, 22.9 MB / 352 个文件)。
>
> **两版的表格渲染机制完全相同**: 关键标识的命中数逐一相等
> (`HyperMD-table-row` 3、`hypermd` 6、`StreamLanguage` 1、`cm-table-widget` 1、
> `cellChildMap` 4、`tokenizeInline` 17、`cm-embed-block` 5), 核心代码逐字对应,
> **仅 minifier 分配的标识符与字符偏移不同**。验证过程与两版偏移对照见 §13.8。
>
> 正文代码片段保留取证时的原始 minified 形式(即 **1.12.4 的标识符**), 仅局部变量名被压缩 ——
> minifier 改不动**属性名与字符串**, 所以类名/字段名全部可信。
> 版权归 Obsidian 所有, 此处仅作技术学习与实现参考。
>
> **配套文档**: 本报告只回答"表格怎么渲染"。整个 Obsidian 的**技术栈与实现语言**
> (运行时版本、源码语言、md 渲染链各层用什么语言实现、前端框架、原生模块边界)见
> **`Obsidian-技术栈与实现语言调研.md`** —— 那份报告中的运行时版本
> (Electron 43.3.0 / Chromium 150 / Node 24.18.1)与本文的渲染结论相互印证。

---

## 1. 结论速览

Obsidian 的表格有**两条独立渲染路径**, 但它们**共用同一套 CSS**:

| | 阅读模式(Reading View) | 实时预览(Live Preview / 编辑态) |
|---|---|---|
| 载体 | 普通 DOM | CodeMirror 6 的 `WidgetType` |
| 容器类名 | `.markdown-rendered`(块级元素另有 `.el-*` 包装, 置信度见 §11) | `.cm-embed-block.cm-table-widget.markdown-rendered` |
| 管线 | md → remark-parse v8(mdast) → mdast-util-to-hast → DOMPurify → DOM | **渲染器同源**; 仅"哪些行算表格"由 CM5 hypermd 词法层判定 |
| 可编辑 | 否 | **是**: 每个单元格是一个**嵌套的独立 CM6 编辑器实例** |

关键点: widget 容器上**同时挂了 `markdown-rendered`**, 这是两条路径共用样式的实现手法 ——
不管内容来自阅读模式还是 Live Preview, `.markdown-rendered table { ... }` 都能命中。

---

## 2. 解析层: remark-parse v8 时代的 tokenizer 架构(不是 markdown-it)

在 3.7 MB 的 `app.js` 里统计关键词出现次数:

| 标识 | 次数 | 说明 |
|---|---|---|
| `markdown-it` | **0** | 完全没用这个库 |
| `micromark` | **0** | 字符串级无痕迹(被打包合并) |
| `mdast` | 2 | |
| `footnoteDefinition` | 10 | **mdast 命名风格**的节点类型 |
| `thematicBreak` | 9 | 同上 |
| `tableCell` | 45 | 表格单元格节点类型 |
| `HyperMD` | 50 | 语法高亮行类名 |
| `hmdTable` | 32 | 表格 tokenizer 状态字段 |

`obsidian.d.ts` 里 `SectionCache.type` 暴露了解析器产出的节点类型清单:

```ts
type: 'blockquote' | 'callout' | 'code' | 'element' | 'footnoteDefinition' | 'heading'
    | 'html' | 'list' | 'paragraph' | 'table' | 'text' | 'thematicBreak' | 'yaml' | string;
```

`footnoteDefinition` / `thematicBreak` 是 **mdast 的 `FootnoteDefinition` / `ThematicBreak`** 的小驼峰形式
(markdown-it 用的是 `fence`、`hr` 这套完全不同的命名), 所以解析层属于 mdast 体系。

**再往下定位到具体架构: 是 `remark-parse` v8/v9 时代的 tokenizer 实现, 不是现代 micromark。**
判据是解析器内部使用的 API 形态 —— 看下面这段表格 block tokenizer 的开头与结尾:

```js
if (!this.options.gfm) return;                  // ← remark-parse v8 读取 options 的方式
...
e(y)({type: "tableCell", padding: t, children: this.tokenizeInline(r, o)}, b)
//                                              ↑ tokenizeInline() 是 v8 的 Parser 方法
```

`this.options.gfm` + `this.tokenizeInline()` + `blockTokenizers` 这套接口属于 **remark-parse v8**;
现代 `micromark` / `mdast-util-from-markdown` 是完全不同的构造(状态机 + `effects`),
**不会出现 `tokenizeInline` 这个方法名**。配合下面的解析选项可判定: Obsidian 是把
**remark-parse v8 时代的 unified 栈整体打进了 bundle**, 而非自研解析器。

配套的解析选项(模块 1393):

```js
e.exports = {position: !0, gfm: !0, commonmark: !1, pedantic: !1, blocks: n(5810)}
```

`gfm: true` 是表格能被解析的前提(表格是 GFM 扩展, 不在 CommonMark 里)。

表格 tokenizer 内部的字面量常量暴露了它认识的语法元素:

```js
var r = "\t", o = "\n", a = " ", s = "-", l = ":", c = "\\", u = "|",
    h = 1, p = 2, d = "left", f = "center", m = "right";
```

即: `|` 分隔、`\` 转义、`:` 定义对齐(映射到 left/center/right)。
`tableCell` 节点还带一个 **`padding` 字段**:

```js
e(y)({type: "tableCell", padding: t, children: this.tokenizeInline(r, o)}, b)
```

这个 `padding` 就是源码里单元格两侧的对齐空格 —— 见 §7。

---

## 3. 语法高亮层: CM5 mode 被 StreamLanguage 搬进了 CM6

这是本次逆向最有意思的一处。Obsidian **确实**打包了完整的 CodeMirror 5.64.0
(`lib/codemirror/codemirror.js`, 版本号字符串实测 `5.64.0`), 但**主编辑器是 CodeMirror 6**。

CM6 的证据 —— `app.js` offset 245681 是 `@codemirror/view` 的完整导出表:

```js
n.d(t, {Decoration:()=>Vn, EditorView:()=>Uo, ViewPlugin:()=>zi, WidgetType:()=>Rn,
        atomicRanges:()=>Gi, ...})
```

> 这也解释了为什么前面按字面搜 `EditorView` 只有 3 次命中 —— 类名被 minifier 重命名成了
> `Uo` / `Vn` / `Rn` / `zi`, 字面量只剩导出表的键名。**只按字符串统计会严重误判**。

而 CM5 的 `getMode` 与 CM6 的 `StreamLanguage` 在同一行里会合了:

```js
X$ = Hd.define(CodeMirror.getMode({}, {name:"hypermd"})),
$$ = Hd.define(CodeMirror.getMode({}, {name:"hypermd", front_matter:!1, table:!1,
      fencedCodeBlockHighlighting:!1, taskLists:!1, headers:!1, blockquotes:!1,
      indentedCode:!1, lists:!1, hr:!1, blockId:!1}))
```

(`Hd` = `StreamLanguage`, 已由导出表 `StreamLanguage:()=>Hd` 对应确认)

**读法**: Obsidian 把自己写的 CM5 mode(`name:"hypermd"`)用 `StreamLanguage.define()` 包成 CM6 语言扩展,
从而在 CM6 下继续产出 CM5 时代的 `HyperMD-*` 行类名 —— 这样海量旧 CSS 与第三方主题**不用改**。

**两个变体是重点**: 第二份把 `table` / `headers` / `lists` / `blockquotes` / `hr` / `blockId` 等
**所有块级特性全部关掉**。这显然是给**表格单元格的子编辑器**用的 —— 单元格里只需要行内高亮,
不需要块级解析(否则单元格里的 `- ` 会被误判成列表)。这是嵌套编辑器架构的一个必要细节。

表格行的类名生成逻辑(节选):

```js
0 == ie && (b += " line-HyperMD-table-".concat(W," line-HyperMD-table-row line-HyperMD-table-row-").concat(te," line-parse-next"),
            o.hmdTableRTL && (b += " line-HyperMD-table-rtl")),
W === uj.NORMAL && (0 === o.hmdTableCol && /^\s*\|$/.test(t.string.slice(0, t.pos)) || t.match(/^\s*$/, !1))
  ? b += " hmd-table-sep hmd-table-sep-dummy"
  : o.hmdTableCol < ne && (b += " hmd-table-sep hmd-table-sep-".concat(ie), o.hmdTableCol += 1)
```

`b` 是累积的行 class 字符串, `t.pos` / `t.peek()` / `t.match()` 是 **CM5 StreamParser 的 token 接口** ——
进一步印证这段就是 CM5 mode 的代码。

---

## 4. 阅读模式渲染: mdast → hast, 用的是 mdast-util-to-hast 的 table handler

`app.js` 里找到了表格转 hast 的**完整函数原文**:

```js
e.exports = function(e, t) {
  var n, a, s, l, c, u = t.children, h = u.length, p = t.align || [], d = p.length, f = [];
  for (; h--;) {
    for (a = u[h].children, l = 0 === h ? "th" : "td", n = d || a.length, s = []; n--;)
      c = a[n], s[n] = e(c, l, {align: p[n]}, c ? o(e, c) : []);
    f[h] = e(u[h], "tr", r(s, !0))
  }
  return e(t, "table", r([
    e(f[0].position, "thead", r([f[0]], !0))
  ].concat(f[1] ? e({start: i.start(f[1]), end: i.end(f[f.length-1])}, "tbody", r(f.slice(1), !0)) : []), !0))
};
```

逐条读出的事实:

1. **`t.align` 数组驱动对齐**, 每个单元格拿到 hast 属性 `{align: p[n]}` ——
   注意是 **HTML 属性 `align`**, 不是 `style="text-align:..."`。CSS 侧靠 `[align="center"]` 选择器接住(§6)。
2. **首行是 `<th>`, 其余是 `<td>`**: `l = 0 === h ? "th" : "td"`。
3. 循环是 `for (; h--;)` **倒序**填充 `f[]`, 所以 `f[0]` 才是第一行 —— 下面 `f[0]` 进 `<thead>`、`f.slice(1)` 进 `<tbody>` 与此一致。
4. **没有数据行时只有 `<thead>`**: `f[1] ? ... : []`。
5. `<tbody>` 的 position 被显式设成"第二行起点 → 末行终点"。

同时 `app.js` 里还打包了 **parse5 的 tree-adapter 规则**(`thead`/`tbody`/`tfoot`/`tr`/`td`/`th`/`colgroup`/`caption` 各自的分组规则),
说明中间态是 hast, 再由 hast 序列化成 DOM/HTML。

另外找到了一处阅读模式的挂载代码, 完整暴露了管线:

```js
s = this.containerEl = createDiv("cm-embed-block " + a);
var l = s.createDiv("markdown-rendered"),
    c = _x(o),          // ① md 文本 → AST
    u = Qx(c);          // ② 中间变换(任务列表/嵌入等)
zC(c, "checklist", function(e) { ... e.data.hProperties["data-line"] = String(t) });
var h = ML(Xx(c));      // ③ AST → hast → DOM
l.toggleClass("rtl", i.vault.getConfig("rightToLeft"));
l.toggleClass("show-indentation-guide", i.vault.getConfig("showIndentGuide"));
l.appendChild(h);       // ④ 挂进 .markdown-rendered
pq.postProcess(this.app, {docId: sc(16), sourcePath: ...});
```

---

## 5. Live Preview: `cm-table-widget`

### 5.1 widget 构造器(字段全暴露)

```js
o.rows = [];            // 二维: rows[row][col] = cell 对象
o.alignments = [];      // 每列对齐方式 ["left"|"center"|"right"|...]
o.colWidths = [];       // 每列宽度(用于源码对齐)
o.isMalformed = !1;     // 列宽不一致标记
o.tableEl = null;       // 真正的 <table> 元素
o.selectedCells = [];   // 框选中的单元格
o.selectionAnchor = null;
o.selectionHead = null;
o.cellChildMap = new Map;   // cell -> [子编辑器/子组件]
o.doc = i;                  // CM6 Text(整张表的源码)
o.containerEl = createDiv({
  cls: "cm-embed-block cm-table-widget markdown-rendered",
  onpointerdown: function(e) { e.target === e.currentTarget && e.preventDefault() }
});
o.isDocComplete = r;
```

`cls` 三个类名各司其职:
- `cm-embed-block` —— CM6 嵌入块的通用定位/交互样式
- `cm-table-widget` —— 表格专属
- **`markdown-rendered`** —— **复用阅读模式样式**(设计上最关键的一手)

### 5.2 表格 DOM 构建: 用原生 DOM API

```js
var E = [], M = (y = r.length, u.insertRow(y));
r.push(E);
for (k = 0; k < m; k++) {
  var S = M.insertCell();
  (P = new mq(this, y, k)).init(S, -1, -1), E[k] = P
}
```

`u.insertRow()` / `M.insertCell()` 是 **HTMLTableElement / HTMLTableRowElement 的原生方法** ——
证明产物是**货真价实的 `<table><tr><td>`**, 不是 div 拼的假表格。

外层容器:

```js
i.createDiv("table-wrapper", function(t) {
  t.append(u),                                     // 装 <table>
  t.createDiv("table-row-btn", function(t) {       // 底部「加行」按钮
    Jm(t, "lucide-plus"), Cv(t, mm.table.actionRowAfter()),
    t.addEventListener("pointerdown", e => e.preventDefault()),
    t.addEventListener("click", () => e.insertRow(e.rows.length, 0))
  }),
  t.createDiv("table-col-btn", function(t) { ... }) // 右侧「加列」按钮
})
```

图标用 **Lucide**(`lucide-plus`), 无障碍标签走 `i18n`(`mm.table.actionRowAfter()`)。

### 5.3 每个单元格是嵌套的独立 CM6 编辑器

这是 Obsidian 表格实现里最重的一块。CSS 直接暴露了嵌套结构:

```css
.markdown-source-view.mod-cm6 .cm-table-widget .cm-content,
.markdown-source-view.mod-cm6 .cm-table-widget .cm-line { ... }
.markdown-source-view.mod-cm6 .cm-table-widget .cm-scroller { ... }
```

`cm-content` / `cm-line` / `cm-scroller` 是 **CM6 编辑器自己的 DOM 结构** ——
它们出现在 `cm-table-widget` **内部**, 说明单元格里跑着独立的 CM6 实例。

子组件的挂载与回收:

```js
// 渲染进单元格: 有子节点就用子节点, 空的就塞一个 <br>
.from(n.childNodes) : [createEl("br")];
(t = e.contentEl).append.apply(t, i), e.dirty = !1, e.setTextDir(), this.postProcess(e)

// 单元格内容变了 → 移除旧的子组件
t.prototype.removeChildren = function(e) {
  var t = this.cellChildMap;
  if (t.has(e)) { var n = t.get(e); t.delete(e); for (var i = 0, r = n; i < r.length; i++) this.removeChild(r[i]) }
}

// 表格整体重建后 → 把已不在 rows 里的 cell 全部回收(防泄漏)
t.prototype.cleanupChildren = function() {
  for (var e, t = this, n = t.cellChildMap, i = t.rows, o = new Set, a = 0, s = i; a < s.length; a++)
    for (var l = 0, c = s[a]; l < c.length; l++) o.add(c[l]);
  for (var h = 0, p = Array.from(n.keys()); h < p.length; h++) { u = p[h];
    if (!o.has(u)) { var d = n.get(u); n.delete(u); for (var f = 0, m = d; f < m.length; f++) this.removeChild(m[f]) } }
}
```

`cellChildMap` 的值是**数组**(`for ... r = n; i < r.length`), 即一个单元格可挂多个子组件
(编辑器 + 其他附件)。

选中多格时把手写权限收掉, 防止并发编辑冲突:

```js
o.updateCellReadonly = yc(function() {
  var e = o, t = e.selectionAnchor, n = e.selectionHead, i = e.editor;
  if (i.tableCell) { var r = !(!t || !n); i.tableCell.setReadonly(r) }
}, 50, !0)     // yc = debounce(50ms), 第三参 true = 立即执行一次
```

另外 `i.editor.tableCell` 说明 Obsidian 往 **CM6 的 EditorState 上挂了一个自定义 `tableCell` 字段**,
记录"当前光标落在哪个单元格", 供键盘导航与上面的只读判定使用。

`is-loading` 类说明 widget 有加载态(大表或渲染未完成):

```css
.markdown-source-view.mod-cm6 .cm-table-widget.is-loading { padding: 0; margin: 0 !important; }
```

### 5.4 行/列拖拽手柄

CSS 与 JS 都出现了 `.table-row-drag-handle` / `.table-col-drag-handle`, 以及 `is-dragging`、
`mod-active-row-handle` / `mod-active-col-handle`(移动端)。即表格支持**拖动整行/整列重排**。

### 5.5 widget 的替换时机: 由 `HyperMD-table-row` 行类名驱动

真正把源码换成渲染表格的地方找到了。它挂在语法树的遍历上, **靠行类名识别表格**:

```js
f.iterate({enter: function(t) {
  var i = t.type, r = t.from, a = t.to, s = i.prop(Qd);   // Xd/Qd = 行 class 属性
  if (s && (Z(r), J(r)), s && !(-1 !== G || -1 !== Y))
    if ((re = new Set(s.split(" "))).has("hmd-codeblock")) ;
    else if (re.has("formatting-math-begin")) ...
}});
```

表格范围的累积与收尾(同一段代码的表格分支):

```js
re.has("HyperMD-table-row") && (Z(r), r - Q > 1 && J(r), -1 === Y && (Y = r), Q = a)
```

即: 每遇到一行 `HyperMD-table-row` 就更新结束位置 `Q`; 若**这一行与上一行不连续**(`r - Q > 1`),
先把前面那张表收尾(`J(r)`); `Y` 记起始行。最终 `J` 负责产出装饰器:

```js
J = function(t) {
  if (-1 !== Y && Q < t) {
    for (var i = h.changes, r = h.docChanged, o = m.slice(Y, Q),
             s = Q !== f.length - 1 || f.length === m.length, l = i.invertedDesc.mapPos(Y),
             c = null, u = 0, p = x; u < p.length; u++) {
      var d = p[u], v = d.start;
      if (l === v || Y === v || i.length >= v && Y === i.mapPos(v)) {
        if (s ? d.receiveUpdate(h, o) : !r || d.receiveIncompleteUpdate(h, o)) {
          c = d, x.remove(d); break                       // 旧 widget 可增量复用
        }
      }
    }
    if (!FA(g, y, Y, Q)) {
      c || (c = new gq(n, e, o, s));                       // 否则新建表格 widget
      var b = Y > 0 && Y > JA(h.newDoc) + 1;
      C.push(w({widget: c, side: 1, block: !0, inclusiveStart: b}, Y, Q)),   // ← 核心
             Gl.isAndroidApp && Q !== m.length && C.push(k6.range(Q + 1))
    }
    c && (c.setPos(Y, Q), c.receiveSelection(h), a.push(c)), Y = -1, Q = -1
  }
};
```

要读出的几点:

1. **`w({widget: c, side: 1, block: !0, inclusiveStart: b}, Y, Q)`** —— 这是一个
   **`Decoration.replace`**, 把 `[Y, Q)` 这一整段表格源码**整体替换成一个 block 级 widget**。
   `block: true` 是关键: 表格是块级元素, 不能用行内 widget 的定位方式。
2. **widget 会增量复用**: 先尝试让旧 widget `receiveUpdate(update, text)` 接收变化, 只有失败
   (或结构已不兼容)才 `new gq(...)`。这就是编辑表格时不会整块闪烁的原因。
3. **`inclusiveStart`** 由 `Y > 0 && Y > JA(doc) + 1` 决定 —— 表格前面还有内容时才启用,
   影响边界处的光标归属。
4. **Android 上额外补一个 range**(`k6.range(Q + 1)`) —— 移动端光标定位的补偿处理。
5. 收尾后 `Y = -1, Q = -1` 复位。

**因此**: 表格一旦被识别, 就在 Live Preview 里被**整体替换为渲染态 widget** —— 编辑通过
widget 内部那些**嵌套单元格编辑器**完成(§5.3), 而不是"退回源码"。

### 5.6 关键辨析: 表格**不会**因光标进入而退回源码(但与公式/代码块不同)

这一点极易搞错, 因为 Obsidian 对**其他块级元素**确实采用"选区相交就显示源码"的策略。
三个判断函数的原文:

```js
function IA(e, t, n) { return e.from <= n && e.to >= t }              // 区间相交
function OA(e, t, n) { for (var i = 0, r = e; i < r.length; i++)      // 任一选区相交
                       { if (IA(r[i], t, n)) return !0 } return !1 }
function FA(e, t, n, i) { var r = !1;                                 // [n,i] 内有搜索命中
                         return e.between(n, i, function(e, n, i) { if (i === t) return r = !0, !1 }), r }
```

ViewPlugin 里把它们组装成:

```js
var v = t.hasFocus ? d.selection.ranges : [],        // 只在编辑器有焦点时才取选区
    b = function(e, t) { return OA(v, e, t) || FA(g, y, e, t) };   // 语义 = "需要显示源码"
```

再看两个**真实调用点**的差别 —— 这是判定的关键:

```js
// ① 块级公式/代码块(Z): 检查 b(), 即"选区相交 或 搜索命中"
Z = function(i) {
  if (-1 !== G && K < i) {
    ...
    b(G, K) || (o || (o = new v6(n, e, t, r)), C.push(w({widget: o, side: 1, block: !0}, G, K))),
    // ↑ b() 为 true 时【不产出】替换装饰 → 显示源码
    ...
  }
};

// ② 表格(J): 只检查 FA(), 即"只有搜索命中"
J = function(t) {
  if (-1 !== Y && Q < t) {
    ... 尝试复用旧 widget ...
    if (!FA(g, y, Y, Q)) {                       // ← 这里没有 b() / OA()
      c || (c = new gq(n, e, o, s));
      var b = Y > 0 && Y > JA(h.newDoc) + 1;     // ← 注意: 局部变量 b 遮蔽了上面的 b 函数
      C.push(w({widget: c, side: 1, block: !0, inclusiveStart: b}, Y, Q)),
             Gl.isAndroidApp && Q !== m.length && C.push(k6.range(Q + 1))
    }
    ...
  }
};
```

结论(**有直接代码对照, 非推断**):

| 元素 | 撤掉 widget 的条件 | 光标/选区进入时 |
|---|---|---|
| 公式、代码块等 | `OA(选区相交) \|\| FA(搜索命中)` | **退回源码** |
| **表格** | **仅 `FA(搜索命中)`** | **保持渲染态**, 直接编辑单元格 |

所以表格是**特例**: 即使选中整个表格, 它仍是渲染态 widget(选中由 widget 内部的单元格选区逻辑处理),
只有在**表格范围内搜索命中**时才会退回源码, 以便让搜索高亮可见。

> ⚠️ 一个容易踩的阅读陷阱: `J` 里那行 `var b = Y > 0 && ...` **遮蔽**了外层的 `b` 函数,
> 所以 `inclusiveStart: b` 传的是布尔值, 而不是判断函数。粗读这段很容易误以为表格也走了
> `b(...)` 的选区判断 —— 这正是**第二路独立取证最初得出的错误结论**, 见 §13.1。

---

## 6. CSS: 变量与关键规则

### 6.1 变量默认值(`:root`)

```css
--table-border-width: 1px;
--table-white-space: break-spaces;
--table-header-border-width: var(--table-border-width);
--table-header-size: var(--table-text-size);
--table-header-weight: calc(var(--font-weight) + var(--bold-modifier));
--table-line-height: var(--line-height-tight);
--table-text-size: var(--font-text-size);
--table-column-min-width: 6ch;
--table-column-max-width: none;
--table-column-alt-background: var(--table-background);
--table-column-first-border-width: var(--table-border-width);
--table-column-last-border-width: var(--table-border-width);
--table-row-background-hover: var(--table-background);
--table-row-alt-background: var(--table-background);
--table-row-alt-background-hover: var(--table-background);
--table-row-last-border-width: var(--table-border-width);
--table-cell-vertical-alignment: top;
```

`--table-white-space: break-spaces` 很关键: 它让单元格内**连续空格与换行都保留**
(配合 `word-break: normal`), 所以你在表格里敲的空格不会被折叠掉。

### 6.2 主体规则(`app.css` 12628 起, 注释 `/* Tables */`)

```css
.markdown-rendered table {
  margin-block-start: var(--p-spacing);
  margin-block-end: var(--p-spacing);
  word-break: normal;
}
.cm-html-embed table,
.markdown-rendered table {
  border-collapse: collapse;
  line-height: var(--table-line-height);
}
.cm-html-embed td, .markdown-rendered td,
.cm-html-embed th, .markdown-rendered th {
  padding: var(--size-2-2) var(--size-4-2);
  border: var(--table-border-width) solid var(--table-border-color);
  max-width: var(--table-column-max-width);
  min-width: var(--table-column-min-width);
  vertical-align: var(--table-cell-vertical-alignment);
}
.cm-html-embed td, .markdown-rendered td { font-size: var(--table-text-size); color: var(--table-text-color); }
.cm-html-embed th, .markdown-rendered th {
  font-size: var(--table-header-size);
  font-weight: var(--table-header-weight);
  color: var(--table-header-color);
  font-family: var(--table-header-font);
  line-height: var(--line-height-tight);
}
.cm-html-embed th, .markdown-rendered th,
.cm-html-embed td, .markdown-rendered td { text-align: start; }

/* 对齐: 靠 HTML align 属性选择器, 不是 inline style */
.markdown-rendered th[align="left"],   .markdown-rendered td[align="left"]   { text-align: start; }
.markdown-rendered th[align="center"], .markdown-rendered td[align="center"] { text-align: center; }
.markdown-rendered th[align="right"],  .markdown-rendered td[align="right"]  { text-align: end; }

/* 单元格超长 → 省略号 */
.cm-html-embed thead > tr > th, .markdown-rendered thead > tr > th,
.cm-html-embed tbody > tr > td, .markdown-rendered tbody > tr > td {
  white-space: var(--table-white-space);
  text-overflow: ellipsis;
  overflow: hidden;
}
```

三个值得抄的细节:

- **`.cm-html-embed` 与 `.markdown-rendered` 成对出现** —— 直接写在 md 里的 `<table>` HTML 块
  也套用同一套表格样式, 保证两种来源视觉一致。
- **用 `text-align: start/end` 而非 `left/right`** —— RTL 语言下自动镜像。
  但注意对齐属性选择器里 `[align="left"] → start`、`[align="right"] → end`, 语义转译是对的。
- 宽度同时受 `min-width: 6ch` 与 `max-width: none` 约束, 再叠加 `text-overflow: ellipsis`,
  即"列不会窄到挤没, 超长内容省略号"。

### 6.3 Live Preview 侧

```css
.markdown-source-view.mod-cm6 .cm-table-widget {
  --table-drag-handle-size: var(--size-4-4);
  padding: var(--table-drag-handle-size);
  margin: 0 calc(-1 * var(--size-4-4)) !important;
  overflow-x: auto;      /* ← 宽表格横向滚动, 不撑破编辑区 */
  overflow-y: hidden;
}
.is-mobile .markdown-source-view.mod-cm6 .cm-table-widget { --table-drag-handle-size: var(--size-4-6); }

.markdown-source-view.mod-cm6 .cm-table-widget .table-wrapper {
  position: relative;    /* ← 承载行/列按钮的绝对定位 */
  width: fit-content;
}
.markdown-source-view.mod-cm6 .cm-table-widget tr { height: 1px; }
.markdown-source-view.mod-cm6 .cm-table-widget th,
.markdown-source-view.mod-cm6 .cm-table-widget td { height: inherit; }
```

`tr { height: 1px }` + `td/th { height: inherit }` 是**经典等高技巧** ——
`height: 1px` 给出下界, `inherit` 让同行所有单元格取该行实际高度, 于是整行等高。
`padding` 给拖拽手柄留出空间, 再用负 `margin` 把多出来的边距抵消掉, 视觉上不缩进。

---

## 7. 特别行为: 源码会被自动对齐

Obsidian 不只是渲染, 它还会**回写并格式化你的表格源码**。每列有目标宽度(`colWidths`),
渲染前把单元格文本按列宽补空格:

```js
e.prototype.updateWidth = function(e) {
  var t = this, n = t.text, i = t.table, r = t.col, o = e - n.length,
      a = i.alignments[r], s = 1, l = 1;
  "right" === a ? s = o - 1
    : "center" === a ? (s = Math.floor(o / 2), l = Math.ceil(o / 2))
    : l = o - 1;
  this.padStart = s, this.padEnd = l
};
e.prototype.getTextWithPadding = function() {
  return " ".repeat(this.padStart) + this.text + " ".repeat(this.padEnd)
};
```

注意 `right` 时左侧补 `o - 1` 空格(右侧留 1 个, 否则 `|` 会贴住文字);
`center` 时左右平分, **落单的空格给右侧**(`Math.ceil` 给 `padEnd`)。

列宽不一致会被标记出来(供后续统一对齐):

```js
if (!g) {
  var x = 0;
  e: for (b = l.length; x < b; x++)
    for (var T = l[x], D = 0, A = r; D < A.length; D++) {
      var P;
      if ((P = (E = A[D])[x]).end - P.start !== T) { g = !0; break e }   // g = isMalformed
    }
}
```

即: 逐列比较每个单元格的字符长度是否都等于该列的期望宽度 `T`, 任一处不等就 `isMalformed = true`。
畸形表格仍会渲染, 只是走不同分支(见 `isMalformed` 的选区处理逻辑)。

---

## 8. 其他细节问答

### 单元格里的 `|` 怎么办? —— 转义成 `\|`
反向转换(HTML → Markdown, 用的 turndown)的规则写得很明白:

```js
cP.addRule("tableCell", {
  filter: ["th", "td"],
  replacement: function(e, t) {
    return (0 === Array.prototype.indexOf.call(t.parentNode.childNodes, t) ? "|" : "") +
      function(e) {
        return e = e.trim().replace(/\|+/g, "\\|").replace(/\n\r?/g, "<br>"), e + "|"
      }(e) + mP(t, "   |")
  }
});
var pP = {left: ":--", right: "--:", center: ":-:"};
```

即 **`|` → `\|`**、**换行 → `<br>`**。`pP` 还确认了 Obsidian 认可的对齐写法是
`:--` / `--:` / `:-:`(两短横就够了, 不要求三个)。

### 单元格内换行?
同上, 转成 `<br>`(HTML 标签)。而渲染侧靠 `white-space: break-spaces` 保留空白。

### 表格里的块级语法?
不会当作块级解析 —— 单元格的子编辑器用的是**关掉全部块级特性**的那个 hypermd 变体(§3),
所以单元格里的 `- ` 不会变成列表。这也是它必须维护两份语言变体的原因。

### 空单元格?
塞一个 `<br>` 占位: `[createEl("br")]`, 保证单元格有内容、行高不塌。

---

## 9. 复原的 DOM 结构

阅读模式(强推断, 类名有实证、层级为推断):

```html
<div class="markdown-rendered">
  <div class="el-table">
    <table>
      <thead><tr><th align="center">…</th></tr></thead>
      <tbody><tr><td align="center">…</td></tr></tbody>
    </table>
  </div>
</div>
```

Live Preview(类名与创建顺序均有实证):

```html
<div class="cm-embed-block cm-table-widget markdown-rendered">
  <div class="table-wrapper">
    <table>
      <thead><tr><th align="center">…</th></tr></thead>
      <tbody><tr><td align="center">…</td></tr></tbody>
    </table>
    <div class="table-row-btn"><svg class="lucide-…"/></div>
    <div class="table-col-btn"><svg class="lucide-…"/></div>
  </div>
</div>
```
(每个 `th`/`td` 内部还嵌着一套 CM6 DOM: `.cm-editor > .cm-scroller > .cm-content > .cm-line`)

---

## 10. 如果要自己复刻, 最小可靠路径

1. **解析**: 用支持 GFM 的解析器(`markdown-it` 开 `table` 规则, 或 `micromark` + `mdast-util-from-markdown`)。
   自己手写表格解析很容易在 `\|`、行内代码里的 `|`、单元格内联格式上翻车 —— Obsidian 也是老实写了个 tokenizer。
2. **对齐**: 走 **HTML `align` 属性**, 不要写 inline style。CSS 用 `[align="center"]` 接住,
   并且**用 `start`/`end` 而不是 `left`/`right`**(RTL 友好, 成本为零)。
3. **结构**: 首行 `<th>` 进 `<thead>`, 其余进 `<tbody>`; 没有数据行时只有 `<thead>` 也是合法的。
4. **宽表格**: 给容器 `overflow-x: auto` + `width: fit-content`(或 `max-width: 100%`)。
   只给 `<table>` 设 `overflow` 是无效的 —— 表格不是块容器。
5. **单元格换行与空白**: `white-space: break-spaces`(或 `pre-wrap`) + `word-break: normal`;
   超长截断配 `text-overflow: ellipsis` + `overflow: hidden`, 并给 `min-width` 兜底(如 `6ch`)。
6. **行等高**: `tr { height: 1px }` + `th,td { height: inherit }`。
7. **转义**: 写回 Markdown 时把 `|` 转 `\|`、换行转 `<br>`, 否则你的表格会被自己写坏。
8. **别做嵌套编辑器**, 除非你确实要 Obsidian 那种体验 —— 那是本项目里最重的一块
   (每个单元格一个 CM6 实例 + 子组件回收 + 选区只读控制 + 为单元格专门裁剪的语言变体)。

---

## 11. 存疑与未验证项

- **阅读模式块是否真的是 `div.el-table`**: `.el-table` 出现在 CSS 规则
  `.markdown-rendered div:is(.el-blockquote,.el-p,.el-pre,.el-table,.el-ul,.el-ol) + div > :is(h1..h6)`
  里, 但 **`el-table` 在 `app.js` 中字面量命中为 0** —— 试过用 `"el-"` 搜拼接, 45 处命中
  **全部是 Lucide 图标名的误匹配**(`funnel-x`、`gallery-horizontal`、`layout-grid` 等内含 `el-`)。
  所以它要么是运行时按节点类型拼出来的(`"el-" + type`), 要么是历史遗留类名。
  **层级结构未证实, 报告 §9 中的阅读模式 DOM 属推断。**
- **`FA(g, y, Y, Q)`(widget 复用判定)的逻辑未定位**: `FA=function` 字面量命中为 0,
  故不清楚在什么条件下会跳过复用、强制重建表格 widget。
- **`mq` 类(单元格对象)的 `init(S, -1, -1)`**: 后两个参数含义未确认(推测是行列索引哨兵值)。
- `--table-white-space: break-spaces` 是默认值, 主题可覆盖; 不同主题下表格观感差异很大。
- Obsidian 版本 **1.13.7**(本报告取证时为 1.12.4, 两版已逐项比对, 见 §13.8)。
  表格实现历史上变动较大(1.5 前后可视化编辑差别明显), 本文结论**只对这两个版本负责**。

---

## 12. 取证方法(可复用)

因 `app.js` 是 **单行 3.7 MB** 的 minified 产物, 常规 grep 只会吐出整行(等于没吐)。做法:

1. 解析 `obsidian.asar`。Electron asar 布局:
   ```
   offset 0   uint32  pickle 载荷大小(恒为 4)
   offset 4   uint32  header 区总字节数 H
   offset 8   uint32  header pickle 载荷大小
   offset 12  uint32  JSON 字符串长度 L
   offset 16  ...     JSON 头(文件树)
   offset 8+H ...     文件内容, 按 JSON 中每个条目的 offset 定位
   ```
   脚本: `obsidian-asar.py`(list / extract / grep; 已随临时目录移除)。
2. **按字符偏移取窗口**, 不按行: `obsidian-ctx.py <file> <pattern> --before N --after N`(同上)。
3. 关键认知: **minifier 改不动属性名与字符串**。所以 `cm-table-widget`、`alignments`、
   `cellChildMap`、`updateCellReadonly` 这些**字段名/类名/方法名全部可信**;
   而 `EditorView` / `WidgetType` 这类**导入的类名会被重命名**(`Uo` / `Rn`),
   **按字面统计会严重低估**。判定库版本要看**导出表**和 **DOM 类名字符串**(`cm-editor`、`cm-content`)。
4. `app.css` 有 20644 行, 未 minified, 可正常 grep/read —— 它是拿类名与设计意图**最快**的入口。
5. 注意 **`app.js` 是单行**: 对单行大文件不要用 `grep`/`Select-String`(只会吐出整行),
   必须按**字符偏移**取窗口。`app.css` 反而有 2 万多行, 常规工具完全够用。

### 12.1 配套脚本源码(完整, 自包含)

`scripts\` 是临时目录、已于 2026-10-11 移除, 所以源码以内嵌于本文件为准。

**① asar 解析器** —— 列清单 / 提取单个文件 / 检索

```python
#!/usr/bin/env python3
"""Electron asar 归档解析: 列清单 / 提取单个文件 / 关键字检索。

asar 布局:
    offset 0  uint32  pickle 载荷大小(恒为 4)
    offset 4  uint32  header 区总字节数 H
    offset 8  uint32  header pickle 载荷大小
    offset 12 uint32  JSON 字符串长度 L
    offset 16 ...     JSON 头(描述整棵文件树)
    offset 8+H ...    各文件内容, 按 JSON 中的 offset 定位

用法:
    python obsidian-asar.py list [--sort size] [--limit N] [--depth D]
    python obsidian-asar.py extract <内部路径> <本地输出路径>
    python obsidian-asar.py grep <正则> [--ext .css,.js] [--ctx 2] [--limit N]
"""
import argparse
import json
import os
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_ARCHIVE = r"C:\Program Files\Obsidian\resources\obsidian.asar"


def load_index(path):
    """返回 (header_json, data_start)。"""
    with open(path, "rb") as fh:
        head = fh.read(8)
        header_area = struct.unpack("<I", head[4:8])[0]
        hb = fh.read(header_area)
        str_len = struct.unpack("<I", hb[4:8])[0]
        header = json.loads(hb[8:8 + str_len].decode("utf-8"))
    return header, 8 + header_area


def walk(node, prefix, out):
    for name, info in node.get("files", {}).items():
        full = f"{prefix}/{name}" if prefix else name
        if "files" in info:
            walk(info, full, out)
        else:
            out.append((full, int(info.get("size", 0)), int(info.get("offset", 0))))
    return out


def read_entry(path, data_start, entry):
    with open(path, "rb") as fh:
        fh.seek(data_start + entry[2])
        return fh.read(entry[1])


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def cmd_list(archive, args):
    header, _ = load_index(archive)
    files = walk(header, "", [])
    print(f"归档 {archive}")
    print(f"文件总数 = {len(files)}  合计 = {human(sum(f[1] for f in files))}\n")

    if args.depth is not None:
        files = [f for f in files if f[0].count("/") < args.depth]

    files.sort(key=(lambda f: -f[1]) if args.sort == "size" else (lambda f: f[0]))
    for path, size, _ in files[: args.limit]:
        print(f"  {human(size):>10}  {path}")
    if len(files) > args.limit:
        print(f"  ... 另有 {len(files) - args.limit} 项")


def cmd_extract(archive, args):
    header, data_start = load_index(archive)
    files = {f[0]: f for f in walk(header, "", [])}
    key = args.path.strip("/")
    entry = files.get(key)
    if entry is None:
        near = [f for f in files if key.lower() in f.lower()][:10]
        sys.exit(f"未找到 {key}" + (f"; 相似: {near}" if near else ""))
    data = read_entry(archive, data_start, entry)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "wb") as fh:
        fh.write(data)
    print(f"已提取 {key} -> {args.out}  ({human(len(data))})")


def cmd_grep(archive, args):
    header, data_start = load_index(archive)
    files = walk(header, "", [])
    exts = tuple(e.strip() for e in args.ext.split(",")) if args.ext else None
    pat = re.compile(args.pattern, re.I)
    total = 0
    for path, size, _ in sorted(files):
        if exts and not path.lower().endswith(exts):
            continue
        if size > args.max_file_mb * 1024 * 1024:
            continue
        raw = read_entry(archive, data_start, (path, size, _))
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if not pat.search(line):
                continue
            total += 1
            print(f"\n### {path}:{i + 1}")
            for j in range(max(0, i - args.ctx), min(len(lines), i + args.ctx + 1)):
                print(f"  {'>' if j == i else ' '} {lines[j][:400]}")
            if total >= args.limit:
                print(f"\n[已达上限 {args.limit} 条]")
                return
    print(f"\n[共 {total} 条命中]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default=DEFAULT_ARCHIVE)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list")
    p.add_argument("--sort", choices=["name", "size"], default="name")
    p.add_argument("--limit", type=int, default=60)
    p.add_argument("--depth", type=int, default=None)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("extract")
    p.add_argument("path")
    p.add_argument("out")
    p.set_defaults(func=cmd_extract)

    p = sub.add_parser("grep")
    p.add_argument("pattern")
    p.add_argument("--ext", default=None)
    p.add_argument("--ctx", type=int, default=2)
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--max-file-mb", type=float, default=60)
    p.set_defaults(func=cmd_grep)

    args = ap.parse_args()
    if not os.path.isfile(args.archive):
        sys.exit(f"归档不存在: {args.archive}")
    args.func(args.archive, args)


if __name__ == "__main__":
    main()
```

**② 字符窗口提取器** —— 专门对付 minified 单行大文件

```python
#!/usr/bin/env python3
"""从 minified(常为单行)文件中按字符位置提取关键字上下文窗口。

普通 grep 对单行 3.7MB 的文件只能吐出整行(等于没吐), 所以这里放弃行概念,
直接按字符偏移取窗口。

用法:
    python obsidian-ctx.py <file> <pattern> [--before N] [--after N] [--max N] [--regex]
"""
import argparse
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("pattern")
    ap.add_argument("--before", type=int, default=250)
    ap.add_argument("--after", type=int, default=450)
    ap.add_argument("--max", type=int, default=8)
    ap.add_argument("--regex", action="store_true")
    args = ap.parse_args()

    with open(args.file, encoding="utf-8", errors="replace") as fh:
        text = fh.read()

    pat = re.compile(args.pattern if args.regex else re.escape(args.pattern))
    hits = list(pat.finditer(text))
    show = min(len(hits), args.max)
    print(f"文件 {args.file}")
    print(f"长度 {len(text)} 字符 / 命中 {len(hits)} 处 / 显示前 {show} 处")
    print(f"窗口 = 前 {args.before} + 后 {args.after} 字符\n")

    for i, m in enumerate(hits[:show]):
        lo, hi = max(0, m.start() - args.before), min(len(text), m.end() + args.after)
        snippet = text[lo:hi].replace("\n", "\\n").replace("\r", "")
        print(f"===== [{i + 1}/{len(hits)}] offset {m.start()} =====")
        print(snippet)
        print()


if __name__ == "__main__":
    main()
```

**③ 关键搜索词速查**(按信息密度排序, 括号内是实测命中/含义)

| 搜索词 | 用途 |
|---|---|
| `.cm-table-widget` | 表格 widget 创建点(唯一 1 处, 最直接) |
| `cm-embed-block` | 所有 Live Preview 嵌入块 |
| `table-wrapper` | 表格滚动容器与行/列按钮 |
| `alignments` | 列对齐数组, 反向找到渲染逻辑 |
| `isMalformed` | 畸形表格分支 |
| `cellChildMap` | 单元格嵌套编辑器管理 |
| `HyperMD-table-row` | 表格行的识别依据(widget 替换的触发源) |
| `getMode(` + `hypermd` | CM5 mode 被 StreamLanguage 包装之处 |
| `Decoration` 的导出别名(`Vn`) | 找 `.replace({widget, block:true})` 必须用它, 搜 `Decoration` 搜不到 |

---

## 13. 第二路独立取证: 交叉验证、版本差异与生态对照

> 本节的原始取证数据(字符 offset、webpack 模块号、逐字节检索记录、生态调研与论坛线索)保存在同目录
> **`Obsidian表格渲染实现调研-1.13.7取证附录.md`**。该文件顶部已加勘误声明 —— 它关于
> "光标进入表格会退回源码"的原始结论**已被 §13.1 证伪**, 结论请以本报告为准。

本报告主体基于**本机实际运行**的 Obsidian **1.13.7**(`C:\Program Files\Obsidian\resources\obsidian.asar`,
2026-09-18 由 1.12.4 升级而来; 两版结论已在 §13.8 逐项对齐)。
另有一路独立取证基于本机 `%APPDATA%\obsidian\obsidian-1.13.7.asar` —— 撰写时它被记为
**"已下载但尚未安装"的更新包**(24.59 MB, 2026-08-12)。**该判断现已修正**: `obsidian.log` 明确记录
`Loaded updated app C:\Users\zghyu\AppData\Roaming\obsidian\obsidian-1.13.7.asar` —— Obsidian 的
自动更新流程是「下载 asar 到 userData → 下次启动直接加载它」, 故它**不是可删的缓存**,
而是被实际加载的那个 asar。两路结论在**机制层面高度一致**
(widget 替换、`cellChildMap`、`colWidths`、单元格嵌套编辑器、`table-wrapper` 全 bundle 仅 1 处、
`markdown-rendered` 复用样式等均相互印证), 差异集中在版本演进与个别细节。

### 13.1 一处被证伪的结论(记录下来避免重蹈)

第二路取证曾判定"**光标进入表格会退回源码**", 依据是 ViewPlugin 里存在
`b = OA(选区相交) || FA(搜索命中)` 这一判断。**该结论是错的** —— `b()` 是通用判断, 服务于
**公式/代码块**等元素; 表格分支 `J` 走的却是 `if (!FA(...))`, **不含任何选区判断**。
两个调用点的逐字对照见 §5.6。

**教训: 变量名复用会骗人。** `J` 内部 `var b = Y > 0 && ...` 局部**遮蔽**了外层的 `b` 函数,
顺着"看到 `b` 就以为走了选区逻辑"的直觉读下去, 会得出完全相反的行为结论。
**判定行为必须定位到该元素真正的调用点, 而不是只找到判断函数本身。**

### 13.2 补充: 阅读模式的消毒环节(DOMPurify)

本报告 §4 原本只追到 hast→DOM。第二路取证补上了最后一跳 —— 渲染结果**经过 DOMPurify**:

```js
DOMPurify.sanitize(html, { RETURN_DOM_FRAGMENT: true, FORBID_TAGS: ["style"] })
```

完整链路因此是:
`md → mdast → hast → HTML 字符串 → DOMPurify → DocumentFragment → importNode 注入`。

`FORBID_TAGS: ["style"]` 意味着**内联 `<style>` 会被剥掉** —— 这解释了为什么表格样式只能靠
CSS 变量与外部样式表, 而无法写在 Markdown 文档里。

### 13.3 补充: 阅读模式侧宽表滚动的真实机制

§6.3 给的是 Live Preview 侧的 `.cm-table-widget { overflow-x: auto }`。
**阅读模式侧机制不同**: 一个内置 post-processor 在"**表格是父节点的唯一子元素**"这一条件下,
给**父元素**(而不是 `<table>` 本身)设 `style.overflowX = "auto"` 并补齐 `dir` 属性。
两侧合起来才是完整的结论 —— **没有任何一侧是给 `<table>` 自己设 overflow 的**。

### 13.4 补充: 完整的类名清单

`table.addClass("table-editor")` —— LP 里那个 `<table>` 实际带 `table-editor` 类。完整清单:

`markdown-rendered` / `cm-table-widget` / `table-wrapper` / `table-editor` / `table-cell-wrapper` /
`table-row-btn` / `table-col-btn` / `table-row-drag-handle` / `table-col-drag-handle`

⚠️ **`markdown-table-*` 这类前缀并不存在**(两个版本的 `app.js`/`app.css` 中均 0 命中),
不要把第三方插件的类名混进来。

### 13.5 补充: 官方 CSS 变量

Obsidian 官方文档登记了 **36 个**表格 CSS 变量
([CSS variables · Table](https://docs.obsidian.md/Reference/CSS+variables/Editor/Table))。
除 §6.1 已列出的之外, 还有若干**官方文档未收录**的内部变量:
`--table-drag-handle-size`、`--table-selection-blend-mode`、
`--table-row-last-border-width`、`--table-column-first-border-width`、`--table-column-last-border-width`。

### 13.6 生态对照: 别人是怎么做表格的

| 方案 | 定位 | 与 Obsidian 的关系 |
|---|---|---|
| `@lezer/markdown` 的 GFM 扩展 | 只做**解析与高亮**(`Table`/`TableHeader`/`TableRow`/`TableCell`/`TableDelimiter`) | CM6 官方语法层; 含 `esc = !esc && next == 92` 的 `\|` 转义与 `delimiterLine` 正则 |
| `@codemirror/lang-markdown` | `commonmarkLanguage` **不含表格**; `markdownLanguage` 含 GFM+Table | **CM6 官方没有表格渲染扩展**, 要做得自写 `WidgetType` + block replace |
| HyperMD | CM5 时代的 markdown 编辑器 | 与 Obsidian 的 CM5 token 体系**同源**(`HyperMD-table-row` 思路一致) |
| Advanced Tables(第三方插件) | **只重排源码**, 不做所见即所得 | 与 Obsidian 内核路径完全不同 |
| `ckant/codemirror-markdown-tables`、`@markwhen/codemirror-tables` | CM6 第三方表格扩展 | 自研 CM6 表格渲染时的参考实现 |
| `obsidian-typings` | 社区类型定义 | 其中 `lineClassNodeProp` 被标注为 **"only in Obsidian"**, 佐证 Obsidian 对 `@codemirror/language` 打过补丁 |

### 13.7 复刻坑清单(补充 §10)

1. `\|` 转义必须处理, 且**行内代码里的 `|` 同样要转义**(不能因为它在 code span 中就放过)。
2. 表格**各行的"首管道"必须一致**(要么都有前导 `|`, 要么都没有), 否则不构成表格。
3. 解析层**不校验列数一致**(宽松); 但 Live Preview 会检测列宽不一致(`isMalformed`)并走不同分支。
4. 空单元格、**空表头**都要能渲染(空表头在某些主题下会显示成普通空行, 属样式问题)。
5. **中文按码元算宽度会让源码态对齐错位** —— `colWidths` 用的是 `text.length`, 中文一个字算 1,
   而实际显示宽度是 2。此条为**推断, 未实测**(§7 的 `updateWidth` 逻辑支持该推断)。
6. 宽表包装: LP 给 widget 设 overflow, RV 给**父元素**设 overflowX —— 不要给 `<table>` 本身设。
7. 表格**前后需要空行**; 遇到不含 `|` 的行即终止。
8. 消毒白名单会剥掉内联 `style`, 样式只能走 CSS 变量。
9. 往返转换要能还原 `\|`、`<br>`、`:--`/`--:`/`:-:`, 否则反复编辑会逐步破坏源码。
10. 列表内嵌表格等边界场景**未验证**。

### 13.8 版本一致性验证(1.13.7 vs 1.12.4)

取证完成后本机 Obsidian 由 **1.12.4 升级到 1.13.7**(`Program Files` 下的 `obsidian.asar`
由 22.9 MB / 352 文件变为 24.59 MB / 358 文件, 4 个进程于同一时刻重启)。
为确认结论未随版本失效, 对新版 `app.js`(3,871,660 字符; 旧版 3,722,960)做了全面重验。

**(1) 关键标识命中数 —— 逐一相等**

| 关键词 | 1.12.4 | 1.13.7 | 判定 |
|---|---|---|---|
| `HyperMD-table-row` | 3 | 3 | ✓ 行类名机制不变 |
| `hypermd` | 6 | 6 | ✓ CM5 mode 仍在 |
| `StreamLanguage` | 1 | 1 | ✓ 仍经 StreamLanguage 包装 |
| `cm-table-widget` | 1 | 1 | ✓ widget 唯一 |
| `cellChildMap` | 4 | 4 | ✓ 单元格编辑器管理不变 |
| `tokenizeInline` | 17 | 17 | ✓ remark-parse v8 架构不变 |
| `cm-embed-block` | 5 | 5 | ✓ |

**(2) 双 hypermd 变体逐字对应**(1.13.7, offset 2517743)

```js
LJ = fp.define(CodeMirror.getMode({}, {name: "hypermd"})),
OJ = fp.define(CodeMirror.getMode({}, {name: "hypermd", front_matter:!1, table:!1,
      fencedCodeBlockHighlighting:!1, taskLists:!1, headers:!1, blockquotes:!1,
      indentedCode:!1, lists:!1, hr:!1, blockId:!1})),
```

与 §3 的 1.12.4 原文(`X$` / `$$` + `Hd.define`)结构完全一致, 仅 StreamLanguage 的
别名由 `Hd` 变为 `fp`。**第二份"关掉全部块级特性"的变体依然存在** —— 它是嵌套单元格编辑器的前提。

**(3) 表格 widget 替换分支逐字对应**(1.13.7, offset 2989930)

```js
J = function(t) {
  if (-1 !== Y && X < t) {
    ... 尝试 receiveUpdate / receiveIncompleteUpdate 复用旧 widget ...
    if (!OL(g, y, Y, X)) {                       // ← 即 1.12.4 的 !FA(...), 仍只检查搜索命中
      c || (c = new nj(n, e, o, s));
      var b = Y > 0 && Y > fO(h.newDoc) + 1;     // ← 局部 b 再次遮蔽外层 b 函数
      C.push(w({widget: c, side: 1, block: !0, inclusiveStart: b}, Y, X)),
             rd.isAndroidApp && X !== v.length && C.push(B3.range(X + 1))
    }
    c && (c.setPos(Y, X), c.receiveSelection(h), a.push(c)), Y = -1, X = -1
  }
};
```

**§5.6 的判据在新版完全成立**: 表格分支只做一次判断(搜索命中), **不含选区相交检查**;
同一作用域内的 `Z`(公式/代码块)仍写作 `b(K,G) || (...)`。
即"**选中表格不退回源码、公式会退回源码**"这一差异在两个版本上一致。

**(4) 两版偏移对照**(仅供定位; 内容一致)

| 目标 | 1.12.4 | 1.13.7 |
|---|---|---|
| `cm-table-widget` 容器构造 | 1,897,527 | 2,019,235 |
| `Table`/`TableRow` 类名生成与 `hmdTable` 字段 | — | 2,117,721 |
| `window.CodeMirror.defineMode("hypermd", …)` | — | 2,104,127 |
| `defineMIME("text/x-hypermd", "hypermd")` | — | 2,119,070 |
| 双变体 `StreamLanguage.define(...)` | 2,391,709 | 2,517,743 |
| 表格 ViewPlugin `J`(`inclusiveStart`) | 2,840,984 | 2,989,930 |
| `OA` / `IA` / `FA` 选区判断函数 | 1,518,541 | (同名, 偏移随构建变化) |

文件规模: `app.js` 3,722,960 → **3,871,660** 字符; `app.css` 20,643 → **21,708** 行。
`app-1.13.7.css` 中 `--table-column-min-width: 6ch`(L2776)、`/* Tables */` 段落(L13725)
等表格样式条目依然存在, 仅行号平移。

> **结论: 1.13.7 未改动表格渲染架构, 本报告全部结论对它同样成立。**
> 若日后需要复核, 请以**当前版本**的 asar 重新提取 —— 所有字符偏移都会随构建变化,
> 但**属性名、类名、字符串常量永远不变**, 它们才是可靠的搜索锚点(见 §12)。

