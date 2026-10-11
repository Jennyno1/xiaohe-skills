# 网页抓取与反爬（模式 + 流水线 + 检测 + L1 源）

> 本文件由 4 份同主题文档合并而成（2026-09-17）。合并理由：抓取相关的模式、流水线、反爬检测、L1 源清单散在四份小文档里，实际使用时总是要一起看。
> 各节正文逐字保留原内容，标题处标注原始文件名，便于回溯与检索。

## 本文件包含

- 〔原 `v8-web-scraping-pattern.md`〕
- 〔原 `v8-web-scraping-pipeline.md`〕
- 〔原 `waf-detection.md`〕
- 〔原 `l1-web-scraping-sources.md`〕

---


## 〔原 `v8-web-scraping-pattern.md`〕

# v8.0 Web Scraping 执行模式

## 问题

SKILL.md 定义了无 RSS 的 L1 源（Anthropic/Meta AI/Microsoft AI/Google Cloud AI/Menlo Ventures），但 cron agent 默认只执行 RSS 拉取步骤，**不会自动执行 web scraping**。结果：规则写了但数据是 0。

## 修复：步骤 3.6 必须显式执行

在 RSS 拉取（步骤1）和 parse_all_feeds.py（步骤3）之间，必须新增步骤 3.6：

```python
# 在 agent 的 terminal 中执行（非 execute_code，cron 下被 block）
from hermes_tools import web_extract
result = web_extract(urls=[
    "https://www.anthropic.com/news",
    "https://ai.meta.com/blog/",
    "https://www.microsoft.com/en-us/microsoft-cloud/blog",
    "https://cloud.google.com/blog/products/ai-machine-learning",
    "https://www.menlovc.com/perspectives"
], char_limit=3000)
```

然后将提取结果解析并写入 `/tmp/scraped_sources.json`，格式：

```json
[
  {"title":"...","link":"https://...","pubDate":"2026-XX-XX","source":"Anthropic","level":"L1","source_type":"official","description":"一句话摘要"},
  {"title":"...","link":"https://...","pubDate":"2026-XX-XX","source":"Microsoft AI","level":"L1","source_type":"industry_case","description":"企业案例摘要"},
  ...
]
```

**source_type 映射：**
- Anthropic/Meta AI/Microsoft AI/Google Cloud AI 官方博客 → `official`
- Cognizant/loveholidays 等客户合作 → `industry_case`
- Menlo Ventures 观点文章 → `business_intel`

## parse_all_feeds.py 已支持

脚本会自动读取 `/tmp/scraped_sources.json`（如果存在）。文件不存在时静默跳过。

## 已知问题

- **Meta AI** (`ai.meta.com/blog/`) 可能被 WAF 拦截（2026-08-28 实测被 block）。失败时跳过继续。
- **web_extract** 在 cron 子代理中可用，但 `execute_code` 被 block。必须用 `terminal` 或 `web_extract` 工具。

## GitHub API 限流回退

GitHub REST API 匿名限额 60 次/小时，cron 中频繁调用容易触发 403。

**回退方案：使用 shields.io 徽章接口验证 star 数**

```bash
# shields.io 不受 GitHub API 限流影响
curl -s "https://img.shields.io/github/stars/microsoft/autogen.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['value'])"
```

返回格式：`{"label":"stars","message":"61k","color":"blue",...}`，`message` 字段即 star 数。

**如果带 GH_TOKEN 也 401**：token 过期，去掉 Authorization 头用匿名请求 + shields.io 兜底。


---


## 〔原 `v8-web-scraping-pipeline.md`〕

# v8.0 Web Scraping 管道模式（2026-08-29 实证）

## 核心教训

**SKILL.md 写了规则 ≠ 管道会执行。** v8.0 初版在 SKILL.md 中定义了 Anthropic/Meta AI/Microsoft AI/Google Cloud AI/Menlo Ventures 五个 web scraping 源，但 parse_all_feeds.py 和执行流程中没有任何对应的采集命令。结果：这 5 个源在实际日报中出现 0 条。

## 正确模式

### 1. 采集层（执行步骤 3.6）

用 `web_extract` 定向抓取无 RSS 的 L1 源页面，提取标题/链接/摘要，写入 `/tmp/scraped_sources.json`：

```python
from hermes_tools import web_extract
result = web_extract(urls=[
    "https://www.anthropic.com/news",
    "https://ai.meta.com/blog/",
    "https://www.microsoft.com/en-us/microsoft-cloud/blog",
    "https://cloud.google.com/blog/products/ai-machine-learning",
    "https://www.menlovc.com/perspectives"
], char_limit=3000)
```

### 2. 数据层（parse_all_feeds.py）

脚本末尾自动读取 `/tmp/scraped_sources.json`（如存在），将条目追加到素材池：

```python
try:
    with open('/tmp/scraped_sources.json') as f:
        scraped = json.load(f)
    for item in scraped:
        results.append(item)
except FileNotFoundError:
    pass  # 静默跳过
```

### 3. JSON 格式要求

每个条目必须包含：`title`, `link`, `pubDate`, `source`, `level`, `source_type`, `description`

`source_type` 映射：
- Anthropic/Meta AI/Microsoft AI/Google Cloud AI → `official`
- 客户案例（Cognizant/loveholidays 等）→ `industry_case`
- Menlo Ventures → `business_intel`

### 4. 实测数据（2026-08-29）

| 源 | 条目数 | source_type | 关键内容 |
|----|--------|-------------|---------|
| Anthropic | 7 | official + industry_case | Claude Opus 5/Sonnet 5, text watermark, open-weights, Cognizant 合作 |
| Microsoft AI | 3 | official + industry_case | Agent Confidence Index, Agentic AI plant ops |
| Google Cloud AI | 4 | official + industry_case | Gemini Enterprise, FinOps for AI, Legal/Financial 版 |
| Menlo Ventures | 5 | business_intel | $37B GenAI 支出, Healthcare AI, Consumer AI |

## 已知限制

- Meta AI (`ai.meta.com/blog/`) 被 WAF 拦截（实测 8/28 返回空内容），需跳过
- web_extract 提取的是页面文本，不是结构化 RSS——需要 agent 从文本中识别最新条目
- 每个源取 2-5 条最重要的（不要贪多）
- scraped_sources.json 是临时文件，每次执行需重新生成


---


## 〔原 `waf-detection.md`〕

# WAF 拦截诊断与 bypass 检测清单

## 快速判断 WAF 类型

当 `curl` 返回 HTTP 200 但响应不是预期内容时，检查 body：

### 阿里云 WAF
```bash
curl -s https://target.com | head -5
```
关键特征：
- `<meta name="aliyun_waf_aa" content="...">`
- `<meta name="aliyun_waf_bb" content="...">`
- JavaScript 中引用 `//o.alicdn.com/captcha-frontend/aliyunCaptcha/`
- 页面标题为空 `<title></title>`
- TraceID 格式：`2f5e3b8017825...`

### Cloudflare
```bash
curl -sI https://target.com
```
关键特征：
- HTTP 403 + `cf-ray:` 响应头
- `<title>Just a moment...</title>` 的 Challenge 页面
- `cf-chl-*` cookies

## 标准 bypass 检测流程（按优先级）

对每个被拦截的站点，按顺序尝试：

```bash
# 1. 直连（基线）
curl -s -o /dev/null -w "HTTP %{http_code} Time: %{time_total}s\n" --max-time 10 https://target.com

# 2. 检查响应体
curl -s --max-time 10 https://target.com | head -3

# 3. SOCKS5 代理
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 10 --socks5 127.0.0.1:10808 https://target.com

# 4. RSS/XML feed
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 10 https://target.com/rss/0.xml

# 5. API 端点（JSON Accept header）
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 10 https://target.com/article -H "Accept: application/json"

# 6. 移动版
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 10 https://m.target.com

# 7. 百度缓存
curl -s --max-time 10 "https://m.baidu.com/s?word=site:target.com+关键词" | grep -oP 'target\.com[^"<>\s]+'
```

## 已知被 WAF 拦截的站点

| 站点 | WAF 类型 | 所有 bypass 路径 | 最终方案 |
|------|---------|-----------------|---------|
| huxiu.com | 阿里云 WAF | curl/browser/SOCKS5/RSS/API 全部不可达 | ⚠️ 新增：RSSHub 路由通过内部 API（`search-api.huxiu.com` + POST 签名）可绕过。优先使用 RSSHub `/huxiu/search/:keyword` 获取结构化内容（待部署验证）。兜底：36kr站内搜索转载 + 百度 site:huxiu.com 摘要（标C级） |
| baidu.com (PC版) | 自研反爬 | PC版触发验证码 | 使用移动版 m.baidu.com |
| weixin.sogou.com（文章页） | 自研反爬 | 搜索页可访问，文章详情页 captcha | 仅用搜索摘要，不点文章详情 |

## 原则

1. **不要浪费时间硬刚 WAF**：curl/browser/SOCKS5/RSS/API 四条路全试过还不行就放弃直连
2. **优先使用转载/聚合源**：36kr、百度搜索、Google 缓存等
3. **标注数据质量**：代理源获取的数据标 `[待验证]` 或 C 级，不做选题唯一依据
4. **记录到本文件**：发现新的被拦截站点时更新上表


---


## 〔原 `l1-web-scraping-sources.md`〕

# L1 Web Scraping 源配置（（当时版本））

> 无 RSS 的一手官方源。**2026-10-08 已从「agent 每天用 web_extract 抓」迁到脚本层**（见下）。

## 🔴 实现状态（2026-10-08 实测）

**执行方式**：`~/.hermes/scripts/scrape_l1_sources.py`，由 `collect_daily_feeds.sh` 步骤 3.7 调用，
产出 `/tmp/scraped_sources.json`（parse_all_feeds.py 自动合并）+ `/tmp/l1_scrape_status.json`（供健康检查）。
**不再依赖 agent 调用 web_extract**——原设计如此（见本文档下方「原执行模式」），但两度证伪：
① 2026-08-28 agent 默认不执行该步骤，数据为 0；② 2026-10-08 agent 联网工具全开撞出 50 次搜索死循环，
整轮日报报废。**结论：无 RSS 源的采集必须落在脚本里，规则写在文档里不算执行层。**

| 源 | 状态 | 方式 / 原因 |
|---|---|---|
| **Anthropic** | ✅ 已接入 | 抓 `/news` 列表页（`<a href="/news/<slug>">` + `<h4>` 标题），每轮 3 条 |
| **腾讯云 ADP** | ✅ 已接入 | 抓 `/zh/blog/<slug>`（需浏览器兜底），每轮 3 条 |
| **DeepSeek** | ✅ 已接入 | 抓 `/news/newsYYMMDD`（日期就在 slug 里，标题去目标页取），每轮 3 条 |
| **Microsoft AI / Azure** | ✅ 已接入（不是抓取！） | 🔎 **它其实是 WordPress，有 RSS**：`https://www.microsoft.com/en-us/microsoft-cloud/blog/feed/`——当普通 RSS 源挂进采集脚本即可 |
| Meta AI | 🚧 未接入 | WAF 拦截（curl 空响应、浏览器超时） |
| Google Cloud AI | 🚧 未接入 | curl 与浏览器均不通（机房 IP 被拦） |
| Menlo Ventures | 🚧 未接入 | Cloudflare 403，浏览器亦被拒 |
| 字节 Seed | 🚧 未接入 | 列表异步渲染，HTML 内无文章数据（需找其接口） |

未接入的 4 个在健康检查里显示 `🚧（未接入：原因）`——**不算故障、不报警**，但不能当已覆盖；
哪天要补，优先试「找隐藏 feed / sitemap」再考虑写抓取规则（Microsoft 就是这么发现不用抓的）。

**维护要点**：
- 列表页改版 → `parse_failed:no_candidates` 会被健康检查报出来（不静默）；
- 同一链接重复（头条卡+列表卡）已在脚本内按链接去重、取标题更干净的一次；
- 标题带日期/栏目前缀（如 `Oct 6, 2026Announcements…`）由 `clean_title()` 剔除，通用词标题
（`this documentation` 等）黑名单过滤，必要时用 `headline: true` 去目标页取真标题；
- 已抓过的链接记在 `~/.hermes/cache/l1_scrape_seen.json`，**只报新文章**（列表页无日期时防重复上报）。

## 原执行模式（已废弃，仅作背景）

## 新增源（（当时版本））

| 源 | URL | 类型 | 价值 |
|---|-----|------|------|
| **腾讯云 ADP** | `https://adp.tencentcloud.com/zh/blog` | 官方 | 企业级 Agent 平台、智能体开发框架、Agent 安全治理 |
| **字节 Seed** | `https://seed.bytedance.com/blog` | 官方 | Seedream/Seedance/Seed Audio 多模态模型发布 |
| **DeepSeek API** | `https://api-docs.deepseek.com/updates` | 官方 | V4-Pro/V4-Flash 模型更新、API 定价调整 |

## 采集方式

```python
from hermes_tools import web_extract
result = web_extract(urls=[
    "https://adp.tencentcloud.com/zh/blog",
    "https://seed.bytedance.com/blog",
    "https://api-docs.deepseek.com/updates"
], char_limit=3000)
```

## source_type 映射

- 腾讯云ADP/字节Seed/DeepSeek API → `official`

## 注意事项

- 这三个源优先于英文源采集
- 每个源取 1-2 条最重要的
- 结果写入 `/tmp/scraped_sources.json`


---
