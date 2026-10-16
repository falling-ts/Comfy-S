#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RunningHub 工作流库更新脚本

拉取官网全量广场「21 个一级分类 × 每类最热门前 50」并增量落盘到 workflows/<分类>/。

口径(2026-10-16 定, 与用户确认):
  - 排序: sort=HOTTEST, days=90 (官网「最热」榜, 90 天热度窗口)
  - 数量: 每类前 50 ⇒ 21 类合并去重后约 804 条唯一工作流
  - 判重: 按**内容 sha256** 全局去重 —— 本地已有同内容文件则不再落盘, 也不重复占空间
  - 文件名: 取服务端 Content-Disposition; 同名但内容不同时加 `<工作流ID>_` 前缀, 绝不覆盖旧文件

⚠️ 无法做到「不重复下载」: 列表接口不返回内容哈希, getDetail 的 md5 字段实测恒为 None,
   只有把内容下下来才知道是否已存在。因此每条都会下载一次(804 条约 1~2 分钟, 并发)。

用法:
  RUNNINGHUB_TOKEN=<裸 JWT> python update-runninghub.py            # 全量更新
  RUNNINGHUB_TOKEN=<裸 JWT> python update-runninghub.py --dry-run  # 只拉列表统计, 不下载
  RUNNINGHUB_TOKEN=<裸 JWT> python update-runninghub.py --workers 6

token 取法: 登录 runninghub.cn → F12 Network → 复制任意接口请求 Authorization 头的
JWT 部分(不带 "Bearer " 前缀; 带脚本也会自动剥掉)。有效期约 30 天。
"""

import argparse
import collections
import datetime
import hashlib
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote, unquote_plus

try:
    import requests
except ImportError:  # pragma: no cover
    sys.exit("需要 requests: pip install requests")

API = "https://www.runninghub.cn"

HERE = Path(__file__).resolve().parent
WF_ROOT = HERE / "workflows"
INDEX_MD = HERE / "workflows-list.md"

SORT = "HOTTEST"
DAYS = 90
TOP_N = 50
PAGE_SIZE = 50          # 实测一页最多可取 200, 取 50 一页足够拿到前 50

# 文件名里不允许出现的字符(跨平台)
_ILLEGAL = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def _headers(token: str) -> dict:
    return {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "client": "WEB",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"),
        "Referer": "https://www.runninghub.cn/page-workflow",
        "Origin": "https://www.runninghub.cn",
        "x-rh-lang": "zh",
        "user-language": "zh_CN",
    }


def _post_json(session, path: str, body: dict, tries: int = 3) -> dict:
    """POST 一个 JSON 接口, 带简单重试。"""
    last = None
    for i in range(tries):
        try:
            r = session.post(API + path, json=body, timeout=90)
            if r.status_code == 200:
                return r.json()
            last = "HTTP %s" % r.status_code
        except Exception as exc:  # noqa: BLE001 - 网络异常一律重试
            last = repr(exc)
        time.sleep(1.5 * (i + 1))
    raise RuntimeError("%s 请求失败: %s" % (path, last))


def _export(session, wid: str, tries: int = 3):
    """下载工作流 JSON, 返回 (bytes, Content-Disposition)。"""
    last = None
    for i in range(tries):
        try:
            r = session.post(API + "/api/workflow/export",
                             json={"workflowId": wid}, timeout=300)
            if r.status_code == 200 and r.content:
                return r.content, r.headers.get("Content-Disposition", "")
            last = "HTTP %s, %d bytes" % (r.status_code, len(r.content or b""))
        except Exception as exc:  # noqa: BLE001
            last = repr(exc)
        time.sleep(2.0 * (i + 1))
    raise RuntimeError("export %s 失败: %s" % (wid, last))


def _filename_from_cd(cd: str, fallback: str) -> str:
    """从 Content-Disposition 解析文件名(RFC 5987 与普通两种写法都试)。"""
    name = None
    if cd:
        m = re.search(r"filename\*\s*=\s*([^;]+)", cd, re.I)
        if m:
            v = m.group(1).strip().strip('"')
            if "''" in v:
                v = v.split("''", 1)[1]
            name = unquote(v)
        else:
            m = (re.search(r'filename\s*=\s*"([^"]*)"', cd, re.I)
                 or re.search(r"filename\s*=\s*([^;]+)", cd, re.I))
            if m:
                name = unquote_plus(m.group(1).strip().strip('"'))
    if not name:
        name = fallback
    name = _ILLEGAL.sub("_", name).strip().strip(".")
    if not name:
        name = "workflow"
    if not name.lower().endswith(".json"):
        name += ".json"
    return name[:180]      # 避免超出文件系统单段上限


def _build_local_index():
    """扫本地全部工作流, 建 {sha256: 相对路径} 与占用路径集合。"""
    by_hash = {}
    paths = set()
    n = 0
    for p in sorted(WF_ROOT.rglob("*.json")):
        try:
            h = hashlib.sha256(p.read_bytes()).hexdigest()
        except Exception:  # noqa: BLE001 - 读不了就跳过
            continue
        rel = p.relative_to(WF_ROOT).as_posix()
        by_hash.setdefault(h, rel)
        paths.add(rel)
        n += 1
    return by_hash, paths, n


def fetch_plan(session):
    """拉分类树 + 每类前 50, 返回 (plan, percat)。plan 为 [(分类名, 记录), ...]。"""
    tree = _post_json(session, "/api/portal/tag/tree", {"rang": "WORKFLOW"})["data"]
    plan = []
    percat = collections.OrderedDict()
    for cat in tree:
        # ⚠️ tags 必须传**子标签 ID 数组**: 传一级分类 ID 只会返回少量官方模板
        tag_ids = [t["id"] for t in (cat.get("childTags") or [])] or [cat["id"]]
        data = _post_json(session, "/api/portal/template/list", {
            "size": PAGE_SIZE, "current": 1, "sort": SORT,
            "days": DAYS, "tags": tag_ids,
        }).get("data") or {}
        recs = (data.get("records") or [])[:TOP_N]
        percat[cat["name"]] = {"site_total": int(data.get("total") or 0),
                               "fetched": len(recs)}
        for r in recs:
            plan.append((cat["name"], r))
        time.sleep(0.15)
    return plan, percat


def _stat(rec):
    st = rec.get("statisticsInfo") or {}
    def _i(k):
        try:
            return int(st.get(k) or 0)
        except (TypeError, ValueError):
            return 0
    return {"like": _i("likeCount"), "use": _i("useCount"),
            "collect": _i("collectCount"), "download": _i("downloadCount")}


def main() -> int:
    ap = argparse.ArgumentParser(description="RunningHub 工作流库更新")
    ap.add_argument("--dry-run", action="store_true", help="只拉列表统计, 不下载")
    ap.add_argument("--workers", type=int, default=4, help="并发下载线程数(默认 4)")
    args = ap.parse_args()

    token = (os.environ.get("RUNNINGHUB_TOKEN") or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token:
        return print("请设置环境变量 RUNNINGHUB_TOKEN(裸 JWT, 不带 'Bearer ' 前缀)") or 2

    session = requests.Session()
    session.headers.update(_headers(token))

    print("== 1) 拉取分类列表 ==")
    plan, percat = fetch_plan(session)
    uniq = {}
    for cat, rec in plan:
        uniq.setdefault(rec["id"], (cat, rec))
    print("   21 类共取到 %d 条记录, 去重后 %d 个唯一工作流" % (len(plan), len(uniq)))

    if args.dry_run:
        for name, info in percat.items():
            print("   %-12s 站点 total=%-7s 本次取样=%d" %
                  (name, info["site_total"], info["fetched"]))
        print("\n(dry-run, 未下载任何文件)")
        return 0

    print("\n== 2) 建本地内容索引 ==")
    by_hash, taken, n_local = _build_local_index()
    print("   本地已有 %d 个 json, 唯一内容 %d 种" % (n_local, len(by_hash)))

    print("\n== 3) 并发下载 %d 个工作流(workers=%d) ==" % (len(uniq), args.workers))
    lock = threading.Lock()
    done = [0]
    payloads = []          # (cat, rec, content, cd)
    failures = []

    def _job(item):
        wid, (cat, rec) = item
        content, cd = _export(session, wid)
        with lock:
            done[0] += 1
            if done[0] % 50 == 0:
                print("   已下载 %d/%d" % (done[0], len(uniq)))
        return cat, rec, content, cd

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futs = {pool.submit(_job, it): it[0] for it in uniq.items()}
        for fut in as_completed(futs):
            wid = futs[fut]
            try:
                payloads.append(fut.result())
            except Exception as exc:  # noqa: BLE001
                failures.append((wid, str(exc)))
                print("   !! 失败 %s: %s" % (wid, exc))
    print("   下载完成: 成功 %d, 失败 %d" % (len(payloads), len(failures)))

    print("\n== 4) 按内容哈希去重落盘 ==")
    added, skipped_dup, renamed = [], [], []
    for cat, rec, content, cd in payloads:
        wid = rec["id"]
        h = hashlib.sha256(content).hexdigest()
        if h in by_hash:
            skipped_dup.append((cat, rec, by_hash[h]))
            continue
        cat_dir = WF_ROOT / cat
        cat_dir.mkdir(parents=True, exist_ok=True)
        fname = _filename_from_cd(cd, rec.get("name") or wid)
        rel = (Path(cat) / fname).as_posix()
        if rel in taken:
            # 同名不同内容 ⇒ 加 <工作流ID>_ 前缀, 绝不覆盖
            fname = "%s_%s" % (wid, fname)
            rel = (Path(cat) / fname).as_posix()
            was_renamed = True
        else:
            was_renamed = False
        target = WF_ROOT / cat / fname
        if target.exists():
            # 极端情况: 连加前缀后都还占着 —— 跳过并计入失败, 不覆盖
            failures.append((wid, "同名冲突未解决: " + rel))
            continue
        target.write_bytes(content)
        taken.add(rel)
        by_hash[h] = rel
        added.append((cat, rec, rel))
        if was_renamed:
            renamed.append((cat, rec, rel))

    print("   新增 %d, 内容重复跳过 %d, 同名加 ID 前缀 %d" %
          (len(added), len(skipped_dup), len(renamed)))

    # 目录内合计
    print("\n== 5) 目录内合计 ==")
    col = collections.Counter()
    for p in WF_ROOT.rglob("*.json"):
        col[p.parent.name] += 1
    for name in percat:
        print("   %-12s %d" % (name, col.get(name, 0)))
    print("   总计 %d" % sum(col.values()))

    # 追加运行账本(不覆盖历史)
    if not added and not failures:
        print("\n本次无新增(库已是最新), 不追加账本记录。")
        return 0
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = ["", "---", "", "## 更新记录 %s" % stamp, "",
             "口径: `sort=%s`、`days=%d`、每类前 %d;按内容 sha256 全局去重。" %
             (SORT, DAYS, TOP_N), "",
             "| 分类 | 站点 total | 本次取样 | 目录内合计 |", "|---|---|---|---|"]
    for name, info in percat.items():
        lines.append("| %s | %s | %d | %d |" %
                     (name, info["site_total"], info["fetched"], col.get(name, 0)))
    lines += ["", "- 唯一工作流 **%d** 个:新增 **%d**、内容重复跳过 **%d**、同名加 ID 前缀 **%d**、失败 **%d**。"
              % (len(uniq), len(added), len(skipped_dup), len(renamed), len(failures))]
    if failures:
        lines += ["", "失败明细:", ""] + ["- `%s` — %s" % (w, m) for w, m in failures]
    lines.append("")
    with INDEX_MD.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("\n已追加更新记录到 %s" % INDEX_MD.name)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
