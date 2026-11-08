#!/usr/bin/env python3
"""
共识/分歧段落硬约束校验脚本

权威规则源：references/consensus-division-rules.md
调用方：cron prompt / ad-hoc 手动跑 / skill 内嵌质量门

校验内容（按 references/consensus-division-rules.md 硬约束）：
  1. 「核心结论」+「1-2 句扩展说明」段里是否出现具名事件/品牌/数字（反例 1-4）
  2. 「引用事件」▸ 引用N：来源名 格式是否完整
  3. 是否做了「删掉引用事件后段落还能读懂」自检（启发式：核心结论+扩展说明的实词数是否足够）

退出码：
  0 = 合规
  1 = 检测到反例或格式违规
  2 = 文件读取/解析错误

用法：
  python3 consensus_check.py --report /path/to/content-research-YYYY-MM-DD.md
  python3 consensus_check.py --report ... --json  # 输出 JSON 格式
"""
import argparse
import json
import re
import sys
from pathlib import Path

# 规则源 references/consensus-division-rules.md 的反例关键词
BANNED_PHRASES = [
    # 反例 1: 共识堆叠事件
    "Ramp Router（降本40%）",
    "Stripe收购OpenRouter（溢价5.4x）",
    "Stripe 收购 OpenRouter",
    "阿里AI ARR破百亿",
    "ARR破百亿",
    "降本40%",
    "溢价5.4x",
    "溢价5.4×",
    "5.4倍",
    "三方独立信号",
    # 反例 2: 分歧并列堆叠
    "WRC 2026",
    "WRC展商",
    "量子位报道强调",
    "WRC 2026'",
    "今年都在关心场景",
    # 反例 3: 数据点混入
    "宇树上市+629%",
    "宇树上市",
    "+629%",
    "629%",
    # 反例 4: 变体堆叠
    "Ramp三年内部经验商业化",
    "OpenRouter被Stripe抢购",
]

# 自检阈值：核心结论+扩展说明合并后，实词数（中文字符 + 英文词）应 ≥ 30
MIN_CONTENT_WORDS = 30

# 段落定位正则
CONSENSUS_HEADER = re.compile(r"##\s*🔵\s*共识解读")
DIVISION_HEADER = re.compile(r"##\s*🔴\s*分歧解读")
QUOTE_HEADER = re.compile(r"\*\*引用事件[：:]\*\*")


def extract_section(prompt_text: str, header_regex: re.Pattern) -> tuple[int, int] | None:
    """定位段落起止位置。"""
    m = header_regex.search(prompt_text)
    if not m:
        return None
    start = m.start()
    # 找到下一个 ## 标题或文件末尾
    next_header = re.search(r"\n##\s+", prompt_text[m.end():])
    end = m.end() + next_header.start() if next_header else len(prompt_text)
    return start, end


def split_body_and_quotes(section: str) -> tuple[str, str]:
    """把段落切成「核心结论+扩展说明」和「引用事件」两部分。"""
    m = QUOTE_HEADER.search(section)
    if not m:
        return section, ""
    return section[: m.start()], section[m.end():]


def check_banned_phrases(body: str) -> list[str]:
    """检查核心结论+扩展说明里是否出现反例关键词。"""
    hits = []
    for phrase in BANNED_PHRASES:
        if phrase in body:
            hits.append(phrase)
    return hits


def count_content_words(body: str) -> int:
    """计算实词数量：去掉 markdown 符号/标点后的中文/英文词数。
    中文按字符算（每字符 1 个语义单元），英文按 \\w+ 算（每词 1 个）。
    """
    cleaned = re.sub(r"\*\*[^*]+\*\*", "", body)
    cleaned = re.sub(r"`[^`]+`", "", cleaned)
    cleaned = re.sub(r"[▸•●①-③]", " ", cleaned)
    cleaned = re.sub(r"[，。、；：？！（）()【】《》「」『』\"'\s]+", "", cleaned)
    cleaned = re.sub(r"[.,;:?!()\[\]{}<>\"'\s]+", "", cleaned)
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", cleaned))
    english_words = len(re.findall(r"[A-Za-z]+", cleaned))
    return chinese_chars + english_words


def check_quote_format(quotes: str) -> list[str]:
    """检查引用事件 ▸ 引用N：来源名 格式。"""
    issues = []
    if not quotes.strip():
        issues.append("缺「引用事件」段（按规则 2 应有 ▸ 引用1/2/3）")
        return issues
    lines = [l for l in quotes.strip().split("\n") if l.strip()]
    refs_found = re.findall(r"▸\s*引用\d+[：:]", "".join(lines))
    if not refs_found:
        refs_found = re.findall(r"^▸\s*\S", "\n".join(lines), re.MULTILINE)
    if len(refs_found) < 3:
        issues.append(f"引用事件数 {len(refs_found)} 条，按硬约束 4 应 ≥ 3 条独立事件")
    return issues


def check_section(label: str, section: str) -> dict:
    """单段（共识或分歧）校验。"""
    body, quotes = split_body_and_quotes(section)
    banned = check_banned_phrases(body)
    word_count = count_content_words(body)
    quote_issues = check_quote_format(quotes)
    return {
        "label": label,
        "body_chars": len(body.strip()),
        "content_words": word_count,
        "banned_phrases": banned,
        "quote_issues": quote_issues,
        "pass": not banned and not quote_issues and word_count >= MIN_CONTENT_WORDS,
    }


def main():
    ap = argparse.ArgumentParser(description="共识/分歧段落硬约束校验")
    ap.add_argument("--report", required=True, help="报告 markdown 路径")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    report_path = Path(args.report).expanduser()
    if not report_path.exists():
        print(f"❌ 报告不存在: {report_path}", file=sys.stderr)
        sys.exit(2)

    try:
        text = report_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ 读取失败: {e}", file=sys.stderr)
        sys.exit(2)

    results = []
    for label, regex in [("共识", CONSENSUS_HEADER), ("分歧", DIVISION_HEADER)]:
        section_range = extract_section(text, regex)
        if not section_range:
            results.append({
                "label": label, "found": False, "pass": False,
                "issue": f"未找到 ## {'🔵' if '共识' in label else '🔴'} {label}解读 标题"
            })
            continue
        section = text[section_range[0]: section_range[1]]
        result = check_section(label, section)
        result["found"] = True
        results.append(result)

    overall_pass = all(r.get("pass") for r in results)

    output = {
        "report": str(report_path),
        "overall_pass": overall_pass,
        "sections": results,
    }

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"📊 共识/分歧段落校验 — {report_path.name}")
        print()
        for r in results:
            label = r["label"]
            if not r.get("found"):
                print(f"  {label} 段: ❌ {r.get('issue', '未找到')}")
                continue
            status = "✅" if r["pass"] else "�"
            print(f"  {label} 段: {status}")
            print(f"    核心结论+扩展字数: {r['body_chars']}")
            print(f"    实词数: {r['content_words']} (阈值 ≥ {MIN_CONTENT_WORDS})")
            if r["banned_phrases"]:
                print(f"    ⚠️  命中反例关键词: {r['banned_phrases']}")
            if r["quote_issues"]:
                print(f"    ⚠️  引用事件格式问题: {r['quote_issues']}")
        print()
        print("整体:", "✅ 合规，可交付" if overall_pass else "❌ 不合规，必须重写")

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
