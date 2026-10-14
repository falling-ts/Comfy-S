#!/usr/bin/env python3
"""通用容器内存清理脚本

容器内 cgroup 限额常远小于宿主内存, 进程读过的文件页缓存 (file cache)
全部计入容器限额并堆积到顶; 宿主内存充裕时内核不会主动回收,
表现为 memory.current 逼近 memory.max、分配被限流 (memory.events max 计数增长)。

本脚本对目录下的文件执行 posix_fadvise(DONTNEED), 精确丢弃干净的页缓存:
- 对 mmap 中的进程 (如 llama-server -mm) 无害, 下次访问自动重读磁盘;
- 脏页先 sync 落盘再丢弃, 不丢数据;
- 对 anon (进程真实内存) 无效, 只回收文件页缓存。

用法:
  python3 clear_page_cache.py                 # 清理默认目录 (模型目录)
  python3 clear_page_cache.py /path/a /path/b # 清理指定目录
  python3 clear_page_cache.py --min-size 1G   # 只处理大于阈值的文件 (默认 512M)

无 cgroup 限制 (裸机) 或无权限时安全退出, 退出码 0。
"""

from __future__ import annotations

import argparse
import ctypes
import os
import sys
import time

POSIX_FADV_DONTNEED = 4

# 默认清理目录: 模型文件是页缓存堆积的大户
DEFAULT_DIRS = [
    "/root/models",
    "/root/Comfy-S/models",
    "/root/Comfy-S/ComfyUI/models",
]


def parse_size(text: str) -> int:
    """'512M' / '2G' / '1073741824' → 字节数"""
    text = text.strip().upper()
    mult = 1
    for suffix, m in (("KIB", 1024), ("MIB", 1024**2), ("GIB", 1024**3),
                      ("K", 1024), ("M", 1024**2), ("G", 1024**3)):
        if text.endswith(suffix):
            mult = m
            text = text[: -len(suffix)]
            break
    return int(float(text) * mult)


def cgroup_memory() -> tuple[int, int] | None:
    """返回 (memory.current, memory.max); 无 cgroup 限制返回 None"""
    for cur, mx in (("/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory.max"),
                    ("/sys/fs/cgroup/memory/memory.usage_in_bytes",
                     "/sys/fs/cgroup/memory/memory.limit_in_bytes")):
        try:
            with open(cur) as f:
                current = int(f.read().strip())
            with open(mx) as f:
                raw = f.read().strip()
            if raw == "max":
                return None
            return current, int(raw)
        except (OSError, ValueError):
            continue
    return None


def drop_file_cache(path: str, libc: ctypes.CDLL) -> None:
    """对单个文件执行 fadvise(DONTNEED), 丢弃干净页缓存"""
    fd = os.open(path, os.O_RDONLY)
    try:
        libc.posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED)
    finally:
        os.close(fd)


def collect_files(dirs: list[str], min_size: int) -> list[str]:
    files: set[str] = set()
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for root, _dirs, names in os.walk(d, followlinks=False):
            for name in names:
                p = os.path.join(root, name)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                if not os.path.isfile(p):  # 排除软链目标重复统计
                    continue
                if st.st_size >= min_size:
                    files.add(os.path.realpath(p))
    return sorted(files, key=lambda p: os.path.getsize(p), reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="丢弃容器内文件页缓存 (fadvise DONTNEED)")
    parser.add_argument("dirs", nargs="*", default=None,
                        help=f"要清理的目录 (默认: {' '.join(DEFAULT_DIRS)})")
    parser.add_argument("--min-size", default="512M",
                        help="只处理大于该大小的文件, 如 100M / 1G (默认 512M)")
    args = parser.parse_args()

    mem = cgroup_memory()
    if mem is None:
        print("[clear_page_cache] 无 cgroup 内存限制, 无需清理")
        return 0

    dirs = args.dirs if args.dirs else DEFAULT_DIRS
    min_size = parse_size(args.min_size)

    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    os.sync()

    before = mem[0]
    files = collect_files(dirs, min_size)
    total = sum(os.path.getsize(f) for f in files)
    print(f"[clear_page_cache] 处理 {len(files)} 个文件 (≥{args.min_size}, 合计 {total/1024**3:.0f}GiB) …")
    dropped = 0
    for f in files:
        try:
            drop_file_cache(f, libc)
            dropped += 1
        except OSError:
            pass
    time.sleep(1)
    os.sync()

    after = cgroup_memory()
    if after is None:
        print("[clear_page_cache] 清理后无法读取 cgroup 状态")
        return 0
    freed = before - after[0]
    print(f"[clear_page_cache] 完成: 丢弃 {dropped}/{len(files)} 个文件, "
          f"memory.current {before/1024**3:.1f}GiB → {after[0]/1024**3:.1f}GiB "
          f"(释放 {freed/1024**3:.1f}GiB, 限额 {after[1]/1024**3:.1f}GiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
