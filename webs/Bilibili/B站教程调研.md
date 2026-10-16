# MiniMax H3 节点优化与模型加速专题(2026-08-05)

调研日期:2026-08-05(数据实时)。范围:B 站搜索「MiniMax H3 加速 / 优化 / 节点优化 / 显存优化 / SageAttention / 量化 / GGUF / EasyCache / 提速」相关视频;筛选标准:真教学(节点/插件/参数/部署实操、加速方案对比),剔除营销引流(一键三连领资料、私信口令、邀请码返利、机构培训广告、纯演示/对比/新闻)。判断依据:视频简介 + 评论区真实讨论(已抽样)。

## A. MiniMax H3 专属(节点优化与加速)

| 排名 | 视频 | 发布时间 | 播放 / 赞 / 藏 | UP 主 | 内容与判断 |
|------|------|------|------|------|------|
| 1 | [MiniMax H3 手搓开源加速新节点 BlockCache,唯一兼顾音频质量,又快又好!全类型模型,低显存,放大及加速选择方案最全对比](https://www.bilibili.com/video/BV1H9Mk61EbQ) | 2026-08-05 16:18 | 6248 / 256 / 264 | T8star-Aix | ✅ 25 分钟手搓开源加速节点 BlockCache,附全类型模型低显存与放大/加速方案最全对比;简介明确"AI 教学",工作流评论区自取,资源走夸克网盘,GitHub 开源(comfyui-minimax) |
| 2 | [【MiniMax-H3】最强加速插件推荐,硬核分析加速到底该怎么选!光流跳步 vs EasyCache vs 超级缓存](https://www.bilibili.com/video/BV13buc61E7r) | 2026-08-04 18:34 | 7177 / 249 / 384 | 机智罗_LX | ⚠️ 三种 H3 加速方案(光流跳步 Spectrum / EasyCache / 超级缓存)硬核对比与取舍,教学价值高;简介带交流群与包月充电群,有轻微引流 |
| 3 | [【保姆级安装教程】官方推荐的加速插件 SageAttention](https://www.bilibili.com/video/BV1u9uw67EPn) | 2026-08-04 22:34 | 4800 / 179 / 393 | SevnFading | ✅ 18:57 保姆级安装,简介直接附 ComfyUI 官方 MiniMax H3 手册链接(docs.comfy.org),无营销 |
| 4 | [开源视频王者降临 MiniMax-H3 全解,全功能案例,提速一倍以上,全提示词指令,九宫格/四视图,视频全能编辑](https://www.bilibili.com/video/BV1VNMr68EJK) | 2026-08-05 10:37 | 2414 / 119 / 202 | Time-AI | ✅ 26 分钟保姆级全解(提速+提示词指令+九宫格/四视图);模型与工作流走夸克网盘 |
| 5 | [MiniMax H3 本地上手实测,文生/图生/全能参考/480P VS 768P 全面对比,Sage Attention 加速实测](https://www.bilibili.com/video/BV1RiMq6QEG8) | 2026-08-05 03:13 | 1083 / 33 / 44 | Prompt娄 | ✅ 480P/768P 与 SageAttention 提速实测;评论区真实讨论(SG 节点安装、内存占用、参数取舍);学习资料夸克网盘 |
| 6 | [MiniMax H3 官方加速方案!SageAttention+EasyCache](https://www.bilibili.com/video/BV1LhMy6uE41) | 2026-08-05 20:40 | 218 / 9 / 12 | HyLan_L | ✅ 官方加速方案组合演示(9:26),模型/工作流走夸克+百度网盘;播放量尚小 |
| 7 | [MiniMax-H3 本地加速实测_RTX-PRO-6000-96GB](https://www.bilibili.com/video/BV1DjM16qEfb) | 2026-08-05 18:15 | 175 / 3 / 3 | 但丁jr | ✅ SageAttention 与 Spectrum 本地提速实测(96GB 卡),记录完整;评论区有参数询问与补充分享 |

## B. 通用模型加速优化(ComfyUI SageAttention/Triton/GGUF,H3 加速的前置)

| 排名 | 视频 | 发布时间 | 播放 / 赞 / 藏 | UP 主 | 内容与判断 |
|------|------|------|------|------|------|
| 1 | [ComfyUI+SageAttention 2.2 视频生成提速40%,终极 Windows 安装与实测教程](https://www.bilibili.com/video/BV1D9GLzyEMa) | 2026-07-08 09:37 | 23007 / 474 / 1002 | 有趣的80后程序员 | ✅ 19 分钟 Windows 安装+实测;评论区为纯技术排错(卸载命令、Triton 版本、环境变量、双 Python 装错),无营销 |
| 2 | [comfyui 桌面版,SageAttention 安装,sageattn2,视频加速](https://www.bilibili.com/video/BV1z39EYdELR) | 2026-03-04 13:54 | 13828 / 242 / 579 | HooTooH | ✅ 官方桌面版安装步骤,简介只给 GitHub 官方仓库链接,无广告 |
| 3 | [新版 ComfyUI 安装 triton 和 SageAttention 避坑](https://www.bilibili.com/video/BV1RBoBYSEfk) | 2026-03-23 21:01 | 11381 / 92 / 246 | 海洋蟹 | ✅ 避坑向;评论区真实报错互助(whl 版本、50 系冲突、便携包问题)并获感谢 |
| 4 | [小白该怎么安装 SageAttention](https://www.bilibili.com/video/BV12PZLYBE2a) | 2026-03-28 04:07 | 9914 / 152 / 324 | 智能绘图猿 | ✅ 21:57 保姆级,配腾讯文档补充资料;评论区全是安装求助与答疑 |
| 5 | [各版本 comfyui,便携版,整合包,官方桌面版,安装 triton 和 sageattention 的步骤](https://www.bilibili.com/video/BV1m4UxB6EVG) | 2025-11-23 01:03 | 4506 / 125 / 261 | 追风知识库 | ✅ 覆盖各版本安装步骤,简介直接给 pip 命令与版本对应表 |
| 6 | [【教程系列】如何快速 sage attention~](https://www.bilibili.com/video/BV1WdQFBiESe) | 2026-04-10 13:06 | 5373 / 93 / 141 | 胖胖的小老弟 | ✅ 快速安装系列教程(cuda/python/torch 版本核对) |
| 7 | [【ComfyUI】SageAttention & Triton 安装、报错,快速排查思路](https://www.bilibili.com/video/BV1N7CTBTEVF) | 2025-11-14 17:26 | 2211 / 27 / 74 | starky | ✅ 针对非官方包的报错排查思路,逐步讲解 |
| 8 | [【ComfyUI】2026 更新最新版教程｜CUDA13.0+PyTorch2.9+SageAttention2.2](https://www.bilibili.com/video/BV1L3KW6yEDf) | 2026-07-21 03:03 | 2027 / 72 / 100 | 晨序AI工坊 | ✅ 2026 新版环境(CUDA13/PyTorch2.9)对齐教程 |
| 9 | [【插件001】Sageattention+Triton 安装教程,便携包难题解决,保姆级安装教程](https://www.bilibili.com/video/BV1AJScBAENU) | 2025-11-30 01:56 | 1433 / 34 / 55 | 初阳AIAgent | ✅ 便携包场景保姆级安装,简介给官方 GitHub 链接 |
| 10 | [20系宝刀不老魔改 SageAttention2 加身 Wan2.2 视频生成速度提升30%](https://www.bilibili.com/video/BV1a4vsByEgd) | 2025-12-29 17:46 | 5185 / 130 / 304 | 恺悌智算 | ✅ Turing 架构老卡魔改 SageAttention2 提速(2080Ti 22G 实测) |
| 11 | [Win11 下 RDNA4 显卡 SageAttention2.2 编译指南](https://www.bilibili.com/video/BV1MfNF6hE7y) | 2026-07-11 20:29 | 888 / 34 / 28 | jokon0408 | ✅ AMD/ROCm 编译指南;评论区反馈"轮子可以用",技术讨论真实 |
| 12 | [没有轮子,我们就自己造!用 Trae 编译 ComfyUI 加速器 SageAttention,老显卡狂飙30%](https://www.bilibili.com/video/BV138N5zoEYu) | 2026-03-09 07:30 | 508 / 21 / 22 | 一点风雨生 | ✅ 无现成轮子时自编译思路;评论区点赞与真实技术交流 |
| 13 | [ComfyUI,安装 GGUF 扩展和 sageattention 和 triton,图片转视频](https://www.bilibili.com/video/BV1j6wBz4Etb) | 2026-03-18 23:27 | 1960 / 25 / 55 | Tin168 | ✅ GGUF 扩展+加速模块安装(需一定动手能力),无广告 |

## 已剔除(营销/引流/非教学)

- **机构/培训广告**:大凯智障君「告别龟速!SageAttention 拯救 MiniMax H3…」(BV1FRM66TEk6,简介为工作室承接定制+人社部证书培训考试广告,技术内容被广告淹没)
- **云平台邀请码返利**:梦影Erislia「…社区最强加速组合(SageAttention+H3 Cache)」(BV1fAM16jET2,Compshare 一键部署+referral_code)、Booday不带「…极限加速全攻略」(BV1WBZJB3E9F,RH 注册送积分邀请码)
- **一键三连/资料引导**:FaboroHacks「Seedance 危矣!MiniMax H3 开源免费版解压即用」(BV1zFMR6gEPV,三连+夸克网盘)、wangyi_AI_Studio「…秋叶视频整合包…」(BV1rrJJzREnH,三连后截图后台领取)、小猪AI-Q「2026最新秋叶整合包V3…」(BV1wkzVBzENu,夸克+RH 邀请码)、T8star-Aix「Ai绘画进阶204…SageAttention 2.2」(BV1F13ozuEWr,私信回复口令自动发送+云端工作台邀请码)
- **整合包分发(非教学)**:豹豹喵呜「七月最新整合包…」(BV1Q3M86dEvM)、雨落实战「AI视频 MiniMax-H3 整合包加速版…」(搜索可见)
- **公众号引流**:擂玩AI「comfyUI报错处理:triton、sageattention」(BV127UMBXE2Q,简介导流微信公众号)
- **新闻/口号/论文解读**:钓鱼不得使用路亚「…SageAttention5.0…即将开源…」(BV1spxXzzEw1)、减论「清华推出SageAttention2…arXiv」(BV137UfYjEsu)
- **疑似假冒/搬运**:秋葉comfyui教程「MiniMax H3 手搓…BlockCache…」(与 T8star 同内容,播放仅 6,疑似搬运或假冒秋叶)
- **待确认**:令狐超kira「12倍加速!MiniMax H3 生成新玩法(别再渲染原生1080p了)」搜索可见(08-05,1177 播放),但详情接口取不回(疑似删除/私密),未收录;该视频曾被观众在其它视频评论区推荐,恢复后可再看

## 说明

H3 于 2026-08-02/03 开源,当前"节点优化/加速"生态刚起步:最硬核的是 T8star 手搓 BlockCache 与机智罗_LX 的方案对比;SageAttention 是官方推荐加速方案,大量安装教程集中在通用 ComfyUI 区(B 组),先装好 SageAttention/Triton 再谈 H3 提速。数据为 2026-08-05 实时抓取,播放/赞/藏随发布增长会变化。


---

## 更新(2026-08-06):MiniMax H3 最新加速方案与 LoRA 加速

调研日期:2026-08-06(数据实时)。范围:全 B 站搜索「MiniMax H3 加速 / LoRA / 蒸馏 / 缓存 / BlockCache / 4步 / 优化 最新」;筛选:真教学(插件/参数/方案实操),剔除营销引流(整合包三连私信、邀请码返利、软件站引流、公众号)。重点核实:当前是否有"H3 LoRA 加速"专项教学。

### 新增收录(按播放量)

| 排名 | 视频 | 发布时间 | 播放 / 赞 / 藏 | UP 主 | 内容与判断 |
|------|------|------|------|------|------|
| 1 | [Minimax-H3的5倍加速且超强画质方案???其实只是一个小技巧](https://www.bilibili.com/video/BV1zMMf6nEYM) | 2026-08-04 06:48 | 17745 / 396 / 847 | 狮子都是孤军奋战 | ✅ 低分辨率生成 + Bernini 放大的"5 倍加速"技巧;评论区真实讨论(4090 实测时间、Bernini OOM、先 480 再放大思路) |
| 2 | [MiniMax H3 本地生成提速60%+!ComfyUI超级加速插件实测](https://www.bilibili.com/video/BV19Juc6DE8k) | 2026-08-04 17:28 | 6784 / 227 / 396 | Mr_陌客 | ✅ HyperStep 加速插件实测(开源 GitHub:biyuhe3442-cmd/ComfyUI-NB-H3-HyperStep,中间层残差复用/跳 34-36 块),推荐链:H3 Loader→SageAttention→HyperStep→Sampler;夸克网盘备链 ⚠️ 注:该插件已在本机移除(2026-08-10,兼容性弃用) |
| 3 | [Minimax H3本地部署福音!低显存及二采加速优化!](https://www.bilibili.com/video/BV1tDMq6GE65) | 2026-08-05 01:25 | 6147 / 285 / 453 | wuwukasi | ✅ 低显存部署 + 二采加速优化,13 分钟讲解;资源走夸克网盘 |
| 4 | [海螺H3 究极多重加速方案 比原版快70% 低配置通杀!](https://www.bilibili.com/video/BV1nkM16DEBC) | 2026-08-06 02:16 | 4269 / 112 / 365 | 阿硕讲ai | ✅ 今日最新,多重加速组合(SHUO-Canvas GitHub);评论区真实讨论(加速会削弱提示词响应、50 系兼容、用什么卡测的) |
| 5 | [Minimax-H3的5倍加速且超强画质方案(+Bernini 1.3B二采)](https://www.bilibili.com/video/BV1GhMk6hEdF) | 2026-08-05 16:51 | 2060 / 72 / 94 | 郭吉军插件汉化 | ⚠️ Bernini 1.3B 二采加速方案,节点开源(ComfyUI_GJJ_Nodes),评论区真实反馈(节点缺失、低显存卸载问题);模型走夸克网盘,资源分发性质偏重 |
| 6 | [海螺H3工作流 加速节点 提示词增强节点-多图参考-首尾帧-视频编辑-强动态-高一致性](https://www.bilibili.com/video/BV1jWMk6KEUJ) | 2026-08-05 16:22 | 423 / 9 / 25 | Mc丶师兄 | ✅ 加速节点 + 完整工作流讲解(11:54);评论区真实讨论(参考视频爆显存、首尾帧禁用图片);资源走夸克网盘,播放量尚小 |

### LoRA 加速专项结论

- 截至 2026-08-06,B 站尚无直接命名"H3 LoRA 加速"的教学视频;H3 加速主流方案是:HyperStep(中间层残差复用/跳块,类似蒸馏)、SageAttention、EasyCache / BlockCache / 超级缓存、Bernini 1.3B 二采、多重方案组合。
- H3 的 LoRA 生态目前以"训练工具"为主(如"LoRA训练天使"中文训练工具、AI Toolkit 支持 H3 训练),但均带软件站/邀请码引流,按本表规则剔除;待出现"H3 加速 LoRA"教学后补录。

### 已剔除(营销/引流)

- **整合包三连+私信获取**:comfyui秋葉(BV1VNuP6ZEXh)、AI原画(BV1dAMC6BEmg)、秋叶SD安装包(BV1imMC6BEVd)、comfyui零基础课程(BV1BEMk6zEbs)、刘悦的技术博客(BV1S9uw6jE66、BV1CVMy6DEK1)、雨落实战(BV1FHMy6jEgy)、htc911(BV1KmMy6tEUD)
- **云端/邀请码返利**:Work-Fisher(BV12kuA6CE7m,RH 邀请码)、梦影Erislia(BV1fAM16jET2,Compshare referral)、惊尘丶573(BV1E9MB6FEqM,RH 邀请码)、小猪AI-Q(BV1zGuc6xEKZ,RH+夸克)、炮老师的小课堂(BV1sruc6iEh7,RH 邀请码)、Doc_workBox(BV181Mq61EGw,RH 邀请码)
- **软件站/关注私信引流**:LoRA训练天使(BV1ipuA64ETN、BV13kM26zEbL,自研工具站)、万能君的软件库(BV1yyuA6GEtA)、Penpos(BV1hZM16zEvo)、1PluS6(BV1khMX63EFQ)、杠精强哥(BV1mtM16FE3n,三连私领取)、程序员萝卜(BV1zBMC6yEq5,公众号引流)
- **非 H3(排除)**:青龙圣者 Lora 训练(SD 系)、CG迷李辰 Qwen 加速 LoRA(BV1YXYszfEH4)、张sir的AI 加速 lora/AuraFlow(BV1PjSYBsE8K)、Zove-try Anima 加速(BV1AzdzBxE7A)、郭吉军 Bernini LoRA(BV1C4MT6jE5L)、多少会点不精 Z-image turbo LoRA(BV1wn3g6fEPB)
- **待确认**:令狐超kira「12倍加速!MiniMax H3 生成新玩法」搜索可见(BV1TiM66JEJZ),详情接口仍取不回(疑似删除/私密),持续未收录


### MiniMax H3 加速模型确认与下载地址(2026-08-06)

来源:单搜索词「HyperStep / bernini / H3加速 / H3 LoRA」全 B 站复核,命中 [4步加速lora来了!MiniMax H3迎来超级加速,comfyui可用(BV1XWMS6EEVK)](https://www.bilibili.com/video/BV1XWMS6EEVK)(AIEveryThing,2026-08-06)。

**加速模型:MiniMax-H3-Turbo-Lora**(4 步加速 LoRA,由 larryvrh 发布在 HuggingFace;B 站 UP 主说明 LoRA 非其训练,只是做了 ComfyUI 可用转换,原版 ComfyUI 直接用不了)。

| 项目 | 地址 |
|------|------|
| HF 原仓库(下载入口,需代理访问) | https://huggingface.co/larryvrh/MiniMax-H3-Turbo-Lora |
| 转换版(ComfyUI 可用,夸克网盘) | https://pan.quark.cn/s/0fcb105f2a64 |
| 官方 H3 底模(魔搭镜像,国内直连) | https://www.modelscope.cn/models/Comfy-Org/MiniMax-H3/files |

配套要求(视频简介):ComfyUI v0.30.0+、KJNodes、ComfyUI-ReservedVRAM、SageAttention、`pip install triton-windows`。

**HF 仓库文件(已在线验证,均为 bf16,各约 744 MB,直链 302 有效):**

| 文件 | 说明 | 直链 |
|------|------|------|
| minimax_h3_turbo_4step.safetensors | 训练权重,快速运动下更清晰(推荐) | https://huggingface.co/larryvrh/MiniMax-H3-Turbo-Lora/resolve/main/minimax_h3_turbo_4step.safetensors |
| minimax_h3_turbo_4step_ema.safetensors | 时间平均权重,更平滑但当前检查点未成熟 | https://huggingface.co/larryvrh/MiniMax-H3-Turbo-Lora/resolve/main/minimax_h3_turbo_4step_ema.safetensors |

> 验证状态(2026-08-06,7890 代理已恢复,HuggingFace 在线确认):仓库 `larryvrh/MiniMax-H3-Turbo-Lora` 存在,Apache-2.0,base_model=`Comfy-Org/MiniMax-H3`,41 likes,2026-08-05 创建。README 明确这是**早期预览(demo/preview,欠训练,EMA 未成熟)**,4 步采样约为常规 20 步的 **5 倍提速**(设计点 4 步,预算充足建议 8 步);**原版暂不支持 ComfyUI(README 原文:No comfyui support yet, will add later)**,ComfyUI 使用需 B 站 UP 的夸克转换版;权重为 bf16 标准 LoRA(应用方式 `W_eff = W + lora_B @ lora_A`,alpha=rank)。

其他加速方案线索:Sol-Attn MiniMax H3 Patcher(BV1z6MC6VEmB,注意力加速补丁);GitHub 全栈加速指南 [juemin4-source/minimax-h3-guide](https://github.com/juemin4-source/minimax-h3-guide)(CUDA13 升级,RTX 4070 Ti 12G 实测 6-8 倍提速,附工作流与 H3RefLoader 插件)。


---

## 更新(2026-10-16):MiniMax H3 **高阶使用技巧**专题 → 见 `MiniMax-H3-高阶使用技巧-教程调研-2026-10-16.md`

本文件前面几期(H3 加速、节点优化)已完成其阶段使命:**H3 生态的重心已从「能不能跑 / 跑多快」转向「怎么跑好」**。本期改换选题口径,专做**高阶使用技巧**——长视频上下文续接、二采/三采放大与去塑料感、视频编辑与角色替换、提示词工程(口型/字幕/画外音/时序)、运镜控制、一致性资产(RefMod/四视图)、加速与显存方案、高动态动作迁移、工作流编排。

**检索规模**:48 个关键词,去重后命中 1376 个视频,过滤同名非 H3 条目(耳机/PLC/玩具枪/背包等)后约 600 个 H3 相关,按播放量逐条抓取前 460 个的详情 + 评论 + UP 主粉丝数(API 实时)。

**最值得看的十期(全部无邀请码/无三连门槛)**:

| 主题 | 视频 | 看点 |
|------|------|------|
| 长视频 · 原理 | [BV1Wsgg6AEeR](https://www.bilibili.com/video/BV1Wsgg6AEeR) | Motion Context 完整数据流:缓存上段末尾 1s 音画 latent → 与新 latent 并联 → 裁重叠拼接 |
| 长视频 · 抗劣化 | [BV12i8Q6vEFP](https://www.bilibili.com/video/BV12i8Q6vEFP) | **官方原生 Add Guide 节点 + 参考帧注噪**,免第三方插件实现真正无限续接 |
| 长视频 · 无色差 | [BV11kHs6NEef](https://www.bilibili.com/video/BV11kHs6NEef) | 新 latent 放大模型 + VAE 提速;评论区有「参考视频质量决定续段质量」等实测 |
| 二采 · 原理 | [BV1whbN6bEtt](https://www.bilibili.com/video/BV1whbN6bEtt) | 一采定框架 / 二采修细节;点破「文系武系只是不同动态 LoRA」;附 sigma 分段方案对照 |
| 二采 · 取舍 | [BV1hupu6qEUX](https://www.bilibili.com/video/BV1hupu6qEUX) | 评论区关键结论:**SelfLift 这类分离 sigma 的二采反而降质**,完整两次采样才更好 |
| 放大 · 显存 | [BV1CybV6DEiA](https://www.bilibili.com/video/BV1CybV6DEiA) | 分块放大 2K/4K;**评论区比视频更值钱**(分离模型省 10G 显存、Sage+Sol 稀疏注意力组合) |
| 编辑 | [BV1v24f6FEuH](https://www.bilibili.com/video/BV1v24f6FEuH) | Ref2VA 整段重构 + **官方六段式提示词公式**拆解 + 参考视频帧率尺寸对齐痛点 |
| 一致性 | [BV1NjWw6CEvD](https://www.bilibili.com/video/BV1NjWw6CEvD) | **RefMod 零训练演员库**:8 张照片封装成 LoRA 式资产,含 tokens 与节点配置 |
| 提示词 | [BV1Lre16rEM1](https://www.bilibili.com/video/BV1Lre16rEM1) | 乱说话(鸟语)/ 画外音 / 内心独白的正确写法 |
| 运镜 | [BV1uuHy6hEfe](https://www.bilibili.com/video/BV1uuHy6hEfe) | **114 条运镜对照测试**(收藏率 0.166 为本专题最高),回答「还需要运镜 LoRA 吗」 |

**三条影响本机工作流的结论**:
1. B 站主流「加速」走的是 Spark-H3 / BlockCache / SelfLift / TaoMate-H3 / DMAD 蒸馏等**非 lightx2v Turbo LoRA** 路线 ⇒ 与本机 `AGENTS.md` 的 shift 配对表无关,换用不需改 `MiniMaxH3SigmaShift`,但要独立复验质量。
2. 「H3 原生运镜够强,未必需要运镜 LoRA」与「SelfLift 式分离 sigma 二采反降质」直接影响本机 H3 的**采样结构选型**。
3. 语义桥(Semantic Bridge)是官方六段式提示词的上游增强,可作为本机 `h3-prompt-writing` 技能的补充手段。

完整清单(含分组表格、逐条引流标注、22 条配套开源项目索引、观看顺序建议)见
[`MiniMax-H3-高阶使用技巧-教程调研-2026-10-16.md`](MiniMax-H3-高阶使用技巧-教程调研-2026-10-16.md)。
