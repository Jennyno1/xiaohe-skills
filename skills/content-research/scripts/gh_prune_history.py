#!/usr/bin/env python3
"""
GitHub 推荐历史库清理工具 (content-research skill)

解决问题：parse_all_feeds.py 后续的筛选脚本会把 `final` 列表全部候选
（最多 8 个）自动追加写入 <hermes_home>/recommended-repos.json，但报告
实际只采用 3 个。未采用的候选会被永久拉黑，后续日报再也推荐不到。

用法（在筛选脚本后、报告生成前执行）：
    python3 <hermes_home>/skills/digital-twin/content-research/scripts/gh_prune_history.py \
        --selected "firecrawl/firecrawl,n8n-io/n8n,Significant-Gravitas/AutoGPT"

也可指定当日 final 候选 JSON，脚本会自动过滤掉未被采纳的：
    python3 gh_prune_history.py --candidates /tmp/gh_trending.json
"""
import argparse
import json
import os
import sys
import _paths  # noqa: E402  (same-dir helper, resolves host paths)

HISTORY_PATH = _paths.hermes_home() / "recommended-repos.json"


def load_history():
    try:
        with open(HISTORY_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def load_candidates(path):
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return [p["full_name"] for p in data.get("items", [])]
        elif isinstance(data, list):
            return [p["full_name"] for p in data if "full_name" in p]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return []


def prune(candidates, selected):
    """从历史库中移除当日候选中未被采纳的项目。"""
    candidates_set = set(candidates)
    selected_set = set(selected)
    history = load_history()
    before = len(history)
    cleaned = [r for r in history if r not in candidates_set or r in selected_set]
    removed = [r for r in history if r in candidates_set and r not in selected_set]

    if cleaned != history:
        with open(HISTORY_PATH, "w") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print(f"History: {before} -> {len(cleaned)} (removed {len(removed)})")
    if removed:
        print(f"Removed from history: {', '.join(removed)}")


def main():
    parser = argparse.ArgumentParser(description="清理 GitHub 推荐历史库")
    parser.add_argument(
        "--candidates",
        help="当日 final 候选 JSON 路径（默认 /tmp/gh_trending.json）",
        default="/tmp/gh_trending.json",
    )
    parser.add_argument(
        "--selected",
        help="当日实际采纳的 org/repo 列表（逗号分隔）",
        default="",
    )
    args = parser.parse_args()

    candidates = load_candidates(args.candidates)
    if not candidates:
        print(f"⚠️ 无法从 {args.candidates} 加载候选", file=sys.stderr)
        sys.exit(1)

    selected = [s.strip() for s in args.selected.split(",") if s.strip()]
    if not selected:
        print("⚠️ 未指定 --selected，跳过清理", file=sys.stderr)
        sys.exit(1)

    prune(candidates, selected)


if __name__ == "__main__":
    main()
