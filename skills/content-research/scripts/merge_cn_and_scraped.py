#!/usr/bin/env python3
"""
Post-parse merge script for content-research pipeline.

After parse_all_feeds.py runs (which often misses RSSHub Chinese sources
and web-scraped sources), this script:
  1. Parses RSSHub JSON files from /tmp/ (36kr, huxiu, zhihu)
  2. Parses /tmp/scraped_sources.json (Anthropic/Meta/Microsoft/Google Cloud/Menlo)
  3. Deduplicates against existing /tmp/all_deduped.json
  4. Appends new items and saves

Usage:
  python3 merge_cn_and_scraped.py                    # merge all available
  python3 merge_cn_and_scraped.py --cn-only          # skip scraped_sources.json
  python3 merge_cn_and_scraped.py --scraped-only     # skip CN RSSHub files

Exit codes: 0 = success with new items, 1 = no new items added, 2 = error
"""
import json
import os
import sys
from collections import Counter

ALL_DEDUPED = "/tmp/all_deduped.json"
SCRAPED_JSON = "/tmp/scraped_sources.json"

RSSHUB_FILES = {
    "/tmp/36kr_news.json": "36氪快讯",
    "/tmp/36kr_hot.json": "36氪热榜",
    "/tmp/huxiu_articles.json": "虎嗅",
    "/tmp/zhihu_hot.json": "知乎热榜",
}


def parse_rsshub(path, source_name):
    """Safe parse RSSHub JSON, handling Extra data via raw_decode."""
    try:
        with open(path) as f:
            raw = f.read().strip()
        decoder = json.JSONDecoder()
        data = decoder.raw_decode(raw)[0]
    except Exception as e:
        print(f"⚠️ Failed to parse {path}: {e}", file=sys.stderr)
        return []

    items = data.get("item", []) or data.get("items", []) or []
    results = []
    for item in items[:20]:
        title = item.get("title", "")
        link = item.get("link", item.get("url", ""))
        pub_date = item.get("pubDate", item.get("pub_date", ""))
        if not title and not link:
            continue
        results.append({
            "title": title,
            "link": link,
            "pubDate": pub_date,
            "source": source_name,
            "level": "L2",
            "source_type": "cn_media",
        })
    return results


def parse_scraped(path):
    """Load scraped_sources.json (already well-formatted)."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to parse {path}: {e}", file=sys.stderr)
        return []


def main():
    cn_only = "--cn-only" in sys.argv
    scraped_only = "--scraped-only" in sys.argv

    # Load existing
    if not os.path.exists(ALL_DEDUPED):
        print(f"❌ {ALL_DEDUPED} not found", file=sys.stderr)
        sys.exit(2)

    with open(ALL_DEDUPED) as f:
        existing = json.load(f)

    existing_titles = set()
    for item in existing:
        t = item.get("title", "")[:60].lower().strip()
        if t:
            existing_titles.add(t)

    before = len(existing)
    new_items = []

    # 1. CN RSSHub sources
    if not scraped_only:
        for path, source_name in RSSHUB_FILES.items():
            if os.path.exists(path):
                items = parse_rsshub(path, source_name)
                for item in items:
                    t = item.get("title", "")[:60].lower().strip()
                    if t and t not in existing_titles:
                        existing_titles.add(t)
                        existing.append(item)
                        new_items.append(item)

    # 2. Web-scraped sources
    if not cn_only and os.path.exists(SCRAPED_JSON):
        scraped = parse_scraped(SCRAPED_JSON)
        for item in scraped:
            t = item.get("title", "")[:60].lower().strip()
            if t and t not in existing_titles:
                existing_titles.add(t)
                existing.append(item)
                new_items.append(item)

    after = len(existing)
    added = after - before

    # Save
    with open(ALL_DEDUPED, "w") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    # Report
    print(f"Merged: +{added} new items ({before} → {after} total)")
    source_counts = Counter(i["source"] for i in existing)
    print("Source distribution:")
    for s, cnt in source_counts.most_common():
        print(f"  {s}: {cnt}")

    if added == 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
