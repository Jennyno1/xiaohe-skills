# RSS / RSSHub 信源与校验

> 本文件由 3 份同主题文档合并而成（2026-09-17）。合并理由：信源发现、校验流程、RSSHub 路由本是一条链上的三件事，分成三份后经常只找到其中一步。
> 各节正文逐字保留原内容，标题处标注原始文件名，便于回溯与检索。

## 本文件包含

- 〔原 `rss-feed-discovery.md`〕
- 〔原 `rss-feed-verification-procedure.md`〕
- 〔原 `rsshub-routes.md`〕

---


## 〔原 `rss-feed-discovery.md`〕

# RSS Feed Discovery 方法论

> 记录于 2026-07-08 电商/AI企业新源验证过程。

## 验证流程

### 1. 候选源收集

**电商类关键词**：`ecommerce blog RSS`, `跨境 行业 网站 RSS`, `Amazon seller blog feed`, `Shopify blog RSS`

**AI企业落地类关键词**：`enterprise AI blog RSS`, `AI business feed`, `企业AI 落地 RSS`

### 2. 连通性测试

```bash
curl -sI --max-time 8 "$URL" -o /dev/null -w '%{http_code}'
```

结果解读：
- **200** → 直接可用 ✅
- **301/302/308** → 有跳转，加 `-L` 跟过去
- **403** → WAF 拦截 ❌（白鲸出海、亿邦动力）
- **404** → 路径错误，尝试 `/feed` `/rss` `/feed.xml` `/atom.xml`
- **410** → 已下线 ❌（微软 AI Blog 旧路径）
- **000** → DNS/连接超时 ❌

### 3. 内容有效性验证

```bash
curl -sL --max-time 10 "$URL" | python3 -c "
import sys, xml.etree.ElementTree as ET
try:
    tree = ET.parse(sys.stdin)
    root = tree.getroot()
    items = root.findall('.//item')
    print(f'Valid RSS: {len(items)} items')
    for i in items[:3]:
        print(f'  • {i.findtext(\"title\",\"\")[:80]}')
except Exception as e:
    print(f'Error: {e}')
"
```

### 4. 常见路径枚举

对无弹窗的站点，按以下顺序试探：

```
/feed
/rss
/rss.xml
/feed.xml
/atom.xml
/blog/feed
/blog/feed.xml
/blog.rss
/blog/atom.xml
/community/feed
```

### 5. L 层级判定标准

| 层级 | 标准 | 示例 |
|------|------|------|
| **L1** | 官方一手，企业/研究机构直接运营 | OpenAI, AWS AI Blog |
| **L2** | 独立分析/垂直媒体，有原创判断 | Practical Ecommerce, Digital Commerce 360 |
| **L3** | 二手聚合/工具公司博客 | Jungle Scout, AI News, VentureBeat AI |

### 6. 2026-07-08 实测结果

#### 电商（4个新增可用）

| 源 | RSS | HTTP | 层级 |
|----|-----|:----:|:----:|
| Practical Ecommerce | `https://www.practicalecommerce.com/feed` | 200 | L2 |
| Digital Commerce 360 | `https://www.digitalcommerce360.com/feed` | 301→200 | L2 |
| Jungle Scout Blog | `https://www.junglescout.com/blog/feed/` | 200 | L3 |
| 雨果跨境 | `https://www.cifnews.com/rss` | 200 | L3 |

#### AI企业落地（3个新增可用）

| 源 | RSS | HTTP | 层级 |
|----|-----|:----:|:----:|
| AI News | `https://www.artificialintelligence-news.com/feed/` | 200 | L3 |
| VentureBeat AI | `https://venturebeat.com/category/ai/feed/` | 308→200 | L3 |
| AWS AI Blog | `https://aws.amazon.com/blogs/ai/feed/` | 301→200 | L1 |

#### 确认不可用

| 源 | 原因 |
|----|------|
| 白鲸出海 (baijing.cn) | WAF 拦截 403 |
| 亿邦动力 (ebrun.com) | WAF 拦截 403 |
| Shopify Blog | 无公开 RSS（所有常见路径均 404） |
| 机器之心 (jiqizhixin.com) | RSS 返回 HTML 非标准 XML |
| 量子位 (qbitai.com) | 403 拦截 |
| AI Business (aibusiness.com) | 403 拦截 |
| McKinsey AI | 无有效 RSS |
| Anthropic Blog | 官方已下架 RSS（已知） |

### 7. 注意事项

- 国内电商站（亿邦动力、联商网）多被 WAF 挡住，可能需要代理或 RSSHub
- Shopify/BigCommerce 等 SaaS 平台通常不提供公开 RSS，需用替代方案（如 Jina Reader 抓取）
- IT之家 RSS 返回 60 条/天，覆盖源广但噪音高，需 LLM 过滤
- 301 跳转的 feed 在 `parse_all_feeds.py` 的 `extract_items()` 中能正常解析（`curl -L` 已跟跳转）


---


## 〔原 `rss-feed-verification-procedure.md`〕

# RSS Feed 可用性评估流程

> 评估新信息源是否可通过 RSS 接入内容管道的标准操作流程。
> v8.0 从 session 2026-08-28 实测总结。

## Step 1: RSS/Atom 连通性探测

```bash
# HTTP 状态码检查（200=连通）
STATUS=$(curl -sI --max-time 10 "<feed_url>" -o /dev/null -w '%{http_code}')
```

仅 HTTP 200 不够 —— 现代 SPA 站点返回 200 但内容是 HTML。需要 Step 2。

## Step 2: 内容有效性检查

```bash
curl -s --max-time 10 "<feed_url>" | head -c 200
# 看是否以以下开头：
# ✅ <?xml  → 有效 RSS/Atom
# ✅ <rss   → 有效 RSS
# ✅ <feed  → 有效 Atom
# ❌ <!doctype  → SPA HTML，不是 RSS
# ❌ <!DOCTYPE html  → SPA HTML
```

## Step 3: 常见替代路径探测

官方 RSS feed 通常在以下路径之一：

```bash
for path in /feed /rss /feed.xml /atom.xml /rss.xml /blog/feed /blog/rss; do
  curl -sI --max-time 10 "https://example.com$path" -o /dev/null -w '%{http_code}' 2>/dev/null
  echo " $path"
done
```

## Step 4: 跟随重定向检查

某些 URL 返回 301/302 重定向。需要用 `-L` 跟随到最终目标：

```bash
curl -sI --max-time 10 -L "<feed_url>" -o /dev/null -w '%{http_code}'
```

如果重定向到有效 RSS → 加入管道。
如果重定向到 SPA HTML → 标记为不可用。

## 决策分流

| 检测结果 | 分流 | 处理方式 |
|---------|------|---------|
| ✅ 有效 RSS/Atom（`<?xml` 开头） | RSS 拉取 | curl → parse_all_feeds.py |
| ❌ 404 / 410 / 连接超时 | 不可用 | 标记 `no-RSS`，备选方案 |
| ❌ SPA HTML（`<!doctype` 开头） | Web Scraping | Tavily + web_extract 补漏 |
| ⚠️ 301 重定向 | 需验证 | `-L` 跟随，检查最终目标 |

## 实测结果记录（2026-08-28）

| 源 | URL | HTTP | 内容 | 决策 |
|---|-----|------|------|------|
| NVIDIA AI Blog | `blogs.nvidia.com/blog/category/deep-learning/feed/` | 200 | XML ✅ | RSS 拉取 |
| AWS AI Blog | `aws.amazon.com/blogs/machine-learning/feed/` | 200 | XML ✅ | RSS 拉取 |
| Google/DeepMind | `blog.google/technology/ai/rss/` | 301→200 | XML ✅ | RSS 拉取（需 -L） |
| Anthropic | `anthropic.com/rss.xml` / `/feed.xml` / `/rss` | 404 | — | Web Scraping |
| Meta AI | `ai.meta.com/blog/rss/` / `/feed/` | 404 | — | Web Scraping |
| Microsoft AI | `blogs.microsoft.com/ai/feed/` | 410 | — | Web Scraping |
| Google Cloud AI | `cloud.google.com/blog/products/ai-machine-learning/rss` | 200 | HTML SPA | Web Scraping |
| Stanford HAI | `hai.stanford.edu/news/rss.xml` | 200 | HTML SPA | Web Scraping |
| Menlo Ventures | `menlovc.com/feed` | 301 | — | Web Scraping |


---


## 〔原 `rsshub-routes.md`〕

# RSSHub 路由清单（内容研究相关）

> 数据获取时间：2026-06-27，通过 `curl -s "https://api.github.com/repos/DIYgod/RSSHub"` API 获取。

RSSHub 可将以下信息源转为结构化 RSS feed，格式统一（标题+时间+摘要+链接），适合定时拉取入库。

## 内容研究核心信息源路由

| 信息源 | 路由数 | 关键路由 | 备注 |
|--------|--------|----------|------|
| 36氪 | 4 | `/36kr/:category/:subCategory?/:keyword?` | 支持搜索文章 `/36kr/search/articles/关键词`、快讯 `/36kr/newsflashes` |
| 虎嗅 | 9 | `/huxiu/article`、`/huxiu/search/:keyword`、`/huxiu/channel/:id` | ⚠️ 使用内部 API（`search-api.huxiu.com` + POST 签名），绕过前端阿里云 WAF。路由标记 `antiCrawler: true` |
| 知乎 | 17 | `/zhihu/daily`、`/zhihu/hot`、`/zhihu/column/:id` | |
| 微博 | 9 | `/weibo/user/:uid`、`/weibo/keyword/:keyword` | |
| 华尔街见闻 | 4 | `/wallstreetcn/` 相关路由 | |
| 格隆汇 | 7 | `/gelonghui/` 相关路由 | |
| 雪球 | 12 | `/xueqiu/` 相关路由 | |

## AI/技术相关路由

| 信息源 | 路由 | 备注 |
|--------|------|------|
| OpenAI | `/openai/blog` | 官方博客 |
| DeepSeek | `/deepseek/blog` | 官方博客 |
| Anthropic/Claude | `/claude/blog` | 官方博客 |
| GitHub | `/github/trending` | |
| Product Hunt | `/producthunt/` | |
| Hacker News | `/hackernews/` | |

## 部署方式

```bash
# 公共实例（无需部署）
curl -s "https://rsshub.app/36kr/newsflashes"

# 自部署（推荐）
docker pull diygod/rsshub
docker run -d --name rsshub -p 1200:1200 diygod/rsshub
```

自部署后可配置更多路由参数（如频率、代理、认证 Cookie）。

## 已知限制

- **百度的 route 不存在**（截至 2026-06-27）
- **虎嗅路由使用内部 API**，公共实例不可用（需自部署后配置认证）

## 相关项目

- **Folo**（原 Follow）：AI RSS 阅读器，与 RSSHub 配对使用
  - 仓库：https://github.com/RSSNext/Folo
  - 支持 AI 发现、筛选、阅读工作流
- **RSSHub Radar**：浏览器扩展，快速发现当前网站的 RSS/RSSHub 订阅
  - 仓库：https://github.com/DIYgod/RSSHub-Radar


---
