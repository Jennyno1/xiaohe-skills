#!/usr/bin/env python3
"""IMA note sync helper for content-research daily briefing.

直接调用 IMA OpenAPI（HTTP header 传凭证），不依赖 ima_api.cjs。

v2（2026-09-16）：**加幂等**。此前无查重直接 import_doc，导致同日出现多篇重复笔记
（实测 2026-09-16 出现 2–3 篇「📋每日简报 · 9月16日」——打磨回放、手动验收、正式运行各导入一次）。
现在先按标题搜索，已存在则跳过（--force 可强制再导一次）。

Usage:
    python3 scripts/ima_sync.py [date_override] [--force]

退出码: 0=成功或已存在（跳过）/1=报告缺失或凭据缺失/3=鉴权失败/5=网络错误
"""
import json
import os
import sys
import urllib.request
from datetime import datetime
import _paths  # noqa: E402  (same-dir helper, resolves host paths)

BASE = "https://ima.qq.com/openapi/note/v1"
FORCE = "--force" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]

# --- 1. Read credentials (<hermes_home>/.env，与校验脚本同一来源) ---
env_path = _paths.hermes_home() / ".env"
env = {}
if os.path.exists(env_path):
    for line in open(env_path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

client_id = env.get("IMA_OPENAPI_CLIENTID", "")
api_key = env.get("IMA_OPENAPI_APIKEY", "")
if not client_id or not api_key:
    print(f"ERROR: IMA_OPENAPI_CLIENTID/APIKEY not found in {env_path}", file=sys.stderr)
    sys.exit(1)

HEADERS = {"Content-Type": "application/json",
           "ima-openapi-clientid": client_id,
           "ima-openapi-apikey": api_key}


def call(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode("utf-8"),
                                 headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# --- 2. Determine report date ---
date_str = args[0] if args else datetime.now().strftime("%Y-%m-%d")
report_path = str(
    _paths.output_home() / "content-research" / f"content-research-{date_str}.md")
if not os.path.exists(report_path):
    print(f"ERROR: report not found: {report_path}", file=sys.stderr)
    sys.exit(1)

title = f"📋每日简报 · {int(date_str[5:7])}月{int(date_str[8:10])}日"

# --- 3. 幂等检查：同日是否已存在 ---
if not FORCE:
    # 2026-09-18 修：原按 title「📋每日简报 · M月D日」检索，但笔记的实际标题来自报告 H1
    # （「每日内容研究简报 · M月D日」）→ 检索命中不到当天笔记 → 同日重复导入。
    # 改为按「M月D日」检索（命中率最高），仍用该日期串在标题上二次过滤。
    day_key = f"{int(date_str[5:7])}月{int(date_str[8:10])}日"
    try:
        # 🔴 search_note 的 end 上限=20（21 以上报 100001），不要调大
        res = call("/search_note", {"search_type": 0, "query_info": {"title": day_key},
                                    "start": 0, "end": 20})
    except Exception as e:
        print(f"WARN: 幂等检查失败（{str(e)[:60]}），继续导入以免漏同步", file=sys.stderr)
        res = None
    if res is not None:
        if res.get("code") != 0:
            # 搜索通道异常时不能阻断同步（历史上这里会把「参数错」误判成鉴权失败）
            print(f"WARN: 幂等检查返回非 0（{res.get('code')}: {res.get('msg')}），继续导入",
                  file=sys.stderr)
        else:
            infos = res.get("data", {}).get("search_note_infos", [])
            same = [i for i in infos
                    if day_key in str(i.get("note_book_info", {}).get("title", ""))]
            if same:
                ids = ", ".join(i["note_book_info"].get("note_id", "?") for i in same)
                print(f"SKIP note_id={ids} (已存在同日笔记，未重复导入；--force 可强制)")
                sys.exit(0)

# --- 4. 导入 ---
content = open(report_path, encoding="utf-8").read()
try:
    result = call("/import_doc", {"content_format": 1, "content": content})
except Exception as e:
    print(f"NETWORK_ERROR: {e}", file=sys.stderr)
    sys.exit(5)

# --- 5. 结果 ---
code = result.get("code", -1)
if code == 0:
    print(f"OK note_id={result.get('data', {}).get('note_id', 'unknown')}")
    sys.exit(0)
if code == -200:
    print(f"VERSION_UPDATE_NEEDED: {result.get('release_desc', '')}")
    sys.exit(2)
if code == 200002:
    print(f"AUTH_FAILED: {result.get('msg', 'skill auth failed')}")
    sys.exit(3)
print(f"UNKNOWN_ERROR code={code}: {result.get('msg', '')}")
sys.exit(4)
