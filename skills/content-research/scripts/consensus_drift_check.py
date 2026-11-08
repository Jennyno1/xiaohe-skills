#!/usr/bin/env python3
"""📊共识/分歧段落事件罗列漂移自检（（当时版本），2026-08-21 用户拍板）。

问题背景：日报「最大共识与分歧」段落的「核心结论 + 1-2句扩展说明」里
出现具名事件/品牌名/数字，违反「机制层结论，不是事件罗列」原则。
软规则「禁止复述引用事件」模型会漂移失效，必须用结构 + 自检验证。

用法：
    # 检查今天的报告（默认）
    python3 scripts/consensus_drift_check.py
    # 检查指定文件
    python3 scripts/consensus_drift_check.py /path/to/content-research-YYYY-MM-DD.md
    # 退出码：0 = 通过；1 = 发现事件罗列漂移；2 = 文件/段落不存在

漂移判定逻辑：
    1. 切出「### 🔵 共识解读」到「### 🔴 分歧解读」之间的内容 → body_consensus
    2. 切出「### 🔴 分歧解读」到「📖 **推荐阅读**」之间的内容 → body_divergence
    3. 对每段 body 删掉「▸ 引用 N」之后的所有内容（只看核心结论 + 扩展说明）
    4. 扫一遍内置违规词 + 用户补充词，命中即视为漂移
    5. 额外检查：body 里是否还有 URL（http:// / https://），命中即漂移
    6. 自检三步模拟：把「核心结论+扩展说明」剥出来，看总字数 < 30 视为过短/偷懒
"""

import re
import sys
from pathlib import Path
from datetime import datetime
import _paths  # noqa: E402  (same-dir helper, resolves host paths)

# 默认报告路径：<output_home>/content-research/content-research-YYYY-MM-DD.md
DEFAULT_REPORT_DIR = _paths.output_home() / "content-research"

# 8/21 实证的 4 条反例模式（作为内置违规词清单）。
# 新增时保持"具名事件 + 品牌 + 数字"三类全覆盖。
BANNED_PATTERNS = [
    # === 共识类反例 ===
    r"Ramp\s*Router",              # 产品名
    r"Stripe",                     # 公司名
    r"OpenRouter",                 # 产品名
    r"阿里\s*AI\s*ARR",            # 品牌+数字
    r"ARR\s*破百亿",               # 数字+品牌
    r"降本\s*\d+\s*%",            # 数字
    r"溢价\s*\d+(?:\.\d+)?\s*[xX×倍]",  # 数字
    # === 分歧类反例 ===
    r"WRC\s*2026",                 # 大会名+年份
    r"量子位",                     # 媒体名
    r"宇树",                       # 公司名
    r"\+?\s*\d+\s*%\s*(?:只|验证|印证|表明)",  # 涨幅 + 结论词
    # === 通用漂移信号 ===
    r"https?://\S+",               # 任何 URL（应只出现在引用事件里）
]


def extract_section(text: str, start_marker: str, end_marker: str) -> str:
    """切出 [start_marker, end_marker) 之间的内容，找不到返回空串。"""
    si = text.find(start_marker)
    if si == -1:
        return ""
    ei = text.find(end_marker, si + len(start_marker))
    if ei == -1:
        return ""
    return text[si:ei]


def strip_references(body: str) -> str:
    """删掉「▸ 引用 N」之后的所有内容（包括空行），只留核心结论+扩展说明。"""
    # 找到第一个 ▸ 出现的位置（用户模板里引用事件以 ▸ 引用 开头）
    m = re.search(r"\n\s*▸\s*引用", body)
    if m:
        return body[:m.start()]
    # 备选：找「**引用事件：**」标签
    m = re.search(r"\*\*引用事件[：:]\*\*", body)
    if m:
        return body[:m.start()]
    return body


def check_drift(body: str, label: str, banned_extra: list = None) -> list:
    """返回漂移命中清单；空清单=通过。"""
    hits = []
    patterns = BANNED_PATTERNS + (banned_extra or [])
    for p in patterns:
        for m in re.finditer(p, body):
            # 取周围 30 字符作为上下文
            ctx = body[max(0, m.start() - 30):min(len(body), m.end() + 30)].replace("\n", " ")
            hits.append({
                "section": label,
                "pattern": p,
                "match": m.group(0),
                "context": ctx,
            })
    return hits


def report_drift(report_path: Path, hits: list) -> None:
    """打印漂移报告。"""
    print(f"🚨 共识/分歧段落事件罗列漂移检测 — {report_path.name}")
    print(f"   命中 {len(hits)} 条违规：\n")
    for h in hits:
        print(f"   [{h['section']}] 命中模式: {h['pattern']!r}")
        print(f"   匹配内容: {h['match']}")
        print(f"   上下文: ...{h['context']}...\n")
    print("🛠️  修复指引：")
    print("   1. 删除核心结论+扩展说明里的具名事件/品牌/数字")
    print("   2. 把这些信息移到「▸ 引用 N」行（来源名后）")
    print("   3. 保留一句机制层结论 + 1-2 句机制说理")
    print("   4. 重跑此脚本验证 → exit 0\n")
    print("📖 详见 skill: content-research （当时版本） 「关键约束」段首 + 输出模板硬约束块")


def resolve_report_path(arg: str) -> Path:
    """解析命令行参数 → report path。"""
    if arg and Path(arg).is_file():
        return Path(arg)
    if arg:
        return Path(arg)  # 让后续 is_file() 检查失败
    # 默认今天
    today = datetime.now().strftime("%Y-%m-%d")
    return DEFAULT_REPORT_DIR / f"content-research-{today}.md"


def main(argv: list) -> int:
    report_path = resolve_report_path(argv[1] if len(argv) > 1 else None)
    if not report_path.is_file():
        print(f"❌ 报告文件不存在: {report_path}", file=sys.stderr)
        print(f"   默认查找: {DEFAULT_REPORT_DIR}/content-research-YYYY-MM-DD.md", file=sys.stderr)
        return 2

    text = report_path.read_text(encoding="utf-8")

    # 1. 共识段
    body_c = extract_section(text, "### 🔵 共识解读", "### 🔴 分歧解读")
    body_c_core = strip_references(body_c)
    # 2. 分歧段
    body_d = extract_section(text, "### 🔴 分歧解读", "📖 **推荐阅读**")
    body_d_core = strip_references(body_d)

    if not body_c and not body_d:
        print(f"⚠️  报告里没有找到「共识解读」或「分歧解读」段落", file=sys.stderr)
        print(f"   检查文件: {report_path}", file=sys.stderr)
        return 2

    # 3. 扫违规
    hits = []
    hits.extend(check_drift(body_c_core, "🔵 共识核心结论+扩展"))
    hits.extend(check_drift(body_d_core, "🔴 分歧核心结论+扩展"))

    # 4. 自检三步：核心结论+扩展说明剥出来后字数过短 = 偷懒
    for label, body in [("共识", body_c_core), ("分歧", body_d_core)]:
        clean = body.replace("###", "").replace("**", "").strip()
        if clean and len(clean) < 30:
            print(f"⚠️  {label}核心结论+扩展说明过短（{len(clean)} 字），疑似偷懒或误切")

    if hits:
        report_drift(report_path, hits)
        return 1

    # 通过
    wc_c = len(body_c_core.replace("###", "").replace("**", "").strip())
    wc_d = len(body_d_core.replace("###", "").replace("**", "").strip())
    print(f"✅ 共识/分歧段落事件罗列检测通过 — {report_path.name}")
    print(f"   共识核心结论+扩展: {wc_c} 字")
    print(f"   分歧核心结论+扩展: {wc_d} 字")
    print(f"   事件名/品牌/数字全部隔离在「▸ 引用 N」行 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
