#!/usr/bin/env bash
# comfy-server.sh — ComfyUI 统一后台启动脚本(跨平台: Linux + Windows Git Bash)
#
# 取代原 comfy-server.cmd(Windows) 与 comfy-server.sh(Linux/AutoDL),
# 参照 harness-server.sh 风格, 三步: 停旧服务 → 后台启动 → 等待端口就绪。
#
# 用法:
#   bash comfy-server.sh                   # 默认端口 8188
#   PORT=8189 bash comfy-server.sh         # 自定义端口
#   WAIT=300 bash comfy-server.sh          # 加长启动等待
#   PY_BIN=... bash comfy-server.sh        # 自定义 Python 解释器
#   LOG=... bash comfy-server.sh           # 自定义日志路径
#
# 平台自适应:
#   - Windows (Git Bash): 解释器默认 .venv/Scripts/python.exe,
#     参数 --enable-manager --disable-pinned-memory(本地 RTX 4060 8GB)
#   - Linux: 解释器默认 .venv/bin/python, 缺失时回退 conda 环境 comfy
#     (/root/miniconda3/envs/comfy/bin/python, ai-server 实例),
#     参数 --enable-manager --fast-disk --reserve-vram $RESERVE_VRAM(默认 22,
#     ai-server 上 llama.cpp 占 ~22GB 显存, 留给 ComfyUI 余量; RESERVE_VRAM=0 则不带该参数),
#     有 setsid 时 detach 会话(SSH 断开后存活)
#   - 日志默认写**调用时所在目录** comfy-server-<port>.log(两平台一致, 同 harness-server.sh)
#   - 停旧服务: Windows 用 netstat + taskkill; Linux 用 fuser, 缺失时回退解析 /proc/net/tcp
#
# 说明: 就绪检测用 bash 内建 /dev/tcp 探测端口(两平台均可用),
# 端口监听即视为就绪; 如需等 API 完全可用, 可自行 curl /system_stats 轮询。
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${PORT:-8188}"
WAIT_SECS="${WAIT:-120}"
COMFY_DIR="$ROOT/ComfyUI"
LOG="${LOG:-$(pwd)/comfy-server-${PORT}.log}"   # 日志写调用时所在目录

IS_WINDOWS=0
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) IS_WINDOWS=1 ;;
esac

if [ "$IS_WINDOWS" -eq 1 ]; then
  PY_BIN="${PY_BIN:-$ROOT/.venv/Scripts/python.exe}"
  ARGS=(--enable-manager --disable-pinned-memory --port "$PORT")
else
  PY_BIN="${PY_BIN:-$ROOT/.venv/bin/python}"
  [ -x "$PY_BIN" ] || PY_BIN="/root/miniconda3/envs/comfy/bin/python"
  RESERVE_VRAM="${RESERVE_VRAM:-22}"
  ARGS=(--enable-manager --fast-disk --port "$PORT")
  [ "$RESERVE_VRAM" = "0" ] || ARGS+=(--reserve-vram "$RESERVE_VRAM")
fi

# [1/3] 停掉占用端口的旧服务
kill_port() {
  if [ "$IS_WINDOWS" -eq 1 ]; then
    local PIDS PID
    PIDS="$(netstat -ano 2>/dev/null | tr -d '\r' | grep -E "[:.]${PORT}[[:space:]]" | grep -iE 'LISTEN' | awk '{print $NF}' | sed 's/\/.*//' | sort -u)"
    if [ -n "$PIDS" ]; then
      for PID in $PIDS; do
        MSYS_NO_PATHCONV=1 taskkill /F /T /PID "$PID" >/dev/null 2>&1 || true
      done
      sleep 1
    else
      echo "      (none found)"
    fi
    return
  fi
  # Linux: fuser 优先; 容器里可能没有, 退回 /proc/net/tcp{,6} 解析 inode → pid
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "$PORT/tcp" >/dev/null 2>&1 || true
    sleep 1
    return
  fi
  local port_hex inodes fd pid i
  port_hex=$(printf '%04X' "$PORT")
  inodes="$(awk -v p=":$port_hex" 'substr($2, length($2)-length(p)+1) == p && $4 == "0A" {print $10}' /proc/net/tcp /proc/net/tcp6 2>/dev/null | sort -u)"
  for inode in $inodes; do
    for fd in /proc/[0-9]*/fd/*; do
      [ "$(readlink "$fd" 2>/dev/null)" = "socket:[$inode]" ] || continue
      pid="${fd#/proc/}"; pid="${pid%%/*}"
      kill "$pid" 2>/dev/null || true
    done
  done
  # 等端口释放; 10 秒后仍在则强杀(有些进程挂起不响应 TERM)
  for i in $(seq 1 10); do
    inodes="$(awk -v p=":$port_hex" 'substr($2, length($2)-length(p)+1) == p && $4 == "0A" {print $10}' /proc/net/tcp /proc/net/tcp6 2>/dev/null | sort -u)"
    [ -z "$inodes" ] && return 0
    sleep 1
  done
  for inode in $inodes; do
    for fd in /proc/[0-9]*/fd/*; do
      [ "$(readlink "$fd" 2>/dev/null)" = "socket:[$inode]" ] || continue
      pid="${fd#/proc/}"; pid="${pid%%/*}"
      kill -9 "$pid" 2>/dev/null 2>&1 || true
    done
  done
  sleep 1
}

[ -x "$PY_BIN" ] || { echo "ERROR: 未找到 Python 解释器: $PY_BIN (建好 .venv 或用 PY_BIN 指定)" >&2; exit 1; }
[ -d "$COMFY_DIR" ] || { echo "ERROR: 未找到 ComfyUI 目录: $COMFY_DIR" >&2; exit 1; }

echo "[1/3] 停掉 $PORT 上的旧服务..."
kill_port

echo "[2/3] 后台启动 ComfyUI (log: $LOG)..."
cd "$COMFY_DIR" || { echo "ERROR: 无法进入 $COMFY_DIR" >&2; exit 1; }

# Linux 用 setsid 完全脱离终端(SSH 断开后存活); Git Bash 无 setsid, nohup 已够
LAUNCH=(nohup)
if [ "$IS_WINDOWS" -eq 0 ] && command -v setsid >/dev/null 2>&1; then
  LAUNCH=(setsid nohup)
fi
PYTHONNOUSERSITE=1 "${LAUNCH[@]}" "$PY_BIN" main.py "${ARGS[@]}" >"$LOG" 2>&1 &
SRV_PID=$!
echo "      (server PID $SRV_PID, log: $LOG)"

echo "[3/3] 等待端口 $PORT (最长 ${WAIT_SECS}s)..."
i=0
while [ "$i" -lt "$WAIT_SECS" ]; do
  if (exec 3<>"/dev/tcp/127.0.0.1/$PORT") 2>/dev/null; then
    echo "OK: ComfyUI 就绪 -> http://127.0.0.1:$PORT/"
    exit 0
  fi
  i=$((i + 1))
  sleep 1
done
echo "ERROR: 端口 $PORT 在 ${WAIT_SECS}s 内未就绪, 最近日志:"
tail -n 40 "$LOG" 2>/dev/null
exit 1
