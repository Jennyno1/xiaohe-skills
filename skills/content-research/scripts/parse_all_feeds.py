#!/usr/bin/env python3
"""Parse all RSS/Atom feeds and RSSHub JSON, dedup, output for report generation (v8.0).

Reads from /tmp/rss_*.xml (RSS feeds), /tmp/36kr_*.json etc (RSSHub).
Outputs:
  /tmp/all_deduped.json — deduplicated item list (L1 > L2 > L3 priority, with source_type)
  /tmp/hot_words.json   — (placeholder, reserved)

Used by content-research skill as a consolidated alternative to inline heredocs.

v8.0 changes:
- Added new L1 sources: NVIDIA AI Blog, AWS AI Blog, Google/DeepMind Blog
- Added source_type field to all items (official/research/analysis/media_news/cn_media/community)
- Improved dedup with source priority awareness
"""

import xml.etree.ElementTree as ET
import json, sys, re
from datetime import datetime, timezone, timedelta

ARXIV_KEYWORDS = [
    'agent','multi-agent','tool use','function calling','RAG',
    'retrieval augmented','LLM application','autonomous','reasoning','planning',
    'code generation','benchmark','evaluation','alignment','safety'
]

# Source type mapping (v8.0)
SOURCE_TYPE_MAP = {
    # L1 Official
    'OpenAI': 'official',
    '阿里云': 'official',
    'NVIDIA AI Blog': 'official',
    'AWS AI Blog': 'official',
    'Google/DeepMind Blog': 'official',
    # L1 Research
    'arXiv cs.AI': 'research',
    'arXiv cs.CL': 'research',
    # L2 Independent Analysis
    'Simon Willison': 'analysis',
    'Latent Space': 'analysis',
    'Product Hunt': 'analysis',
    # L2 Media
    'TechCrunch AI': 'media_news',
    'TechCrunch M&A': 'media_news',
    'The Decoder': 'media_news',
    'The Verge AI': 'media_news',
    # L2 CN Media
    '36氪快讯': 'cn_media',
    '36氪热榜': 'cn_media',
    '虎嗅': 'cn_media',
    '知乎': 'cn_media',
    '量子位': 'cn_media',
    'IT之家': 'cn_media',
    # Community
    'GitHub Trending': 'community',
    'Hacker News': 'community',
}

def get_source_type(source_name):
    """Map source name to source_type label."""
    for key, stype in SOURCE_TYPE_MAP.items():
        if key in source_name:
            return stype
    return 'media_news'  # default

def is_recent(pub_date_str, days=7):
    if not pub_date_str: return True
    for fmt in ['%a, %d %b %Y %H:%M:%S %z','%a, %d %b %Y %H:%M:%S %Z',
                '%Y-%m-%dT%H:%M:%SZ','%Y-%m-%dT%H:%M:%S%z','%Y-%m-%d %H:%M:%S']:
        try: dt = datetime.strptime(pub_date_str.strip(), fmt); break
        except: continue
    else: return True
    # Make naive datetimes timezone-aware (assume UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt) < timedelta(days=days)

def strip_html(text):
    return re.sub(r'<[^>]+>', '', text) if text else ''

def extract_items(xml_path, source_name, level, is_arxiv=False, max_items=15):
    try: tree = ET.parse(xml_path); root = tree.getroot()
    except: return []
    items = []
    ns = {'atom':'http://www.w3.org/2005/Atom'}
    source_type = get_source_type(source_name)
    # RSS 2.0
    for item in root.findall('.//item'):
        title = (item.findtext('title','') or '').strip()
        link = (item.findtext('link','') or '').strip()
        pub_date = item.findtext('pubDate','') or ''
        desc = strip_html(item.findtext('description','') or '')
        if not title and not link: continue
        if not is_recent(pub_date, 7): continue
        if is_arxiv and not any(kw.lower() in (title+' '+desc).lower() for kw in ARXIV_KEYWORDS): continue
        items.append({'title':title,'link':link,'pubDate':pub_date,'source':source_name,'level':level,
                      'source_type':source_type,'description':desc[:300]})
        if len(items) >= max_items: break
    # Atom
    for entry in root.findall('.//atom:entry', ns):
        title = (entry.findtext('atom:title','',ns) or '').strip()
        link_el = entry.find('atom:link',ns)
        link = link_el.get('href','') if link_el is not None else ''
        pub_date = (entry.findtext('atom:published','',ns) or entry.findtext('atom:updated','',ns) or '')
        if not link:  # try alternate link
            for l in entry.findall('atom:link',ns):
                if l.get('rel') == 'alternate': link = l.get('href',''); break
        # Atom feeds carry no <description>; fall back to <summary>, then <content>
        summary = (entry.findtext('atom:summary','',ns) or entry.findtext('atom:content','',ns) or '')
        desc = strip_html(summary)[:300]
        if not title and not link: continue
        if is_arxiv and not any(kw.lower() in (title+' ').lower() for kw in ARXIV_KEYWORDS): continue
        items.append({'title':title,'link':link,'pubDate':pub_date,'source':source_name,'level':level,
                      'source_type':source_type,'description':desc})
        if len(items) >= max_items: break
    return items

def parse_rsshub(path):
    """Safe-parse RSSHub JSON, handling Extra data."""
    try:
        with open(path,'rb') as f: raw = f.read()
        text = raw.decode('utf-8')
    except: return []
    decoder = json.JSONDecoder()
    try: data,_ = decoder.raw_decode(text); return data
    except:
        try: return json.loads(text, strict=False)
        except: return []

# === MAIN ===
results = []

# L1 官方源 (v8.0: +NVIDIA +AWS +DeepMind)
for spec in [('/tmp/rss_openai.xml','OpenAI'),
             ('/tmp/rss_alibaba.xml','阿里云'),
             ('/tmp/rss_nvidia.xml','NVIDIA AI Blog'),
             ('/tmp/rss_aws_ai.xml','AWS AI Blog'),
             ('/tmp/rss_deepmind.xml','Google/DeepMind Blog'),
             ('/tmp/rss_ms_ai.xml','Microsoft AI')]:
    results.extend(extract_items(spec[0], spec[1], 'L1'))

# L1 研究源
for spec in [('/tmp/rss_arxiv_ai.xml','arXiv cs.AI',True),('/tmp/rss_arxiv_cl.xml','arXiv cs.CL',True)]:
    results.extend(extract_items(spec[0], spec[1], 'L1', is_arxiv=spec[2]))

# L2 英文深度 + AI创作工具雷达
for spec in [('/tmp/rss_simonw.xml','Simon Willison'),('/tmp/rss_latentspace.xml','Latent Space'),
             ('/tmp/rss_producthunt.xml','Product Hunt'),('/tmp/rss_tc_ai.xml','TechCrunch AI'),
             ('/tmp/rss_tc_ma.xml','TechCrunch M&A'),('/tmp/rss_qbitai.xml','量子位')]:
    results.extend(extract_items(spec[0], spec[1], 'L2'))

# L2 RSSHub 中文源（36氪/虎嗅/知乎 — 已升级为L2）
rsshub_sources = [
    ('/tmp/36kr_news.json','36氪快讯','L2'),
    ('/tmp/36kr_hot.json','36氪热榜','L2'),
    ('/tmp/huxiu_articles.json','虎嗅','L2'),
    ('/tmp/zhihu_hot.json','知乎','L2'),
]
for path, label, level in rsshub_sources:
    try:
        data = parse_rsshub(path)
        if not isinstance(data, dict): continue
        rss_items = data.get('item', []) if isinstance(data, dict) else []
        if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
            rss_items = data['data']
        source_type = get_source_type(label)
        for it in rss_items[:12]:
            if isinstance(it, dict):
                title = (it.get('title','') or '').strip()
                link = (it.get('link','') or it.get('url','') or '').strip()
                desc = strip_html(it.get('description','') or '')[:300]
                if title:
                    results.append({'title':title,'link':link,'pubDate':it.get('pubDate','') or it.get('date','') or '',
                                    'source':label,'level':level,'source_type':source_type,'description':desc})
    except Exception as e:
        print(f"⚠️ RSSHub parse error {path}: {e}", file=sys.stderr)

# L3 聚焦补充
for spec in [('/tmp/rss_thedecoder.xml','The Decoder'),('/tmp/rss_ithome.xml','IT之家'),
             ('/tmp/rss_verge_ai.xml','The Verge AI')]:
    results.extend(extract_items(spec[0], spec[1], 'L3'))

# v8.0: Web scraping sources (Anthropic/Meta AI/Microsoft/Google Cloud AI/Menlo)
try:
    with open('/tmp/scraped_sources.json') as f:
        scraped = json.load(f)
    for item in scraped:
        if item.get('title'):
            item.setdefault('description','')
            results.append(item)
    print(f"  Loaded {len(scraped)} items from scraped_sources.json", file=sys.stderr)
except FileNotFoundError:
    print("  ⚠️ scraped_sources.json not found, skipping web scraping sources", file=sys.stderr)

# === DEDUP (L1 > L2 > L3 priority, with source_type) ===
seen_titles = set()
deduped = []
level_order = {'L1':0,'L2':1,'L3':2,'L4':3}
all_sorted = sorted(results, key=lambda x: level_order.get(x.get('level','L4'),4))
for item in all_sorted:
    title_key = (item.get('title','') or '')[:80].lower().strip()
    if not title_key or title_key in seen_titles: continue
    seen_titles.add(title_key)
    deduped.append(item)

# === JUNK FILTER（2026-10-08）===
# 背景：一条“小行星撞地球/末日”的垃圾传闻混进素材池，agent 为它连做 50 次 web_search 求证，
# 撞上护栏导致整轮日报报废。垃圾素材是触发器，在解析层就剔掉，别让它进池。
# 判据取“精确且低误报”：含邮箱地址（垃圾传播特征）→ 直接丢，并打日志（可审计，不静默）。
import re as _re
_EMAIL_RE = _re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
junk, kept = [], []
for item in deduped:
    blob = f"{item.get('title','')} {item.get('description','')}"
    if _EMAIL_RE.search(blob):
        junk.append(item)
        continue
    kept.append(item)
if junk:
    print(f"🧹 JUNK FILTER: 剔除 {len(junk)} 条含邮箱等垃圾特征素材", file=sys.stderr)
    for j in junk[:5]:
        print(f"   - [{j.get('source')}] {(j.get('title') or '')[:60]}", file=sys.stderr)
deduped = kept

# === STATISTICS ===
level_counts = {}
source_type_counts = {}
source_counts = {}
for i in deduped:
    lv = i.get('level','?')
    level_counts[lv] = level_counts.get(lv,0)+1
    st = i.get('source_type','?')
    source_type_counts[st] = source_type_counts.get(st,0)+1
    src = i.get('source','?')
    source_counts[src] = source_counts.get(src,0)+1

print(f"Total after dedup: {len(deduped)}", file=sys.stderr)
for lv in sorted(level_counts.keys()):
    print(f"  {lv}: {level_counts[lv]}", file=sys.stderr)
print(f"Source types:", file=sys.stderr)
for st, cnt in sorted(source_type_counts.items(), key=lambda x: -x[1]):
    print(f"  {st}: {cnt}", file=sys.stderr)

with open('/tmp/all_deduped.json','w') as f:
    json.dump(deduped, f, ensure_ascii=False, indent=2)

print(json.dumps({'total_deduped':len(deduped),'level_counts':level_counts,
                  'source_type_counts':source_type_counts,'source_counts':source_counts},
                 ensure_ascii=False))
