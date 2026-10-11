# RunningHub API 读取指南(工作流列表 / 详情 / 内容)

调研日期:2026-08-03。来源:通过页面 SSR 数据 + 前端 JS 反推(BYkLh8GN.js 为工作流 API 模块,xpIlMWPs.js 为广场列表 API 模块),并用 Bearer token 实测通过。适用于读取 RunningHub 工作流广场列表(精选 + 全部分类)、详情与工作流 JSON。

## 0. 认证方式

- 请求头:`Authorization: Bearer <token>`
- token 获取:登录 `runninghub.cn` 后,浏览器开发者工具 → Network → 复制任意接口请求的 `Authorization` 头;或从站点 localStorage 中取(登录后存有 `token` 类字段)
- 有效期:约 30 天(JWT 的 `exp` 字段,本次实测 token 至 2026-09-02 前后);过期后重新抓取即可
- 失败特征:token 缺失/过期返回 `{"code":412,"msg":"TOKEN_INVALID"}`;参数错返回 `301 PARAMS_INVALID` / `301 must not be null`;路径不存在返回 `404 NOT_FOUND`
- ⚠️ **token 属于敏感凭据:不要写入文档、不要提交到 git。本文件不保存任何真实 token。**

## 1. 工作流列表(工作流广场首页数据)

- 接口:`POST https://www.runninghub.cn/api/secondary-page/workflow/published`
- Body:`{}`(空对象)
- 返回结构:`data.pageForm.groups[]`,每个分组含 `id / title / titleCn / sort / slots[]`
  - `slots[].title` — 工作流名称
  - `slots[].jumpUrl` — 详情页地址,形如 `https://www.runninghub.cn/post/<id>` 或 `/post/<id>/aiDetail`
- 实测结果(2026-08-03):4 个分组、27 个工作流
  - ComfyUI 热门内容(7):全能视频X-编辑视频-官方稳定版、Seedance2.0全能参考视频、全能图片 Pro、LTX2.3 去水印、Qwen-image 洗图、DaSiWaV9、Qwen3-TTS+LTX-2
  - ComfyUI 精选工具(7):数字人对口型、电商主图、Wan2.2 首尾帧 for 循环、电商详情页 V3、Qwen3VL+Next Scene、SeedVR2、万能去水印
  - ComfyUI 图像设计(7):图像分层 PSD、涂鸦注解造像师、FLUX2-KLEIN、老照片划痕清理、G Image 2.0、挂拍转立体图、kontext 金属修图
  - MiniMax H3 开源版工作流(6):文生视频、首帧参考、尾帧参考、首尾帧参考、多图参考、图像+音频参考
- 说明:这是"精选展示页"数据,不等于全量广场/搜索列表;全量列表另有接口(见 §5)。

> 全量工作流广场(21 个分类 × 排序 × 时间窗口)的完整拉取方法见 **§9**。

## 2. 工作流详情

- 接口:`POST https://www.runninghub.cn/api/workflow/getDetail`
- Body:`{"workflowId": "<post_id>"}`
- 返回:`data` 含 `id / name / desc / owner{id,name} / publishTime / timestamp / md5 / nodeCount / status / workflowState / usedModels / customNodes / primitiveNodes / publishAccess / statisticsInfo` 等
  - `usedModels` — 工作流所需的模型文件列表(数组)
  - `customNodes` — 依赖的自定义节点列表(数组)
  - `primitiveNodes` — ComfyUI 内置节点列表(数组)
  - `nodeCount` — 节点总数;`publishAccess` — 可见性/加密状态(`granted`/`encrypted`)
  - ⚠️ 注意:详情接口里的 `workflowContent` 恒为 `null`,**工作流内容请用 §3 的 getContent 获取**
- 关键点:参数名**必须是 `workflowId`**;`id / postId / workId` 均报 `301 must not be null`
- 别名:`POST /api/portal/workflow/detail` 与 `getDetail` 返回完全相同(实测)

## 3. 工作流内容(ComfyUI JSON,重点)

- 接口:`POST https://www.runninghub.cn/api/workflow/getContent`
- Body:`{"workflowId": "<post_id>"}`
- 返回:`data.workflowName` + `data.workflowContent`
  - `workflowContent` 是**字符串化的 ComfyUI 工作流 JSON**(含 `last_node_id / nodes / links`)
  - `json.loads()` 后即为标准 ComfyUI 工作流,可保存为 `.json` 直接导入
- 实测:H3 文生视频(10 节点/10 连线),节点为 RunningHub 私有 `RHMiniMaxH3*` 系列,本地运行需先装对应自定义节点

## 4. 工作流导出(前端"下载"按钮)

- 接口:`POST https://www.runninghub.cn/api/workflow/export`,`responseType: blob`
- Body:`{"workflowId": "<post_id>"}`
- 即详情页"下载"按钮调用的接口;实测返回 `Content-Disposition: attachment; filename=<工作流名称>.json`,body 为可直接导入 ComfyUI 的工作流 JSON 文件
- 实测:320 个公开工作流全部可成功下载(文件名按服务端下发,非法字符需清洗)
- 需要登录态
- 未登录状态下所有 `/api/workflow/*`、`/api/aiDetail/*` 均返回 `TOKEN_INVALID`,无法匿名下载

## 5. 其他已知接口(个人工作台 / 模板)

全部为 POST(来自前端 `BYkLh8GN.js` 工作流 API 模块):

| 接口 | 用途 |
|---|---|
| `/api/workflow/templateList` | 模板列表 |
| `/api/workflow/user/list` | 我的工作流列表 |
| `/api/workflow/page/simpleList` | 工作流分页列表 |
| `/api/workflow/simpleList` | 简单列表 |
| `/api/workflow/create` | 创建 |
| `/api/workflow/setContent` | 保存内容 |
| `/api/workflow/getMd5` | 内容 MD5 |
| `/api/workflow/upload` | 上传 |
| `/api/workflow/publish` | 发布 |
| `/api/workflow/remove` / `copy` / `reName` | 删除 / 复制 / 重命名 |
| `/api/workflow/folder/list` 及 folder 系列 | 文件夹管理 |
| `/api/secondary-page/workflow/draft` | 草稿页数据(与 published 对称) |

### 5.1 广场(portal)接口(xpIlMWPs.js 模块,全部 POST)

| 接口 | 用途 |
|---|---|
| `/api/portal/tag/tree` | 分类树(工作流/模型等,rang 区分) |
| `/api/portal/template/list` | **全量工作流列表**(分类+排序+时间窗口) |
| `/api/search/workflow` | 搜索工作流(portalTemplateListRes 的 searchPage 分支) |
| `/api/portal/workflow/detail` | 广场工作流详情 |
| `/api/comment/list` / `subComments` / `create` / `delete` | 评论相关 |
| `/api/portal/template/tags` | 已废弃/无效(实测 404),用 `/api/portal/tag/tree` |

## 6. 前端反推方法(接口变更后如何自查)

1. 打开目标页面,查看 SSR HTML 中的内嵌数据与 `<link rel="modulepreload">` 引用的 `/_nuxt/*.js` 脚本
2. 在 JS 里搜索 API 路径字符串,如 `"/api/workflow/getDetail"`;懒加载模块在页面组件的其他 chunk 中(本次关键模块是 `BYkLh8GN.js`)
3. 页面路由 → 组件映射在主 bundle(如 `VQXFaQrF.js`)里:搜 `path:"/page-workflow"` 可得组件 chunk(`Z_AIYDQz.js`),其内含列表接口 `/api/secondary-page/workflow/published`
4. 用带 token 的请求实测(POST 优先;同一路径 GET 可能 404/参数错,别急着下结论)

## 7. MiniMax H3 开源版 6 个工作流 ID(2026-08-03)

| 工作流 | post id | 详情页 |
|---|---|---|
| H3 文生视频 | 2084079636237078529 | https://www.runninghub.cn/post/2084079636237078529 |
| H3 首帧参考生视频 | 2084067455902765057 | https://www.runninghub.cn/post/2084067455902765057 |
| H3 尾帧参考生视频 | 2084071981670035457 | https://www.runninghub.cn/post/2084071981670035457 |
| H3 首尾帧参考生视频 | 2084070256573767682 | https://www.runninghub.cn/post/2084070256573767682 |
| H3 多图参考生视频 | 2084117309760823297 | https://www.runninghub.cn/post/2084117309760823297 |
| H3 图像+音频参考生视频 | 2084124735289520130 | https://www.runninghub.cn/post/2084124735289520130 |

## 8. 实测示例(占位 token,自行替换)

```python
import requests, json

TOKEN = "<你的 Bearer token>"
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Authorization": "Bearer " + TOKEN,
    "Referer": "https://www.runninghub.cn/page-workflow",
    "Content-Type": "application/json",
}

# 1) 列表
r = requests.post("https://www.runninghub.cn/api/secondary-page/workflow/published", json={}, headers=H)
groups = r.json()["data"]["pageForm"]["groups"]
for g in groups:
    for s in g["slots"]:
        print(g.get("titleCn"), "|", s.get("title"), "|", s.get("jumpUrl"))

# 2) 工作流 JSON
wid = "2084079636237078529"  # H3 文生视频
r = requests.post("https://www.runninghub.cn/api/workflow/getContent", json={"workflowId": wid}, headers=H)
data = r.json()["data"]
wf = json.loads(data["workflowContent"])
print(data["workflowName"], len(wf["nodes"]), "nodes")
# 保存
# with open("h3_t2v.json", "w", encoding="utf-8") as f:
#     json.dump(wf, f, ensure_ascii=False, indent=2)
```

PowerShell 版要点:同一 POST 请求用 `Invoke-WebRequest -Method POST -Body '{"workflowId":"..."}' -Headers @{Authorization="Bearer $token"; 'Content-Type'='application/json'}`;中文注意用 UTF-8 解码响应内容。

## 9. 全部分类工作流列表拉取(官网 /workflows 全量广场,重点补充)

官网 `/workflows` 页面对应全量工作流广场(2026-08-03 实测 `total=68506`),支持**分类 × 排序 × 时间窗口**三维筛选。本次"每类 20 条、按点赞排行"的完整拉取方法如下。

### 9.1 分类树接口

- 接口:`POST https://www.runninghub.cn/api/portal/tag/tree`
- Body:`{"rang": "WORKFLOW"}`
- 返回:`data` 为数组,每项为一级分类:`{id, name, childTags: [{id, name}, ...]}`
- 实测:21 个一级分类(完整清单见 §10)
- ⚠️ **关键坑**:列表接口的 `tags` 参数必须传**子标签(childTags)的 ID 数组**。直接传一级分类 ID 只会返回少量官方模板(实测 8 条且点赞全为 0)

### 9.2 全量列表接口

- 接口:`POST https://www.runninghub.cn/api/portal/template/list`
- Body 参数表(实测):

| 参数 | 说明 | 实测值 |
|---|---|---|
| `size` | 每页条数 | 30(前端固定值,不宜改大) |
| `current` | 页码 | 1 开始 |
| `sort` | 排序 | `RECOMMEND` 推荐 / `REPUTATION` 人气 / `HOTTEST` 最热 / `NEWEST` 最新 |
| `tags` | 分类标签 ID 数组 | 子标签 ID 列表(见 9.1) |
| `search` | 关键词(可选) | 省略 |
| `days` | 时间窗口(天) | `3` / `7` / `30` / `90`(90=最近三个月) |

- 排序取值来源:前端 `Q` 常量 `RECOMMEND / REPUTATION / HOTTEST / NEWEST`(i18n:推荐/人气/最热/最新)
- 时间档位来源:系统配置 `list_query_valid_days`(getConfigSystem 接口下发),前端 timeConfig 渲染成 `{key, text, value:{days:N}}`,展开进请求体后**实际生效的就是顶层 `days` 字段**
- 返回结构:
  - 分页:`data.total / size / current / pages / hasNext / hasPrevious / nextCursor`
  - 记录:`data.records[]`(字段字典见 §11)

### 9.3 "最近三个月"的正确理解(重要)

- `days=90` 是**热度统计窗口**:服务器用最近 90 天计算 REPUTATION/HOTTEST 的"热度",**不是按发布时间过滤**
- 因此结果可能包含 2025 年发布、近三个月依然热门的工作流 —— 与官网 UI 行为完全一致
- 若需要"发布时间在最近三个月",请用 `records[].timestamp` 自行过滤

### 9.4 完整拉取流程(本次执行步骤)

1. 调用 9.1 分类树 → 得到 21 个一级分类及其子标签 ID
2. 对每个一级分类,循环翻页(每页 size=30,取前 3 页):
   - Body:`{"size":30, "current":page, "sort":"REPUTATION", "days":90, "tags":[该分类全部子标签ID]}`
   - 依据 `data.hasNext` 决定是否继续翻页
3. 跨页合并去重(同 `id` 覆盖)
4. 按 `statisticsInfo.likeCount` 降序排序
5. 每类取前 20 条写入 `workflows-list.md`(不足 20 的全部列出;本次仅 `AI漫剧` 类只有 2 条)
6. 详情页地址 = `https://www.runninghub.cn/post/<id>`

### 9.5 完整 Python 实测脚本

```python
import sys, time, json, datetime
import requests

TOKEN = "<你的 Bearer token>"   # 不要写死在脚本里,建议从环境变量读取
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Authorization": "Bearer " + TOKEN,
    "Referer": "https://www.runninghub.cn/workflows",
    "Content-Type": "application/json",
}
API = "https://www.runninghub.cn"

def post(path, body):
    for _ in range(3):                       # 简单重试
        try:
            return requests.post(API + path, json=body, headers=H, timeout=40).json()
        except Exception:
            time.sleep(2)
    raise RuntimeError("request failed: " + path)

# 1) 分类树
tree = post("/api/portal/tag/tree", {"rang": "WORKFLOW"})["data"]
cats = [{"id": c["id"], "name": c["name"],
         "childs": [ct["id"] for ct in (c.get("childTags") or [])]} for c in tree]

# 2) 逐分类拉取(3 页 x 30 条)
results = {}
for cat in cats:
    merged = {}
    for page in (1, 2, 3):
        body = {"size": 30, "current": page, "sort": "REPUTATION",
                "days": 90, "tags": cat["childs"] or [cat["id"]]}
        j = post("/api/portal/template/list", body)
        d = j.get("data") or {}
        for r in d.get("records") or []:
            merged[r["id"]] = r
        if not d.get("hasNext"):
            break
        time.sleep(0.3)

    # 3) 整理 + 按点赞降序
    rows = []
    for r in merged.values():
        st = r.get("statisticsInfo") or {}
        ts = int(r.get("timestamp") or 0) / 1000
        dt = datetime.datetime.fromtimestamp(ts,
              tz=datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d") if ts else ""
        rows.append({"id": r["id"], "name": r.get("name") or "",
                     "like": int(st.get("likeCount") or 0),
                     "use": int(st.get("useCount") or 0),
                     "collect": int(st.get("collectCount") or 0),
                     "author": (r.get("owner") or {}).get("name") or "",
                     "date": dt, "system": bool(r.get("systemWorkflow"))})
    rows.sort(key=lambda x: -x["like"])     # 点赞从高到低
    results[cat["name"]] = rows[:20]        # 每类取前 20

# 4) 输出(此处自行拼接 Markdown 表格)
for cat_name, rows in results.items():
    print(f"## {cat_name}({len(rows)} 条)")
    for i, r in enumerate(rows, 1):
        print(f"| {i} | {r['name']} | {r['like']} | {r['use']} | {r['collect']} | "
              f"{r['author']} | {r['date']} | https://www.runninghub.cn/post/{r['id']} |")
```

PowerShell 要点:列表接口同样是 POST,Body 用 UTF-8 JSON;分页判断 `hasNext`;`likeCount/useCount/collectCount` 在响应里是**字符串**,记得转 int 再排序。

## 10. 分类树全量(21 个一级分类,2026-08-03 实测)

| 一级分类 | 子标签数 | 子标签 |
|---|---|---|
| 数字人 | 1 | 数字人 |
| 图片生成 | 3 | 文生图、图生图、反推提示词 |
| 视频生成 | 3 | 文生视频、图生视频、视频生视频 |
| 视频特效 | 6 | 人物类特效、场景类特效、战斗特效、滤镜特效、转场特效、视频运镜 |
| 二次元 | 13 | 写实、美少女、热门IP、动漫角色、游戏角色、校园题材、和风题材、魔幻风格 等 |
| 音频生成 | 1 | 音频生成 |
| 海报 | 2 | 海报制作、字体 |
| 图片处理 | 15 | 抠图、去水印、扩图、高清放大、滤镜、局部重绘、精修、擦除 等 |
| 摄影 | 8 | 人像写真、证件照、物品摄影、换脸、宠物摄影、妆容、换装、其它摄影 |
| 影视游戏 | 7 | 角色设计、角色一致性、分镜生成出图、角色表演、场景道具、视频、其他影视游戏 |
| 3D模型 | 7 | 人物角色、场景环境、道具物件、建筑结构、交通工具、武器装备、生物动物 |
| 创意玩法 | 5 | 风格迁移、创意形象、新奇创意、盲盒手办、其他创意 |
| 平面设计 | 4 | logo、节日、服饰、其它平面设计 |
| 电商产品 | 8 | 商品换背景、商品换包装、模特产品展示、图案迁移、重新打光、服装展示、商品替换、其它电商产品 |
| 室内外设计 | 6 | 场景中加人物、毛坯房一键改造、装修风格变换、家具/建筑添加背景、手稿到渲染图、其它建筑及空间设计 |
| 风格画作 | 11 | 经典绘画风、手工艺风、CG幻想、现代创意插画、像素风、中国风、欧美风格、热门IP 等 |
| API | 22 | Kontext、全能图片G、悠船、jimeng、全能视频V、Kling、全能图片、混元3D 等 |
| AI漫剧 | 4 | 脚本梳理、资产创建、分镜图制作、视频生成 |
| 视频处理 | 8 | 动作迁移、视频风格转换、视频超分、移除视频元素、去水印、视频换脸、视频换背景、其它视频处理 |
| 插件 | 2 | 葫芦娃、其它插件 |
| 其他 | 1 | 其他 |

> 说明:上表只列子标签名称;调用 API 时所需的**子标签 ID** 请实时调用 §9.1 分类树接口获取(名称↔ID 一一对应,ID 为雪花号)。

## 11. records 字段字典(portal/template/list)

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 工作流 ID,详情页 = `https://www.runninghub.cn/post/<id>` |
| `name` | string | 工作流名称 |
| `desc` | string | 简介(常含 UP 主引导语/邀请码) |
| `systemWorkflow` | bool | 是否官方/系统工作流 |
| `publishTime` | string | 发布时间(ISO 8601,UTC) |
| `timestamp` | string | 发布时间毫秒时间戳(换算本地时间用) |
| `preview` | string/null | 预览图 |
| `owner` | object | `{id, avatar, name}` 作者信息 |
| `statisticsInfo` | object | `{likeCount 点赞, downloadCount 下载, useCount 使用, pv 浏览, collectCount 收藏}`,**数值均为字符串** |
| `nodeCount` | number/null | 节点数 |
| `liked` | int | 当前用户是否已点赞 |
| `covers` | array | 封面图列表(`{url, thumbnailUri, imageWidth, imageHeight}`) |
| `tags` | array | 标签 `[{id, name, nameEn}]` |
| `labels` | string | 标签名逗号串 |
| `seq` | string | 排序权重 |
| `homeShow` | string/null | 首页展示标记 |

## 12. 注意事项

- RunningHub 接口全部走 POST(前端 axios 封装 `r.post`);相同路径用 GET 会 404 或参数错误
- H3 工作流节点为 RH 私有节点(`RHMiniMaxH3DirectModelLoader` 等),JSON 主要在 RunningHub 平台运行;本地 ComfyUI 需先装对应自定义节点
- `getContent` 返回的 JSON 可直接导入 ComfyUI,但私有节点缺失时前端会提示缺节点
- 本目录(`webs\RunningHub\`)已纳入根仓库跟踪(2026-09 起),下载的工作流文件同样提交
- 全量列表的 `tags` 参数必须传**子标签 ID 数组**(见 §9.1);分类筛选别用一级分类 ID
- `days` 是热度窗口不是发布时间过滤(见 §9.3);按点赞排行时记得把 `likeCount` 从字符串转 int
- 广场接口(/api/portal/*)在 `/api` 前缀下实测有效;`/api/portal/template/tags` 已失效(404),分类用 `/api/portal/tag/tree`
- 批量下载时**必须按工作流 ID 去重**:同一工作流可同时上多个分类榜,否则会对同一 ID 重复发起 export

## 12.1 2026-09-17 复核(下载量与文件名冲突)

- 本次条件:`sort=HOTTEST`、`days=3`、每类前 50,21 个分类共 **804** 条唯一工作流;本地已有 384 条直接复用,
  新增下载 **420** 个全部成功(脚本 `runninghub-update.py`,token 走环境变量 `RUNNINGHUB_TOKEN`;脚本随根 `scripts\` 于 2026-10-11 移除)。
- **不要每次全量重下**:`export` 单请求最慢 1~2 分钟,2500+ 个文件逐个重下不可行;应按 ID 与本地比对,只补缺失的。
- **同名不同工作流是常态**:不同 ID 的工作流可能取完全相同的名字(如多个"换衣服++衣服展示+一键换装"),且内容长短不一。
  保存前若目标名已存在,**必须加 `<工作流ID>_` 前缀**而不是覆盖,否则会永久丢掉旧文件(本库现有约 160 组这类前缀文件)。
- 复核结论:本次唯一一组真重复是同一 ID 因跨分类被入队两次(服务端两次返回的文件名不同),按 ID 去重后修复;
  「同名不同 ID」的文件大小各异,属正常共存,**不是重复**。

## 12.2 2026-09-21 复核(全量更新,本地累计 2831 个)

- 本次条件与上次一致:`sort=HOTTEST`、`days=3`、每类前 50,21 个分类共 **804** 条唯一工作流
  (表格行 1002 行,同一工作流可同时上多个分类榜)。
- 结果:本地已有 **484** 条直接复用,新下载 **320** 个,**全部成功**(失败 0);
  本地工作流库由约 2511 增至 **2831** 个 json,分布仍为 21 个一级分类目录。
- 新下载的 320 个里有 **308** 个遇到同名冲突(目标名已被别的 ID 占用),脚本按约定加 `<工作流ID>_` 前缀保存,
  未覆盖任何旧文件 —— 这印证了 §12.1 的结论:同名不同工作流是常态,必须加前缀而非覆盖。
- **落地校验**(建议每次更新后都跑):
  1. 从 `workflows-list.md` 反解全部 `post/<ID>` 与下载路径,逐条 `os.path.exists` → 本次 **0 缺失**;
  2. 检查是否有**不同 ID 指向同一文件路径**(并发写同名文件的覆盖信号)→ 本次 **0 处**;
  3. 抽样 `json.load` 校验合法性 → 60 个样本全部可解析,平均 46.2 节点,大小 2.5 KB ~ 3.19 MB。
- ⚠️ **token 前缀与 AutoDL 相反,别搞混**:本脚本内部写死 `"Authorization": "Bearer " + TOKEN`,
  所以环境变量 `RUNNINGHUB_TOKEN` 要传**裸 JWT**(不带 `Bearer `),否则会拼成 `Bearer Bearer eyJ...` 而 412。
  AutoDL 那边(`autodl-update-models.py`)则是**裸 token 直接放**,两者口径不同。
- 反解 md 时**别用 `[^)>]+?` 匹配文件名**:工作流名里可能含 `)`(如 `xxx(1).json`),该正则会截断而漏掉约 30 条;
  用 `post/(\d{15,20})` 统计 ID 数才是准的(本次 804,与脚本一致)。

---

## 13. 附录:获取工作流下载地址/文件 — 最详细流程(合并自原 API.md)


调研日期:2026-08-03,全部接口经真实 Bearer token 实测。本文是"如何从 RunningHub 拿到某个工作流的下载地址/文件"的完整操作手册;接口通用说明见本文上文各节。

## 0. 结论速览

| 需求 | 用哪个 | 说明 |
|---|---|---|
| 下载工作流 JSON 文件(本地保存) | `POST /api/workflow/export` | 返回 `attachment` 文件,文件名即工作流名 |
| 只读工作流内容(字符串) | `POST /api/workflow/getContent` | 返回 `workflowContent` 字段(ComfyUI JSON 字符串) |
| 工作流元数据(节点数/依赖模型/自定义节点) | `POST /api/workflow/getDetail` | 不含内容(`workflowContent` 恒为 null) |
| 网页手动下载 | 详情页"下载"按钮 | 本质就是调 export,需登录 |

> ⚠️ 没有"匿名/静态下载 URL":所有下载都走 POST 接口且必须带登录 token。所谓"下载地址"= 可复现的 POST 调用(带工作流 ID)。

## 1. 前置条件

### 1.1 认证

所有请求带请求头:

```
Authorization: Bearer <token>
Content-Type: application/json
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...
Referer: https://www.runninghub.cn/workflows
```

token 获取:登录 runninghub.cn → 浏览器 F12 → Network → 复制任意接口请求的 `Authorization` 头。有效期约 30 天(JWT `exp` 字段)。

### 1.2 工作流 ID

每个工作流的唯一 ID 是 19 位雪花号:

- 详情页 URL 提取:`https://www.runninghub.cn/post/<ID>`(或 `/post/<ID>/aiDetail`)
- 列表接口返回:`records[].id`
- 本地 list.md:每行链接 `https://www.runninghub.cn/post/<ID>`

## 2. 方式 A:网页手动下载(最简单)

1. 浏览器登录 RunningHub
2. 打开工作流详情页 `https://www.runninghub.cn/post/<ID>`
3. 点击页面上的 **下载** 按钮
4. 浏览器自动保存 `<工作流名称>.json`

本质:该按钮前端调用 `POST /api/workflow/export`,所以手动下载和 API 下载结果完全一致。

## 3. 方式 B:export 接口下载文件(推荐,可批量)

### 3.1 请求

```
POST https://www.runninghub.cn/api/workflow/export
Body: {"workflowId": "<ID>"}
```

### 3.2 响应(实测)

```
HTTP 200
Content-Type: application/octet-stream
Content-Disposition: attachment; filename=YZ%E9%87%91%E9%B1%BC-...%E5%B7%A5%E4%BD%9C%E6%B5%81.json
Body: 工作流 JSON 文本(以 {\n\t"last_link_id":... 开头)
```

### 3.3 关键细节

- **成功判定**:看响应头 `Content-Disposition` 是否含 `attachment`,**不能**用 body 首字节判断——工作流 JSON 文件本身以 `{` 开头,和错误响应 `{"code":...}` 一样都是 `{`,只看首字节必踩坑(本次实测就因此误判过一次)
- **文件名**:`Content-Disposition` 里的 `filename*=UTF-8''<url编码>` 是工作流名(URL 编码),需 `unquote` 解码;个别旧接口可能用 `filename="xxx"`(不带编码),两种都要兼容
- **文件内容**:就是标准 ComfyUI 工作流 JSON(`last_node_id / nodes / links`),可直接导入 ComfyUI
- **需要登录**:未登录返回 `{"code":412,"msg":"TOKEN_INVALID"}`
- **加密/权限工作流**:若 `publishAccess.encrypted=true` 且无权访问,export 会失败(实测 320 个公开工作流全部成功,未遇加密失败)

### 3.4 文件名清洗(Windows)

服务端文件名可能含 `\/:*?"<>|` 等非法字符,保存前替换为 `_`;若目标已存在(重名),加 `<ID>_` 前缀:

```python
import re, os, requests

safe = re.sub(r'[\\/:*?"<>|]', '_', filename)
fp = os.path.join(OUT_DIR, safe)
if os.path.exists(fp):
    fp = os.path.join(OUT_DIR, f"{workflow_id}_{safe}")
```

## 4. 方式 C:getContent 接口获取内容字符串

不需要下载文件、只想拿 JSON 时用:

```
POST https://www.runninghub.cn/api/workflow/getContent
Body: {"workflowId": "<ID>"}
```

响应:

```json
{
  "code": 0,
  "data": {
    "id": "<ID>",
    "workflowName": "工作流名称",
    "workflowContent": "{...ComfyUI JSON 字符串...}",
    "userId": "...",
    "systemWorkflow": false,
    "draft": false,
    "saveFlag": 0
  }
}
```

`workflowContent` 是**字符串**,要 `json.loads()` 后再用;与 export 返回的文件内容一致(export 会多做一次转存)。

## 5. 方式 D:getDetail 接口获取元数据(详情)

```
POST https://www.runninghub.cn/api/workflow/getDetail
Body: {"workflowId": "<ID>"}
```

返回 `data` 关键字段(详见本文 §2 / §11):

| 字段 | 说明 |
|---|---|
| `nodeCount` | 节点总数 |
| `usedModels` | 所需模型文件名数组(可据此判断显存/下载哪些模型) |
| `customNodes` | 依赖的自定义节点数组(本地运行前要装) |
| `primitiveNodes` | ComfyUI 内置节点数组 |
| `publishAccess` | `granted` 是否可访问、`encrypted` 是否加密 |
| `statisticsInfo` | `likeCount/useCount/collectCount`(字符串) |

⚠️ 该接口的 `workflowContent` 字段恒为 `null` —— 详情 ≠ 内容,内容请用 §3/§4。

## 6. 批量获取下载地址/文件(本次 320 个实操流程)

### 6.1 总流程

```
1. 从 workflows-list.md 解析全部工作流 ID(正则提取 post/<ID>)
2. 并行调用 getDetail(6 线程)→ 元数据(节点/模型/自定义节点)
3. 并行调用 export(6 线程)→ 下载 JSON 文件到 webs\RunningHub\workflows\
4. 解析 Content-Disposition 拿文件名 → 清洗 → 保存
5. 把 详情列 + 下载地址(workflows/<文件名>)写回 workflows-list.md
```

### 6.2 实测统计(2026-08-03)

- 列表总行数:402(21 分类 × 20,AI漫剧 2 条)+ 官网精选 27
- 去重后唯一工作流:**320**
- 详情拉取:320/320 成功
- 文件下载:320/320 成功
- 总大小:约 28.1 MB(单文件 3.9 KB ~ 1.6 MB)
- 下载目录:`webs\RunningHub\workflows\`

### 6.3 并发要点

- 6 个并发线程实测稳定(太快会被风控/超时)
- export 单个请求最慢可达 1~2 分钟(服务端生成文件),超时设 120s
- 每次请求失败重试 3 次、间隔 2s

## 7. 常见失败与排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `412 TOKEN_INVALID` | token 缺失/过期 | 重新登录抓 token |
| `404 NOT_FOUND` | 路径错,或用了 GET | 确认 POST + 正确路径 |
| `301 PARAMS_INVALID` | 参数名错 | 必须是 `workflowId`,不是 id/postId/workId |
| export 返回 200 但内容像 JSON 错误 | 误把错误响应当文件 | 看 Content-Disposition 是否含 attachment |
| 保存后文件打不开 | 文件名含非法字符/未加 .json | 按 §3.4 清洗 |
| 某些工作流下载失败 | 加密/下架/权限 | 查 getDetail 的 `publishAccess` 与 `status` |

## 8. 完整 Python 脚本(实测可用)

```python
import sys, os, re, json, time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

TOKEN = "<你的 Bearer token>"          # 建议从环境变量读,别硬编码
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Authorization": "Bearer " + TOKEN,
    "Referer": "https://www.runninghub.cn/workflows",
    "Content-Type": "application/json",
}
BASE = "https://www.runninghub.cn"
OUT = r"webs\RunningHub\workflows"  # 下载目录
os.makedirs(OUT, exist_ok=True)

def post(path, body, timeout=120):
    for _ in range(3):
        try:
            return requests.post(BASE + path, json=body, headers=H, timeout=timeout)
        except Exception:
            time.sleep(2)
    raise RuntimeError("failed: " + path)

def clean_name(name, wid):
    if not name.lower().endswith(".json"):
        name += ".json"
    safe = re.sub(r'[\\/:*?"<>|]', "_", name)
    fp = os.path.join(OUT, safe)
    if os.path.exists(fp):
        fp = os.path.join(OUT, f"{wid}_{safe}")
    return fp

def fetch(wid):
    # 详情
    detail = None
    try:
        j = post("/api/workflow/getDetail", {"workflowId": wid}, timeout=40).json()
        detail = j.get("data") if j.get("code") == 0 else None
    except Exception:
        pass
    # 下载
    try:
        r = post("/api/workflow/export", {"workflowId": wid})
        cd = r.headers.get("Content-Disposition") or ""
        if r.status_code == 200 and "attachment" in cd and r.content:
            m = re.search(r"filename\*=UTF-8''([^;]+)|filename=\"?([^\";]+)", cd)
            raw = (m.group(1) or m.group(2) or "") if m else ""
            fname = requests.utils.unquote(raw) if raw else ""
            fp = clean_name(fname, wid)
            with open(fp, "wb") as f:
                f.write(r.content)
            return wid, detail, os.path.basename(fp), True, ""
        return wid, detail, None, False, cd[:80]
    except Exception as e:
        return wid, detail, None, False, str(e)[:100]

ids = ["<工作流ID1>", "<工作流ID2>"]   # 从 list.md 解析:re.findall(r'post/(\d{16,19})', text)
results = {}
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(fetch, w): w for w in ids}
    for fu in as_completed(futs):
        wid, detail, fname, ok, err = fu.result()
        results[wid] = {"detail": detail, "file": fname, "ok": ok, "err": err}

print("成功:", sum(1 for v in results.values() if v["ok"]), "/", len(ids))
```

## 9. 写入 workflows-list.md 的映射规则

每个工作流行新增两列:

| 列 | 内容 | 来源 |
|---|---|---|
| 详情 | `{节点数}节点/{模型数}模型/{自定义节点数}自定义节点` | getDetail:`nodeCount` / `len(usedModels)` / `len(customNodes)` |
| 下载地址 | `[下载](workflows/<文件名>.json)` 相对链接 | export 的 Content-Disposition 文件名 |

表头(分类区):

```
| 排名 | 工作流名称 | 点赞 | 使用 | 收藏 | 作者 | 发布日期 | 详情(节点/模型/自定义节点) | 下载地址 | 链接 |
```

## 10. 安全与规范

- token 是敏感凭据,不要写入任何 md、不要提交 git;脚本从环境变量读取
- `webs\RunningHub\` 目录不属于任何 git 仓库,下载文件可安全存放
- 下载的工作流可能使用 RunningHub 私有自定义节点(详情列有数量),导入本地 ComfyUI 前先装对应节点
- 批量调用注意频率(6 并发实测稳定),避免触发风控

## 12. 2026-10-10 实际下载(2831 → 4571 个工作流)

需求是「实际下载工作流」而非只拉列表,故本轮用一次性下载脚本(`pull-runninghub.py`,随根 `scripts\` 于 2026-10-11 移除)走完三段接口把 JSON 落到 `webs/RunningHub/workflows/<分类>/`。

### 12.1 本轮口径与结果

| 项 | 值 |
|---|---|
| 分类树 | `POST /api/portal/tag/tree` body `{"rang":"WORKFLOW"}` → 21 个一级分类 |
| 列表 | `POST /api/portal/template/list`,`size=30` / `sort=REPUTATION` / `days=90` / `tags=该分类全部子标签 id 数组` |
| 每类取样 | 按 `statisticsInfo.likeCount` 降序取**前 100 条**(旧脚本口径是前 20) |
| 内容 | `POST /api/workflow/getContent` body `{"workflowId": "<id>"}` → `data.workflowContent`(字符串化 JSON,`json.loads` 后直接落盘) |
| 本地规模 | 2831 → **4571** 个工作流,21 个分类,**新增 1740** |
| 站点规模 | 21 个分类 total 合计 **153866**(单类最高 `图片生成` 43653) |
| JSON 校验 | 4571 个全部可解析、均含 `nodes`,平均 43.2 节点;失败 1(分类 `二次元`,单条 getContent 返回空) |

### 12.2 本轮踩到的坑

1. ⚠️ **`tags` 必须传子标签 id 数组** —— 传一级分类 id 只返回少量官方模板(点赞全 0)。沿用 9.1 的结论。
2. ⚠️ **`data.total` 远大于本地目录规模是正常的** —— `total` 是该标签下的全站条目数,不是本次取样数;`AI漫剧` 类 total 只有 **2**、`插件` 161,这类小类取不满 100 条也属正常。
3. ⚠️ **`likeCount` / `useCount` / `collectCount` 在响应里是字符串**,排序前必须 `int()`。
4. ⚠️ **文件名必须清洗** —— 标题里带 `/ : * ? " < > |` 与控制字符(如 `+FLUX+动漫场景文生图+_+二次修复+.json`),直接当文件名在 Windows 上会失败;脚本统一替换为 `_`、截断到 120 字符、去掉尾部 `.` 与空格。
5. ⚠️ **同名文件会互相覆盖** —— 不同 id 可能同名。本轮对已存在的同名文件**跳过**(增量、不覆盖),故同名只保留首次落盘的那份。
6. 增量口径:本轮只下新增、不覆盖旧文件,所以「作者后来更新了工作流」这类变化**不会**被同步;要强制刷新需删目录重拉。

### 12.3 复跑方式

```powershell
$env:RH_TOKEN='<Bearer token>'
.\.venv\Scripts\python.exe -X utf8 scripts\pull-runninghub.py  # 脚本已于 2026-10-11 随根 scripts 目录移除
```

token 只经环境变量传入,**不落盘、不入 md、不提交 git**。

