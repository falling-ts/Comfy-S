# pipeline — 工作流档案、依赖 DAG 与执行模板

> 本文件是 `auto` 技能的参考附件。所有档案均**实测自本机** `workflows/` 与
> `stories/七纹刻印/` 的实际内容(2026-10-15 复核), 不是推测。

## 1. 工作流档案(35 个)

「数据表」列 = 该工作流内 `FallingTSMarkDownTable` 节点的 `md_path` 指向;
「产物目录」= 保存类节点的实际落盘目录(`media/七纹刻印/<目录>/`)。

| 工作流 | 数据表 | 产物目录 | 说明 |
|---|---|---|---|
| `0010_灰度遮罩` | **无** | `0010_灰度遮罩/` | 加载图像 → 遮罩编辑器 → 存 `<5位编号>_<名称>.png` |
| `0011_万物建模` | `0011_万物建模.md` | `0011_万物建模/` | 人物/器物版式图(人物: 左脸部特写 + 右上三视图 + 右下手部特写); **身份唯一上游**; 产物尺寸 = md 宽高(**×1 直通**) |
| `00110_万物建模_QI2.1` | `0011_万物建模.md` | `0011_万物建模/` | 同上, Qwen-Image 2.1 版; **与 0011 共用表、同目录、同 ID 互相覆盖** |
| `0012_万物变化` | `0012_万物变化.md` | `0012_万物变化/` | 单图/多图编辑 + 灰度遮罩局部重绘 |
| `00120_万物变化_QI2.1` | `0012_万物变化.md` | `0012_万物变化/` | 同上 2.1 版, 共用表 |
| `0013_首图建模` | `0013_首图建模.md` | `0013_首图建模/` | I2VA 人物锁身份(原地逆时针 45°×8) |
| `0014_参考建模` | `0014_参考建模.md` | `0014_参考建模/` | REF2VA 六段, 一般只填 `<Picture 1>` |
| `0015_建模截帧` | **无**(自带加载节点) | `0015_建模截帧/` | 视频 → 8 单帧 + 四图/八图 |
| `0016_建模拆图` | **无**(两个加载节点) | `0016_建模拆图/` | 2×2 / 3×3 拆格; 用 **RunGroup** 跑单流 |
| `0017_建模细节` | `0017_建模细节.md` | `0017_建模细节/` | 拆块局部精修(Qwen-Image-Edit) |
| `0020_场景首帧` | `0020_场景首帧.md` | `0020_场景首帧/` | 场景九宫格生成; **场景唯一上游** |
| `00200_场景首帧_QI2.1` | `0020_场景首帧.md` | `0020_场景首帧/` | 同上 2.1 版, 共用表 |
| `0021_场景拉镜` | `0021_场景拉镜.md` | `0021_场景拉镜/` | 扩图 + 优化两段 |
| `0022_场景推镜` | `0022_场景推镜.md` | `0022_场景推镜/` | 框选放大 → 编辑精修 |
| `00220_场景推镜_QI2.1` | `0022_场景推镜.md` | `0022_场景推镜/` | 同上 2.1 版, 共用表 |
| `0023_场景旋镜` | `0023_场景旋镜.md` | `0023_场景旋镜/` | 八方位**视角图** + 全图 |
| `0030_文生场景` | `0030_文生场景.md` | `0030_文生场景/` | H3 T2VA, 仅画面 |
| `0031_首帧场景` | `0031_首帧场景.md` | `0031_首帧场景/` | H3 I2VA 旋镜视频; **0035/0034 的上游** |
| `0032_参考场景` | `0032_参考场景.md` | `0032_参考场景/` | REF2VA 场景(多图/多视频参考) |
| `0034_世界模型` | `0034_世界模型.md` | `0034_世界模型/` | 360° 视频 → 3DGS PLY; **复用 0031 视频** |
| `0035_场景截帧` | **无**(自带加载节点) | `0035_场景截帧/` | **源视频 = `0031_首帧场景/<ID>.mp4`** |
| `0040_文生视频` | `0040_文生视频.md` | `0040_文生视频/` | T2VA 三字段, 无对齐指令 |
| `0041_首帧视频` | `0041_首帧视频.md` | `0041_首帧视频/` | I2VA |
| `0042_首尾视频` | `0042_首尾视频.md` | `0042_首尾视频/` | FL2VA |
| `0043_关键帧视频` | `0043_关键帧视频.md` | `0043_关键帧视频/` | 最多 9 图 + 秒数列 |
| `0044_参考视频` | `0044_参考视频.md` | `0044_参考视频/` | REF2VA 全参考; **全链汇聚点** |
| `0050_视频截帧` | **无** | `0050_视频截帧/` | 加载视频 → 三个 `AutoSaveImage` |
| `0051_视频拆音` | **无** | `0051_视频拆音/` | 加载视频 `audio` → 波形截段 |
| `0060_背景音乐` | `0060_背景音乐.md` | `0060_背景音乐/` | 整片配乐 |
| `0061_环境音效` | `0061_环境音效.md` | `0061_环境音效/` | 环境氛围声 |
| `0062_效果音效` | `0062_效果音效.md` | `0062_效果音效/` | 效果声 |
| `0063_文生人声` | `0063_文生人声.md` | `0063_文生人声/` | 内容 + 情绪 |
| `0064_参考人声` | `0064_参考人声.md` | `0064_参考人声/` | 原人声 + 内容 + 情绪 |
| `0070_截取声音` | **无** | `0070_截取声音/` | 加载音频 → 波形截段 |

### 关键实测值(2026-10-15)

- `0044_参考视频`: 42 节点; UNET `minimax_h3_ref2va_pruned_int8_convrot`,
  CLIP `qwen3vl_32b_minimax_h3_int8_convrot`, 两个 LoRA
  (`ref2v_turbo_4step_v0.1` / `ref2v_turbo_8step_v1.0_768p`), 两个 `MiniMaxH3SigmaShift` **均为 `[12, 3]`**。
- `0031_首帧场景`: 34 节点; UNET `minimax_h3_fl2va_pruned_int8_convrot`, shift **`[12, 3]`**。
- `0030_文生场景` / `0040_文生视频`: shift **`[6, 3]`**(LoRA 姓 `fl2v_turbo_*_768p`)。
- 含 `FallingTSContinue` 闸门的工作流: `0011`、`00110`、`0020`、`00200`、`0021`、`0063`。
- 含 `FallingTSRunGroup` 的: 只有 `0016`(2 个)。

## 2. 依赖 DAG(实测)

```
                    ┌──────────────────────────────┐
  正文/大纲 ───────→│ 0011 万物建模 (人物/器物)     │──→ 0013 首图建模 ──→ 0015 建模截帧 ─┐
                    │ 0020 场景首帧 (场景)          │                        ↑          │
                    └──────────────────────────────┘                        └─ 0014 参考建模
                              │                     │
                              │                     └──→ 0021 拉镜 / 0022 推镜 / 0023 旋镜
                              ↓
                        0020 ──→ 0031 首帧场景 ──┬──→ 0035 场景截帧 ──→ 0032 / 0044
                                                └──→ 0034 世界模型 (复用同一视频)

  0011 / 0020 / 0023 / 0035 产物 ──→ 0040 / 0041 / 0042 / 0043 / 0044 视频
  0011 ──→ 0016 建模拆图 ──→ 0017 建模细节
  0060~0062 独立;  0063 → 0064
```

**硬结论**:

1. **0011 是人物身份唯一上游** —— 脸必须来自它的高分辨率独立生成, **绝不从全身小图裁脸**。
2. **0035 的输入是 0031 的产物**(不是 0023): 必须先跑 `0031_首帧场景`。
3. **0034 复用 0031 的同一段旋镜视频**, 不另拍; 且只对封闭场景(房间/院子/车厢)做。
4. **0044 是汇聚点**, 引用 0011/0012/0020/0023/0035 的既有产物。
5. Qwen-Image 2.1 版与 1.x 版**共用表** ⇒ **落同一目录, 同 ID 产物互相覆盖, 只留一份**。

## 3. 实测引用分布(`@{...}`)

`stories/七纹刻印/*.md` 内共 **69 条**引用、**去重后 20 条**:

| 被引表 | 去重条数 |
|---|---|
| `0035_场景截帧` | 10 |
| `0020_场景首帧` | 2 |
| `0011_万物建模` | 2 |
| `0010_灰度遮罩` | 2 |
| `0050_视频截帧` | 1 |
| `0031_首帧场景` | 1 |
| `0016_建模拆图` | 1 |
| `0012_万物变化` | 1 |

### 实测解析结果(2026-10-15, 经运行中的 8188 `/fallingts_mdtable/resolve`)

**20 条里 18 条严格命中 / 1 条兜底命中(共 19 命中) / 1 条真失败**:

- ✗ `@{0010_灰度遮罩/00001_陈落换装}`(出现在 `0012_万物变化.md`) ——
  `media/七纹刻印/0010_灰度遮罩/` 下只有 `00001_参考视频第一条_手机.png`, 该名称不存在。

⚠️ **唯一一条"看似写错、其实能命中"的引用** —— 它靠**兜底趟**才成功, 属于**隐患**:

| 引用(写在) | 严格趟结果 | 实际命中 |
|---|---|---|
| `@{0011_万物建模/00001_陈落_左上}`(`0044`) | `0011_万物建模/` 下只有 `00001_陈落.png`, **严格趟落空** | 兜底趟全区搜到 `0016_建模拆图/00001_陈落_左上.png` |

⇒ 上表**语义写错了目录**(`_左上` 是 `0016` 的产物, 不是 `0011` 的),
但解析器兜底趟救了它。**兜底趟会掩盖目录名错误**, 一旦 `0016` 改名或该文件被清理,
这条引用就会**静默变 `None`**。写引用时一律以**产物真实所在目录**为准。

> ⚠️ **端点只吃 `GET`。** 实测 `POST /fallingts_mdtable/resolve` 恒返回 **`405 Method Not Allowed`**;
> 若脚本用 `urllib` 发 POST 且异常处理不当, 会把 405 误读成"成功", 报出**全绿的假结果**。
> 校验时必须**显式判断 `ok` 字段**, 并把「请求异常」与「ok=false」分开计数。

> 复核口径: `grep -oh '@{[^}]*}' stories/<库>/*.md | sort -u`, 再逐条打
> `GET /fallingts_mdtable/resolve?path=@{<表名>/<ID>}`(**必须带 `@{}` 包起来**, 传裸路径一律失败)。
> 历史数据表**没有 mdtable 刷新就不会重跑**, 死引用可能长期潜伏 —— 每次作业前跑 §7.2。

## 4. 各表表头(实测, 写入时必须逐字照抄)

```
0011_万物建模   | ID | 主-正词(TEXT) | 主-负词(TEXT) | 宽度(INT) | 高度(INT) |
0012_万物变化   | ID | 原图(IMAGE) | 灰度遮罩(MASK) | 图1(IMAGE) | 图2(IMAGE) | 图3(IMAGE) | 变化-正词(TEXT) | 变化-负词(TEXT) |
0013_首图建模   | ID | <Picture 1>(IMAGE) | 建模提示词(TEXT) | 宽度(INT) | 高度(INT) | 视频秒数(INT) |
0014_参考建模   | ID | 建模提示词(TEXT) | <Picture 1..9>(IMAGE) | <Video 1..3>(VIDEO) | <Audio 1..3>(AUDIO) | 宽度(INT) | 高度(INT) | 视频秒数(INT) |
0017_建模细节   | ID | 原图(IMAGE) | 主-正词(TEXT) | 主-负词(TEXT) |
0020_场景首帧   | ID | 主-正词(TEXT) | 主-负词(TEXT) | 宽度(INT) | 高度(INT) |
0021_场景拉镜   | ID | 原场景(IMAGE) | 扩展-正词(TEXT) | 扩展-负词(TEXT) | 图2(IMAGE) | 图3(IMAGE) | 优化-正词(TEXT) | 优化-负词(TEXT) |
0022_场景推镜   | ID | 原场景(IMAGE) | 主-正词(TEXT) | 主-负词(TEXT) |
0023_场景旋镜   | ID | 原视角(IMAGE) | 前右-正词(TEXT) | …(八方位各一正一负)… | 全图-正词(TEXT) | 全图-负词(TEXT) |
0030_文生场景   | ID | 场景提示词(TEXT) | 宽度(INT) | 高度(INT) | 视频秒数(INT) |
0031_首帧场景   | ID | <Picture 1>(IMAGE) | 场景提示词(TEXT) | 宽度(INT) | 高度(INT) | 视频秒数(INT) |
0032_参考场景   | ID | 场景提示词(TEXT) | <Picture 1..9>(IMAGE) | <Video 1..3>(VIDEO) | <Audio 1..3>(AUDIO) | 宽度 | 高度 | 视频秒数 |
0034_世界模型   | ID | 场景描述(TEXT) | 360环绕视频(VIDEO) |
0040_文生视频   | ID | 视频提示词(TEXT) | 宽度(INT) | 高度(INT) | 视频秒数(INT) |
0041_首帧视频   | ID | <Picture 1>(IMAGE) | 视频提示词(TEXT) | 宽度(INT) | 高度(INT) | 视频秒数(INT) |
0042_首尾视频   | ID | <Picture 1>(IMAGE) | <Picture 2>(IMAGE) | 视频提示词(TEXT) | 宽度 | 高度 | 视频秒数 |
0043_关键帧视频 | ID | 视频提示词(TEXT) | 锚点数(INT) | <Picture 1> 首帧(IMAGE) | <Picture 2>(IMAGE) | 关键帧2所在秒数(FLOAT) | … | <Picture 9> 尾帧(IMAGE) | 宽度 | 高度 | 视频秒数 |   (共 22 列)
0044_参考视频   | ID | 视频提示词(TEXT) | <Picture 1..9>(IMAGE) | <Video 1..3>(VIDEO) | <Audio 1..3>(AUDIO) | 宽度 | 高度 | 视频秒数 |
0060_背景音乐   | ID | 音乐提示词(TEXT) | 秒数(INT) |
0061_环境音效   | ID | 音效提示词(TEXT) | 秒数(INT) |
0062_效果音效   | ID | 音效提示词(TEXT) | 秒数(INT) |
0063_文生人声   | ID | 内容(TEXT) | 情绪(TEXT) |
0064_参考人声   | ID | 原人声(AUDIO) | 内容(TEXT) | 情绪(TEXT) |
```

**mdtable 位置式槽位**(决定列序不可改):
`0`=ID; `1..9`=`<Picture 1..9>`; `10..12`=`<Video 1..3>`; `13..15`=`<Audio 1..3>`;
`16`=提示词; `17`=宽; `18`=高; `19`=秒数。

## 5. 尺寸与分辨率统一(2026-10-15 实测)

### 5.1 分辨率参数怎么生效(三段链路, 缺一不可)

```
auto 的「分辨率」参数
  ├─① 写入 md 表「宽度」「高度」列 ──→ FallingTSMarkDownTable 的槽 17/18
  └─② 提交时把宽高 FallingTSSelector 的 selection 覆盖成「默认」
         ↓
   selector 选中「默认」档 = 采用 md 宽高列的值
         ↓
   喂给 EmptySD3LatentImage / EmptyMiniMaxH3LatentAV / MiniMaxH3ImageToVideo
```

⚠️ **只做 ① 不做 ② 会静默失效** —— 实测 `0013`/`0014`/`0030`/`0033`/`0040`/`0041`/`0042`/`0043`
这 8 个工作流的宽高 selector **当前停在「横480」档**, 该档直接取 `PrimitiveInt(832,480)`,
**完全不读 md 宽高列**。`0031`/`0032`/`0044` 的 selector 已是「默认」, 所以它们才与 md 一致。
`0011`/`0020` **没有 selector**, md 宽高**直连** latent, 天然生效。

### 5.2 含宽高列的 13 张表(实测)

只有这 13 张会被 S0 改写; 其余表**没有**宽高列, 不受分辨率参数影响。

| 表 | 宽槽 | 高槽 | 宽高去向 |
|---|---|---|---|
| `0011_万物建模` | 3 | 4 | 直连 `EmptySD3LatentImage` |
| `0013_首图建模` | 3 | 4 | `FallingTSSelector`(#134) |
| `0014_参考建模` | 17 | 18 | `FallingTSSelector`(#138) |
| `0020_场景首帧` | 3 | 4 | 直连 `EmptySD3LatentImage` |
| `0030_文生场景` | 2 | 3 | `FallingTSSelector`(#129) |
| `0031_首帧场景` | 3 | 4 | `FallingTSSelector`(#134) |
| `0032_参考场景` | 17 | 18 | `FallingTSSelector`(#138) |
| `0040_文生视频` | 2 | 3 | `FallingTSSelector`(#71) |
| `0041_首帧视频` | 3 | 4 | `FallingTSSelector`(#918) |
| `0042_首尾视频` | 4 | 5 | `FallingTSSelector`(#918) |
| `0043_关键帧视频` | 19 | 20 | `FallingTSSelector`(#916) |
| `0044_参考视频` | 17 | 18 | `FallingTSSelector`(#926) |

**无宽高列的表**: `0012` `0017` `0021` `0022` `0023` `0034` `0060` `0061` `0062` `0063` `0064`。

### 5.3 各档位代表尺寸

| 档位 | 尺寸 | 竖版 |
|---|---|---|
| H3 480p | `832×480` | `480×832` |
| H3 544p | `960×544` | `544×960` |
| H3 768p | `1344×768` | `768×1344` |

其余合法桶: `1536×672`(21:9)、`1152×768`(3:2)、`1024×768`(4:3)、`768×768`(1:1)、
`768×1024`(3:4)、`768×1152`(2:3)、`768×1344`(9:16)、`672×1536`(9:21)。
硬约束: **短边 ≤768、面积 ≤1 032 192、每轴 32 的倍数**。
H3 固定 **24fps**(表内不设帧率列), 秒数取 **5~15 秒**。

⚠️ **`0011_万物建模` 的编辑链放大倍数于 2026-10-17 由 ×3 改为 ×1**(`LatentUpscaleBy(bicubic, 1)`):
**产物尺寸 = md 宽高列的原始值**, 不再有 ×3 换算。
本库 `0011_万物建模.md` 固定档为 **1920×1088**, 故产物即 `1920×1088`。
实测旧口径(×3 时代): md `960×544` → `2880×1632`, **已废止, 不要再用**。
`00110_万物建模_QI2.1` 同样是 ×1。

⇒ **所有图片产物的分辨率 == md 宽高列的原始值**(0011 现在也遵循这条)。

⚠️ **`0020_场景首帧` 的 latent 默认值是 `1920×1088`(2 倍), 但它被 md 宽高覆盖** ——
实测产物 960×544 正是 md 值, 说明覆盖生效。别被 `EmptySD3LatentImage` 的静态默认值误导。

## 6. H3 shift 配对(改 LoRA 必查)

| LoRA 谱系 | 档位 | shift(video/audio) |
|---|---|---|
| Ref2VA 全部(4step v0.1 / 8step v1.0 768p) | 任意 | **12 / 3** |
| FL2VA 768p 系 | 768p | **6 / 3** |
| FL2VA 544p 系 | 480p / 544p | **12 / 3** |

⚠️ **Ref2VA 不随分辨率改 shift** —— 它的 8step 文件名带 `768p` 只说明**训练分辨率**,
不蕴含 shift 6; 官方两个 LoRA 推荐**都是 12/3**。`6/3` **只属于 FL2VA 的 768p 系**。
第三方资料(comfyui-wiki、vpipe)常在此记错, **不可作为依据**。
完整配对表与权威来源见根 `AGENTS.md`。

### 6.1 自动切档映射(脚本 `--resolution` 实测)

`workflow-to-prompt.py --resolution W*H` 会按 `UNETLoader` 的 `ref2va`/`fl2va` 判定谱系,
按**短边**(≥768 归 768p, 否则 544p)选档, 同时替换两处 LoRA 并按**替换后**的步数配 shift:

| 谱系 | 档位 | 4步 LoRA | 8步 LoRA | shift |
|---|---|---|---|---|
| FL2VA | 544p | `fl2v_lightx2v_turbo_4step_v0.1_comfy` | `fl2v_turbo_8step_v1.0_comfyui_bf16` | 12/3 |
| FL2VA | 768p | `fl2v_turbo_4step_v1.0_768p_comfyui_bf16` | `fl2v_turbo_8step_v1.0_768p_comfyui_bf16` | 6/3 |
| Ref2VA | 544p | `ref2v_turbo_4step_v0.1_comfyui_bf16` | `ref2v_turbo_8step_v1.0_768p_comfyui_bf16` | 12/3 |
| Ref2VA | 768p | 同上 | 同上 | **12/3**(不变) |

实测(2026-10-15):

- `0041_首帧视频` + `960*544` → 两个 LoRA 换成 544p 系、shift `6/3`→`12/3`、selector `横480`→`默认` ✓
- `0044_参考视频` + `960*544` → **零改动**(本就是 544p/12/3/默认) ✓
- `0044_参考视频` + `1344*768` → shift **保持 12/3**(Ref2VA 铁律) ✓
- `0031_首帧场景` + `960*544` → **零改动**(本就是 544p/12/3/默认) ✓
- `0031_首帧场景` + `1344*768` → 切 768p 系、shift `12/3`→`6/3` ✓

边界拒绝(实测): `1664*960`(短边超)、`1376*768`(面积超)、`960*545`(非 32 倍数) 全部报错退出。

## 7. 执行模板

### 7.1 单工作流(全自动跑一段)

```bash
cd /root/Comfy-S

# ① 干跑: 转换 + 刷新 mdtable + 分辨率覆盖, 只导出不提交
#    (先看节点数、提示词长度、以及 `*` 开头的覆盖条目是否符合预期)
/root/miniconda3/envs/comfy/bin/python \
  .agents/skills/comfyui-workflow-runner/scripts/workflow-to-prompt.py \
  "0044_参考视频.json" --refresh-md --resolution 960*544 --dump /tmp/prompt-0044.json

# ② 检查 /tmp/prompt-0044.json(参考图是否解析成功、LoRA 谱系、sigma shift、宽高 selector)

# ③ 真提交(脚本自动轮询 /history 并打印产物文件名)
/root/miniconda3/envs/comfy/bin/python \
  .agents/skills/comfyui-workflow-runner/scripts/workflow-to-prompt.py \
  "0044_参考视频.json" --refresh-md --resolution 960*544 --submit
```

> ⚠️ **`--resolution` 是「本次给了分辨率参数就必加」**, 漏加 ⇒ selector 停在旧档 ⇒
> md 宽高被**静默忽略**, 且 LoRA/shift 停在旧档也不会报错。给了分辨率却漏传的排查法:
> 跑完看产物分辨率是否等于目标值(S7 必查项)。
>
> ⚠️ `--refresh-md` 与 `--resolution` **都只改 API 载荷, 不写回工作流 JSON**。要让磁盘上的
> 快照也一致, 需 `GET /fallingts_mdtable/read` 后把结果写回 `widgets_values[0]` **与**
> `widgets_values_named.data`(两个镜像必须逐字节相同)。

### 7.2 提交前强校验(内联, 不落盘)

```bash
cd /root/Comfy-S
/root/miniconda3/envs/comfy/bin/python - <<'PY'
import json, re, urllib.parse, urllib.request, pathlib
API = "http://127.0.0.1:8188"
base = pathlib.Path("stories/七纹刻印")
refs = {}
for md in sorted(base.glob("*.md")):
    for m in re.finditer(r"@\{([^}]+)\}", md.read_text(encoding="utf-8")):
        refs.setdefault(m.group(1), set()).add(md.name)
bad = []
for r in sorted(refs):
    # ⚠️ 必须把 @{} 连同包起来: /resolve 认的是 `@{表名/ID}` 这种引用串,
    #    传裸路径 `0011_万物建模/00001_陈落` 会**全部**解析失败(实测 20/20 误报)。
    q = urllib.parse.urlencode({"path": "@{" + r + "}"})
    try:
        j = json.load(urllib.request.urlopen(f"{API}/fallingts_mdtable/resolve?{q}", timeout=30))
        ok, p = bool(j.get("ok")), j.get("path")
    except Exception as e:
        ok, p = False, f"请求失败 {e}"
    if not ok:
        bad.append((r, sorted(refs[r]), p))
print(f"共 {len(refs)} 条引用, 失败 {len(bad)} 条")
for r, where, why in bad:
    print(f"  ✗ {r}  (出现在 {where})  -> {why}")
raise SystemExit(1 if bad else 0)
PY
```

**任一条失败 ⇒ 拒绝提交**(失败会在执行时静默变成 `None`, 不报错)。
⚠️ 该脚本的 `/resolve` 会走**兜底趟**, 所以「通过」不代表引用目录写对了 —— 详见 §3 的
`@{0011_万物建模/00001_陈落_左上}` 例子。要严格核对目录, 需把返回的 `path` 与
引用的表名段做前缀比对。

### 7.3 Run 前 reset(必做)

```bash
for ep in preview-image preview-video preview-audio audio-trim; do
  curl -s -X POST "http://127.0.0.1:8188/${ep}/reset" >/dev/null
done
curl -s -X POST http://127.0.0.1:8188/proceed/reset >/dev/null
```

不做的话 `_reset_generation` 不递增 ⇒ ComfyUI 执行缓存会把节点**跳过**。

### 7.4 保存产物(预览节点只写 `temp/`)

```bash
# 视频
curl -s -X POST http://127.0.0.1:8188/preview-video/save/901 \
  -H 'Content-Type: application/json' \
  -d '{"filename_prefix":"0044_参考视频","filename_prefix_linked":false,
       "filename_suffix":"","workflow_name":"0044_参考视频"}'
# 回读校验(很多端点字段名错也返 200)
curl -s http://127.0.0.1:8188/preview-video/state/901
```

⚠️ `AutoSaveImage`(0035 / 0050 的图片保存节点)**没有保存按钮、执行到即落盘**,
不要对它调 `/preview-image/save/{id}`; 但提交时要**自带工作流名**,
否则产物落回 output 根而不是 `<工作流名>/` 子目录。

### 7.5 放行「继续」闸门

```bash
curl -s -X POST http://127.0.0.1:8188/free \
  -H 'Content-Type: application/json' -d '{"unload_models":true,"free_memory":true}'
curl -s -X POST http://127.0.0.1:8188/proceed/continue/43
# 未跑到该节点会 400「没有上游数据, 请先运行到该节点」
```

### 7.6 产物验证

⚠️ **本机没有 `ffprobe`** (实测 `command not found`, exit 127); `imageio_ffmpeg` 只带 ffmpeg
不带 ffprobe; `motion-profile.py` 的 `FALLBACK_FFMPEG` 是 Windows 路径, **在本机直接 `sys.exit`**。
所以用 PyAV 探针 + `imageio_ffmpeg` 抽帧:

```python
import av, imageio_ffmpeg, subprocess
FF = imageio_ffmpeg.get_ffmpeg_exe()
f = "media/七纹刻印/0044_参考视频/00011_xxx.mp4"
with av.open(f) as c:                       # 时长/分辨率/fps/帧数/是否有音频流
    v = c.streams.video[0]
    print(v.codec_context.width, v.codec_context.height, float(v.average_rate),
          v.frames, float(c.duration) / 1e6, len(c.streams.audio) > 0)
subprocess.run([FF, "-v", "error", "-y", "-i", f,
                "-vf", "fps=1/3,scale=640:-1,tile=4x2", "-frames:v", "1", "/tmp/grid.png"])
# 然后必须真的 read /tmp/grid.png 看图判断内容与连续性
```

**必须核对探到的分辨率 == 本次目标分辨率**(`0011` 产物 = md 宽高, ×1 直通, 见 §5.3)。
动作幅度用 PyAV 抽帧 + 相邻帧绝对差 (`np.abs(np.diff(frames, axis=0)).mean()`),
**不要只看 `pblack`**(H3 颗粒下会饱和)。

**同时必须核对落盘规则**(插件统一口径, 详见 `production-flow.md` §7):

```python
import os, re
# ① 目录 = md 表文件名(无表节点才是工作流名)
assert os.path.basename(os.path.dirname(f)) == 表名, "产物目录与表文件名不一致"
# ② 文件名以 0000x 开头, 与表内 ID 一致
assert re.match(r"^\d{5}_", os.path.basename(f)), "文件名不合 ID 规则"
```

⚠️ **唯一已知例外**: `0034_世界模型` 的 `PreviewImageSave`(`#3`)前缀硬编码
`'0034_世界模型_360长图'`, 不以 `0000x` 开头 —— 跑它时需在 API 载荷层面覆盖, 或明确告知用户。

## 8. 运行账本(每次追加, 不要清空)

```json
{"run_id":"...","ts":"...","story":"七纹刻印","table":"0044_参考视频",
 "row":"00011_xxx","lines":[121,180],"anchor_first":"首段前20字","anchor_last":"末段前20字",
 "prompt_sha256":"...","workflow":"0044_参考视频.json","workflow_sha256":"...",
 "refs":[{"slot":"<Picture 2>","ref":"@{0011_万物建模/00001_陈落}","path":"...","sha256":"..."}],
 "width":960,"height":544,"seconds":15,"seed":123,
 "actions":[{"endpoint":"/preview-video/save/901","http":200,"artifact":"..."}],
 "status":"success"}
```

## 9. 常见坑(每条都真实踩过)

| 坑 | 后果 | 对策 |
|---|---|---|
| 控件按**位置**对齐 | 动态子控件(`COMFY_DYNAMICCOMBO_V3`)占位导致后续整体错位一格, **静默**传到错误参数 | 按**名字**对齐; 动态子项用扁平点号 `selection.tau` |
| `Reroute` 当节点处理 | API 图里不存在, 下游 `filename_prefix` **全部丢链** | 穿透到真实源节点 |
| `MarkdownNote`/`Note` | 纯前端节点, 进 prompt 会报错 | 跳过 |
| 字节完全相同地重提 | 执行缓存命中, **几秒"跑完"**, 实际没跑 | 改 seed 或改提示词 |
| 只改 md 没刷新快照 | 跑了但用的还是旧提示词 | `--refresh-md`; 提交前比对提示词长度 |
| 服务重启 | 所有按钮状态是**模块级内存**, 重启即失 | 跑完**立刻**操作保存/截帧/放行 |
| 参考图被删/改名 | `@{...}` **静默变 `None`** | §7.2 强校验 |
| 端点返 200 但字段名错 | 如 `frame-remove` 传 `index` 会静默 no-op | **回读 state** 校验 |
| `/resolve` 传**裸路径** | 20 条引用**全部**误报失败 | 必须包成 `@{表名/ID}` 再传 |
| `@{...}` 目录段写错 | 兜底趟**掩盖**错误, 一旦源文件被清理就静默 `None` | 引用一律写**产物真实所在目录** |
| 改了 md 宽高但尺寸不变 | 宽高 selector 停在「横480」档**忽略 md** | 提交必带 `--resolution`(§5.1) |
| 换 LoRA 没改 shift | 无报错, 但画面/音频**结构性崩坏** | 用 `--resolution` 自动配对; Ref2VA 恒 12/3 |
| 用 `ffprobe`/`motion-profile.py` | 本机没装 ffprobe, 脚本 `sys.exit` | 用 PyAV + `imageio_ffmpeg`(§7.6) |

## 10. 本机当前缺口(跑之前先确认)

实测(2026-10-15):

- ✅ **图像链 / H3 视频链模型齐全** —— `qwen_image_2512_fp8_e4m3fn_scaled_comfyui`、
  `qwen_image_edit_2511_fp8mixed`、`qwen_2.5_vl_7b_fp8_scaled`、
  `minimax_h3_ref2va_pruned_int8_convrot`、`qwen3vl_32b_minimax_h3_int8_convrot`、
  `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16`、`minimax_h3_video_vae_int8_convrot`
  全部存在 ⇒ **S1~S5(资产 → 视频)可直接跑通**。
- ❌ **Qwen3-TTS(0063 文生人声 / 0064 参考人声)不可用** —— `models/TTS/` 下只有
  `Qwen3-TTS-12Hz-1.7B-VoiceDesign.zip` / `…-1.7B-Base.zip`, **没有解压目录**
  (`models/TTS/Qwen/`)。插件按 `models/TTS/<repo_id>` 找**解压后的目录**, 不是 zip。
  ⇒ **S6 音频阶段当前会失败**。两条出路: ①用户先解压那两个 zip; ②本技能跳过 S6,
  只交付视频(音频留空)。

> 因此 auto 的默认边界是 **S1~S5 出视频**; 需要配音/音效时先让用户解压 TTS 模型。
> 0060/0061/0062(背景音乐/环境音效/效果音效)走 `stable_audio_3_medium.safetensors`,
> **与 TTS 无关**, 不受此缺口影响。
