# 双机同步:Syncthing 实时文件同步 + Git 代码同步(2026-08-19)

本地 Windows(`D:\AI\Comfy-S`)与 AutoDL GPU 服务器(`/root/Comfy`)之间的整套同步方案:
**Syncthing** 负责 `media / workflows / stories\七纹刻印` 三个目录的实时双向文件同步,
**Git** 负责 Comfy 代码(根仓库文件 + 子模块指针)的提交级同步。冲突策略统一为
"谁最后修改谁赢"。

> **2026-08-20 换实例注记**: 服务器已换新实例 `connect.westd.seetacloud.com:16362`(旧
> `bjb1:40871` / `bjb2:41215` 均已失效,RTX 5090 D 32GB / 754GB 内存)。沿用状态:Syncthing
> 配置与设备 ID 未变(三个双向文件夹直接可用)、`/root/Comfy` 为同一 GitHub 仓库
> (`receive.denyCurrentBranch=updateInstead` 已设、本地公钥已在新实例 authorized_keys)、
> `/etc/autodl.sh` 自启钩子在位;新实例**无**旧实例的 `/root/AGENTS.md` 运维手册。
> 下文 `server` remote 地址已更新为新实例。

## 1. 背景与选型

需求:两端 ComfyUI 工作区实时互通,文件按最后修改者同步给对方。

### 1.1 走过的弯路:SSHFS 挂载(已放弃)

曾尝试 WinFsp + SSHFS-Win 把服务器 `/root/Shares` 挂载到本地 `D:\Shares`,踩到两个
无法绕过的限制后彻底卸载:

- Windows OpenSSH 9.5p2 默认 `sock` stdio 模式与 sshfs 不兼容(报 `Connection reset
  by peer`),必须用 SSHFS-Win 自带的 Cygwin ssh(把其 bin 目录放 PATH 最前)或设
  `OPENSSH_STDIO_MODE=nonsock`;
- **FUSE 根本限制:符号链接目标指向挂载点之外(无论绝对路径还是 `..` 相对路径)一律
  报 File Not Found**——FUSE 把链接目标解析限制在挂载命名空间内,无法修复。服务器
  `/root/Shares` 的三个软链接(指向 `/root/Comfy/...`)正是这种场景,挂载方案不成立。

WinFsp/SSHFS-Win、服务、驱动、PATH、临时文件均已清理干净。

### 1.2 候选方案对比(2026-08 调研)

| 方案 | 双向 | 实时 | 冲突策略 | 结论 |
|------|------|------|----------|------|
| **Syncthing** v2.1.3 | ✓ | ✓(文件监听,秒级) | **默认=最后修改者胜**(较新版本保留,旧版本改名 `.sync-conflict-<日期>-<时间>-<设备>` 保留不删) | **采用** |
| Mutagen v0.18.1 | ✓ | ✓ | 正常单侧修改自动同步;真同时冲突需手动处理(旧版 `prefer-newest` 自动策略已移除);`two-way-resolved` 是固定一端赢 | 次选:纯 CLI 无 GUI,真冲突不自动 |
| Unison | ✓ | ✗ 轮询 | 保守(两边留 `.unison` 文件) | 排除 |
| rclone bisync | ✓ | ✗ 定时批量 | 弱 | 排除 |
| FreeFileSync | ✓ | ✗ 手动/计划 | 可选保留最新 | 排除 |
| rsync / lsyncd | 单向 | inotify 实时 | — | 排除 |

Syncthing 决定性优势:**默认冲突处理就是"谁最后修改谁赢"**(官方文档
[syncing - Conflicting Changes](https://docs.syncthing.net/users/syncing.html):
修改时间较旧的一方被改名为冲突文件,较新的保留),且走全球 relay 时**服务器无需开
任何入站端口**。

## 2. Syncthing 部署现状

版本 v2.1.3(两端一致)。连接走 Syncthing 全球 relay(如 `47.116.119.148:22067`),
无需开端口;若将来 media 大文件同步嫌慢,可在 AutoDL 控制台映射端口实现直连提速。

### 2.1 Windows 端(当前用户运行)

- 程序:`C:\Program Files\Syncthing\syncthing.exe`(便携 zip 安装;v2.1.3 起官方不再
  提供 MSI,便携 zip + 脚本/服务管理器是官方推荐方式)
- 启动:**项目根 `sync-server.cmd`**(与 `comfy-server.cmd` 同款三步:杀旧实例 →
  PowerShell 无窗口后台拉起 → 等 8384 端口就绪,120s 超时打日志尾部);
  日志 `%TEMP%\syncthing-server-8384.log`。开机自启用法同 comfy-server.cmd(快捷方式
  放 `shell:startup`)
- 配置:%LOCALAPPDATA%\Syncthing(即 `C:\Users\<用户>\AppData\Local\Syncthing`),
  设备 ID `LR3GWQM-XCWDQVR-WCHZCEA-LBABNZX-DUKX4L2-DV6ZHT5-OH5237A-7LCRAAZ`
- GUI:`http://127.0.0.1:8384`(无鉴权,可直接看状态/改设置)
- 历史注:曾用 nssm 注册服务(以 LocalSystem 运行,配置跑到 systemprofile 目录),
  后按用户要求删除服务、改为 sync-server.cmd 用户态运行,配置已迁回用户默认位置

### 2.2 服务器端(SysV 服务,AutoDL 容器)

AutoDL 容器无 systemd(PID 1 是平台 boot 脚本),服务规范见旧实例 `/root/AGENTS.md`
(SysV LSB init 脚本 + `/etc/autodl.sh` 开机钩子,规范副本存 `/root` 防 `/etc` 重置;
2026-08-20 新实例无此文件,但 `/etc/autodl.sh` 与 `/root/.harness` 在位)。

- 程序:`/usr/local/bin/syncthing`(官方 linux-amd64 二进制)
- 服务:`/etc/init.d/syncthing`,规范副本 `/root/.syncthing/init.d/syncthing`;开机由
  `/etc/autodl.sh` 重装并启动(顺序 harness → qwen → comfy → **syncthing**)
- 管理:`service syncthing start|stop|status|restart`;pidfile `/var/run/syncthing.pid`,
  日志 `/var/log/syncthing.log`
- 配置:`/root/.local/state/syncthing`(**新版默认 XDG state 目录,不是 `.config`**),
  设备 ID `ZKHCVRP-5P443UX-BXX6FL2-DQB4ATA-27LV5YN-DCMGPSA-V26QCNP-TDAIYAJ`
- init 脚本关键点(照抄本机 comfy 脚本模式):
  - `start-stop-daemon --background --make-pidfile` 守护;`start` 前 / `stop` 后各跑
    一次 `port_pids()/kill_port()`(端口 22000,扫 `/proc/net/tcp{,6}` +
    `/proc/*/fd`,容器内无 ss/fuser),自动收编服务外启动的残留实例
  - `serve --no-restart` → monitor+worker 双进程,pidfile 记 monitor(进程组组长),
    stop 整组 TERM

### 2.3 同步文件夹(两端一致,均为 sendreceive 双向)

| 文件夹 ID | 本地路径 | 服务器路径 |
|-----------|----------|------------|
| `media` | `D:\AI\Comfy-S\media` | `/root/Comfy/media` |
| `workflows` | `D:\AI\Comfy-S\workflows` | `/root/Comfy/workflows` |
| `stories-qwx` | `D:\AI\Comfy-S\stories\七纹刻印` | `/root/Comfy/stories/七纹刻印` |

首跑即完成全量同步,并自动创建了服务器上原本不存在的 `stories/七纹刻印`
(顺带解决了服务器端 `/root/Shares` 悬空软链接的问题)。

### 2.4 已踩过的坑(部署时真实遇到)

1. **REST API 建文件夹 `devices[]` 必须同时列本地+对端设备 ID**——只写对端时两端都
   显示 100%/idle 但文件根本不传(最隐蔽的一个,实测排查)。
2. **`start-stop-daemon` 剥光环境变量**:不 `export HOME=/root` 则 syncthing 启动
   panic `Failed to get user home dir`;系统时区 UTC 而 shell 是 CST,再 `export
   TZ=Asia/Shanghai` 对齐日志时间。
3. Windows 侧 v2.1.3 无 MSI;LocalSystem 服务账户的 `%LOCALAPPDATA%` 是
   `systemprofile` 目录(配置会跑到那里,删服务时别漏)。
4. 服务器容器无 systemd/cron,早期用 `.bashrc` 钩子临时自启,后按 AGENTS.md 规范改为
   正式 SysV 服务(钩子已删)。
5. 验证手法:两端各建/删测试文件互相同步,再查 `/rest/db/status?folder=<id>` 的
   state/need/errors。

## 3. Git 代码同步(本机 ↔ 服务器)

### 3.1 拓扑

- 两端都是 GitHub 仓库 `git@github.com:falling-ts/Comfy-S.git` 的克隆(分支 `main`),
  互为备份与中转;日常直连不走 GitHub
- 直连通道:本地 → 服务器 SSH(`connect.westd.seetacloud.com:16362`,root 用户,2026-08-20 换实例)
  - 本地 `~/.ssh/id_rsa` 公钥已加入服务器 `/root/.ssh/authorized_keys`
  - 服务器自带密钥 `id_rsa` + `~/.ssh/config` 中 github.com 走 Clash 代理
    (`ProxyCommand /usr/bin/connect -H 127.0.0.1:7890 %h %p`),供服务器直连 GitHub
- 本地 remote:
  - `origin` = `git@github.com:falling-ts/Comfy-S.git`
  - `server` = `ssh://root@connect.westd.seetacloud.com:16362/root/Comfy` ← 直连服务器
- 服务器仓库已设 `receive.denyCurrentBranch=updateInstead`:本地 push 会自动更新
  服务器工作树(若服务器工作树对将更新的文件有本地修改,push 会被安全拒绝,不会静默
  覆盖)

### 3.2 日常操作

**本地改代码(主路径):**

```bash
git add . && git commit -m "..."
git push server main      # 直连推给服务器,服务器工作树自动更新
# 可选:同步 GitHub
git push origin main
```

**服务器上有新提交(如服务器侧脚本改动):**

```bash
# 在本地执行(跨机操作一律从本地发起,服务器在 NAT 后无法主动连本地)
git fetch server && git merge server/main   # 或 git pull server main
```

**两端同时改了同一个文件:** Syncthing 已先把"最后修改的内容"同步到两端工作树,
先 commit 的一方 push 时,另一方若工作树脏会被 `updateInstead` 拒绝——先把对方改动
提交(或 stash),再推即可,内容以最后修改者为准,与文件同步策略一致。

### 3.3 分工与边界

| 机制 | 覆盖范围 | 特性 |
|------|----------|------|
| Syncthing | `media/`、`workflows/`、`stories/七纹刻印/` 文件内容 | 实时、双向、最后修改者胜、大文件增量 |
| Git | 根仓库全部跟踪文件 + 子模块指针(ComfyUI 主程序/43 插件/h3 等) | 提交级、带历史、可追溯 |
| 不同步 | `models/`(各槽位 `.gitignore` 忽略,约 189GB,走 AutoDL 云盘/按需下载) | — |

- `workflows/`、`stories/七纹刻印/` 两套机制叠加:Syncthing 保内容实时一致,Git 保
  提交历史;二者收敛方向相同(最后修改者),无冲突风险
- `.stfolder/` 是 Syncthing 文件夹标记目录,已加入 `.gitignore`
- **子模块指针谨慎推**:服务器 `ComfyUI` 是运行中服务(conda env comfy),推指针更新
  会在服务器切出对应版本,需确认两端环境都支持后再推

## 4. 运维速查

| 操作 | 命令/位置 |
|------|-----------|
| 本地起 Syncthing | 双击/执行 `sync-server.cmd`(或 `shell:startup` 自启) |
| 服务器 Syncthing | `service syncthing start\|stop\|status\|restart`;日志 `/var/log/syncthing.log` |
| 本地 GUI | `http://127.0.0.1:8384` |
| 服务器 GUI | 需 SSH 隧道到服务器 `127.0.0.1:8384`(如 dsh-ssh `ssh_tunnel`) |
| 两端直推 | 本地 `git push server main`;服务器侧提交后本地 `git fetch server && git merge server/main` |
| 排查同步 | 两端 `curl -H "X-API-Key: <key>" http://127.0.0.1:8384/rest/db/status?folder=<id>`(key 在各自 config.xml) |
| 冲突文件 | 找 `.sync-conflict-*` 改名文件,人工比对后删除旧版 |

## 5. 实施记录(2026-08-19)

1. 调研选型 → 定 Syncthing;Windows 便携版 + 服务器二进制安装,REST API 配 3 对双向
   文件夹,踩坑 devices[] 双 ID 后打通,双向创建/修改/删除实测通过
2. Windows 端按用户要求弃用 nssm 服务,改 `sync-server.cmd`(项目根,同 comfy-server.cmd
   模式),配置迁回用户默认位置
3. 服务器端按 `/root/AGENTS.md` 规范装为 SysV 服务 + `/etc/autodl.sh` 开机自启,修掉
   HOME/TZ 两个环境坑;服务器 AGENTS.md 已登记该服务
4. Git 直连:本地公钥入服务器 authorized_keys,本地加 `server` remote,
   `receive.denyCurrentBranch=updateInstead`;服务器领先 commit a0698af
   (comfy-server.sh 适配 AutoDL)已 ff 合并到本地
5. `.stfolder/` 加入 `.gitignore`
