# 信源体系全量目录（L1-L4 / L1.5 GitHub / 黑名单 / RSSHub / 健康检查）

> 来源：`SKILL.md` （当时版本） 原文搬迁（2026-09-16 鲁班打磨，来源行号 [(144, 391), (432, 450), (1611, 1625)]）
> 本文件由 SKILL.md 原样切分，内容未做改动，仅移除已废弃的重复段落标注。

<!-- 来源 L144-L391 -->
## 信源体系（L1-L4 分层）

> **核心原则：源头质量优先 — 一手原生 RSS > 中文二手转译。** 中文 AI 媒体大量内容是英文一手源的转译重打包，直接接一手源可去掉一层信息衰减、更快、更易去重。

### 分层标准

| 层级 | 定义 | 权重 | 去重规则 |
|------|------|:----:|---------|
| **L1** | 一手官方/研究 | 最高 | 原始信号，零转译衰减 |
| **L2** | 一手独立分析 | 高 | 有判断力的深度解读，常先于中文媒体 |
| **L3** | 二手聚合/编辑 | 中 | 覆盖广但重复多，强制去重 |
| **L4** | 热榜/转译 | 低 | 多为二手转译或热度榜，仅作补漏 |

**去重铁律**：同一事件多源命中 → 保留 L1 原文 + 至多 1 条最佳 L2 解读 → 丢弃 L3/L4 重复条目。

### L1 信源（一手官方/研究）

| # | 源 | feed 地址 | 语言 | 类型 | 状态 | 备注 |
|---|-----|----------|------|------|:----:|------|
| 1 | OpenAI News | `https://openai.com/news/rss.xml` | EN | 官方 | ✅ | 模型/产品发布 |
| 2 | **阿里云** | `https://www.alibabacloud.com/blog/feed` | ZH | 官方 | ✅ | **2026-07-21 新增**。阿里系AI产品发布、百炼平台动态、企业AI基础设施，对赛道❷企业AI和赛道❸AI产业都有价值 |
| 3 | arXiv cs.AI | `https://rss.arxiv.org/rss/cs.AI` | EN | 研究 | ✅ | **必关键词过滤** |
| 4 | arXiv cs.CL | `https://rss.arxiv.org/rss/cs.CL` | EN | 研究 | ✅ | NLP/LLM，**必过滤** |
| 5 | **NVIDIA AI Blog** | `https://blogs.nvidia.com/blog/category/deep-learning/feed/` | EN | 官方 | ✅ | **2026-08-28 新增**。AI Infrastructure 核心源：AI Factory/Inference/Scale-up/Networking/Agent Infrastructure/Physical AI/Enterprise Architecture/Customer Deployment。NVIDIA 权重应较高。 |
| 6 | **AWS AI Blog** | `https://aws.amazon.com/blogs/machine-learning/feed/` | EN | 官方 | ✅ | **2026-08-28 新增**。AWS AI/ML 产品发布、Bedrock 动态、企业 AI 部署案例、SageMaker 更新。 |
| 7 | **Google/DeepMind Blog** | `https://blog.google/technology/ai/rss/` | EN | 官方 | ✅ | **2026-08-28 新增**（301→Google AI Blog）。DeepMind 研究 + Google AI 产品发布（Gemini/Gemma/GCP AI）。 |

**arXiv 关键词过滤（强制执行）**：cs.AI 单类年增 ~4.5 万条，全量订阅会淹没管道。拉取后仅保留命中以下关键词的条目：

```
agent, multi-agent, tool use, function calling, RAG, retrieval augmented, 
LLM application, autonomous, reasoning, planning, code generation,
benchmark, evaluation, alignment, safety
```

### L2 信源（深度覆盖 — 中英文分析）

| # | 源 | feed 地址 / 路由 | 语言 | 状态 | 备注 |
|---|-----|------------------|------|:----:|------|
| 1 | Simon Willison | `https://simonwillison.net/atom/everything/` | EN | ✅ | LLM/Agent 实践第一线，企业AI工具落地最有参考价值 |
| 2 | Latent Space | `https://www.latent.space/feed` | EN | ✅ | AI Engineering 深度分析，产业趋势判断力强 |
| 3 | **36氪 快讯** | RSSHub `/36kr/newsflashes` | ZH | ✅ | **升级自L4**。实时快讯，阿里系/腾讯系/字节系AI产品动态第一手 |
| 4 | **36氪 热榜** | RSSHub `/36kr/hot-list/24` | ZH | ✅ | **升级自L4**。24h热榜，AI行业热点+内容创作趋势 |
| 5 | **虎嗅** | RSSHub `/huxiu/article` | ZH | ✅ | **升级自L4**。企业/商业深度报道，产业分析有判断力 |
| 4 | **知乎 热榜** | RSSHub `/zhihu/hot` | ZH | ✅ | **升级自L4**。泛互联网热榜，消费趋势+AI话题 |
| 5 | **Product Hunt** | `https://www.producthunt.com/feed` | EN | ✅ | **2026-07-23 新增**。Atom feed，每日AI创作工具上新雷达，对赛道❶AI内容创作价值极高 |
| 6 | **TechCrunch AI** | `https://techcrunch.com/category/artificial-intelligence/feed/` | EN | ✅ | **2026-07-23 新增**。AI创作行业动态+创业公司覆盖（Runway/Anthropic等），英文权威商业科技媒体 |
| 7 | **量子位 QbitAI** | `https://www.qbitai.com/feed` | ZH | ✅ | **2026-08-06 新增**。AI产业+应用报道。官网直出RSS（实测无RSSHub路由，走原生RSS） |
| 8 | **TechCrunch M&A（并购/融资专用）** | `https://techcrunch.com/tag/mergers-and-acquisitions/feed/` | EN | ✅ | **2026-08-12 新增**。AI/科技并购、融资、品牌整合一手信源。专治资本运作类新闻漏报（8/7-8/8 漏掉 SpaceX 600亿美元收购 Cursor 母公司 Anysphere 的教训：当时只有 TechCrunch AI 分类 feed，并购新闻不在其中）。**此 feed 内容优先入赛道❸或独立资本动态条目** |

### 🔴 L1 Web Scraping 源（无 RSS — agent 定向抓取）

以下 L1 官方源**无公开 RSS feed**（已实测确认），通过 Tavily 搜索或 agent web scraping 补充：

| # | 源 | 获取方式 | 类型 | 备注 |
|---|-----|---------|------|------|
| 1 | **Anthropic** | Tavily `include_domains:["anthropic.com"]` + `/news` 页面 web_extract | 官方 | Model Release/Research/Engineering/Agent/Reasoning/Coding/Safety 核心源。权重高。 |
| 2 | **Google DeepMind** | Tavily `include_domains:["deepmind.google"]` + `/research` 页面 web_extract | 官方 | 重大研究成果、论文、模型发布。 |
| 3 | **Meta AI** | Tavily `include_domains:["ai.meta.com"]` + `/blog` 页面 web_extract | 官方 | Llama 系列、开源模型、AI 研究。 |
| 4 | **Microsoft AI / Azure AI** | Tavily `include_domains:["microsoft.com"]` + `/ai` 页面 web_extract | 官方 | Copilot/ Azure AI/ 企业 AI 部署。 |
| 5 | **Google Cloud AI** | Tavily `include_domains:["cloud.google.com"]` + AI-ML blog web_extract | 官方 | GCP AI 产品、Vertex AI、企业部署。 |

> ⚠️ **Web scraping 采集纪律**：每日从上述 5 个源各采集 1-3 条最重要的更新（不要贪多）。Tavily 每日配额 ≤3 次（basic），优先用于 Anthropic/Meta AI/DeepMind 三个最核心但最无 RSS 的源。Microsoft AI 和 Google Cloud AI 可用 web_extract 直抓。

### 🔵 信息源类型标签（v8.0 新增）

每个素材条目增加 `source_type` 字段，用于报告底部的来源说明：

| source_type | 说明 | 示例源 |
|------------|------|--------|
| `official` | 官方一手发布 | OpenAI/Anthropic/NVIDIA/阿里云 |
| `research` | 学术研究/论文 | arXiv |
| `analysis` | 独立分析/深度评论 | Simon Willison/Latent Space |
| `media_news` | 综合科技媒体报道 | TechCrunch/The Verge/The Decoder |
| `cn_media` | 中文科技媒体 | 36氪/虎嗅/IT之家/量子位/知乎 |
| `industry_case` | 企业客户案例 | 各厂商 Customer Stories |
| `business_intel` | 商业/投资情报 | Stanford AI Index/Menlo Ventures |
| `community` | 社区/开发者信号 | GitHub Trending/Hacker News |
| `weak_signal` | 弱信号/早期趋势 | 跨源综合分析 |

### 🟡 信息源优先级体系（v8.0 新增 — 防重复转述）

**统一优先级（从高到低）**：
1. 官方一手源（L1 RSS + L1 Web Scraping）
2. 高质量独立研究/分析（Simon Willison/Latent Space）
3. 专业垂直媒体（Product Hunt/TechCrunch）
4. 综合科技媒体（The Verge/The Decoder/36氪/虎嗅）
5. 热榜/社区信息（知乎/IT之家）

**去重铁律升级**：当同一事件已在 L1 官方源出现时：
- ✅ 使用 L1 官方原文作为事实底稿
- ✅ 二手媒体仅在**有独家信息/商业背景/行业分析/反方观点/中国本地化价值**时才提升权重
- ❌ 禁止同一事件经过 OpenAI→TechCrunch→The Verge→量子位→IT之家→36氪 多轮转述后在日报中形成**虚假高重要度**

### 🔶 AI 企业应用 / 产业落地信息（v8.0 新增）

**新增企业客户案例源**（无 RSS，通过 Tavily + web_extract 采集）：

| 源 | 获取方式 | 关注点 |
|----|---------|--------|
| OpenAI Customer Stories | Tavily `site:openai.com customer stories` | Production 部署、KPI/ROI |
| Anthropic Customer Stories | Tavily `site:anthropic.com customer stories` | Enterprise 安全、合规场景 |
| Microsoft Customer Stories | Tavily `site:microsoft.com AI customer stories` | Copilot/Azure AI 企业部署 |
| AWS Customer Stories | Tavily `site:aws.amazon.com generative AI customer stories` | Bedrock/SageMaker 生产部署 |
| Google Cloud AI Customer Stories | Tavily `site:cloud.google.com AI customer stories` | Vertex AI 企业应用 |
| NVIDIA Customer Stories | Tavily `site:nvidia.com customer stories` | AI Factory/推理/网络部署 |

**客户案例筛选标准**（每天 1-3 个高质量案例，宁缺毋滥）：
- 优先提取：行业→客户→业务问题→AI场景→使用模型/平台→是否Production→部署规模→KPI→效率提升→ROI
- 优先级排序：规模化Production > 已正式上线 > 有明确KPI/ROI > PoC/Pilot > 单纯合作宣布
- 特别关注行业：Government/Public Safety/Teleq/Manufacturing/Finance/Healthcare/Energy/Transportation/Enterprise Productivity
- 融入方式：根据内容性质，自动融入「企业应用」及相关重点赛道栏目（不新增独立栏目）

### 🔶 AI Business 原始信息（v8.0 新增）

| 源 | 获取方式 | 关注点 |
|----|---------|--------|
| **Stanford AI Index** | Tavily `site:hai.stanford.edu` + 年度报告 web_extract | AI Investment/Enterprise Adoption/Model Cost/Infrastructure/Policy |
| **Menlo Ventures — Enterprise AI** | Tavily `site:menlovc.com enterprise AI` | Enterprise AI Spending/Model Adoption/Application Layer/Agent |

> ⚠️ Menlo 属于投资机构，其数据和观点用于判断产业与资本方向，**不能自动视为中立事实**。涉及重要市场规模/份额/增长率时应交叉验证。

**AI Business 筛选逻辑**：
- ❌ 降低单纯"XX AI 公司完成 XX 亿美元融资"的权重
- ✅ 提高以下内容权重：企业为什么愿意为AI付钱？AI Spending流向？哪些AI产品已形成稳定商业模式？哪些Agent/Enterprise场景已有真实Adoption？AI成本下降是否打开新商业场景？
- 最终目标：增强 **AI Commercialization Intelligence**

### 🔥 资本运作类新闻收录规则（2026-08-12 新增 — 防漏报铁律）

**背景**：8/7–8/8 漏报 SpaceX 以 600 亿美元收购 Cursor 母公司 Anysphere（史上最大初创收购案）。根因：现有信源偏「功能型新闻」（模型/工具/价格），资本运作类（并购/融资/品牌整合）没有专门信源和收录权重。

**收录规则**：
1. **金额门槛**：AI/科技公司并购 ≥ $10 亿、融资轮 ≥ $1 亿、估值变化 ≥ $50 亿 → **必须收录**（无论是否属于三大赛道直接范围）
2. **信号类型**：收购/被收购、融资轮次（A-C轮+）、IPO、估值变化、品牌整合/更名、大厂分拆 → 全部纳入监控
3. **归入赛道**：默认入赛道❸（AI产业与技术动态）的 📌 最新动态；若涉及 AI 工具/创作/企业应用（如收购 Cursor/Anysphere），在对应赛道标注关联
4. **素材充足时**：资本运作类新闻允许在 🎯 今天要点 占据一条（重要性 ≥ 模型发布）
5. **跨日跟踪**：重大并购案（如 Cursor 收购）持续跟进交割进度、价格变化、团队变动，放入 📈 持续跟踪 或 推荐阅读
6. **信源补漏**：TechCrunch M&A feed 为空时，用 36氪搜索路由补漏：`/36kr/search/articles/收购`、`/36kr/search/articles/融资`、`/36kr/search/articles/IPO`

### 🔥 虎嗅内容保留规则（2026-07-23 用户明确）

用户通过3篇虎嗅公众号文章明确以下**必须保留的主题方向**：

| 主题 | 说明 | 对应赛道 |
|:----|:------|:--------:|
| 🏭 **AI商业相关** | AI行业的产品发布、技术趋势、商业落地、融资动态、企业AI战略等（不限于大会） | ❷企业AI + ❸AI产业 |
| 🌍 **社会发展变化** | AI对社会结构、就业市场、教育体系的影响 | ❷企业AI |
| 💼 **职业变化与转型** | AI导致的岗位变化、技能鸿沟、文科生转型、新职业出现 | ❷企业AI |

**执行规则**：
- 虎嗅feed（`/huxiu/article`）中命中以上三个主题的文章，**不得因与赛道关键词匹配度低而过滤**
- 即使文章标题不含「AI」「智能」「大模型」等关键字（如社会观察类），只要涉及以上三个主题，都保留
- **标题含「AI」直接保留**，不论赛道匹配度
- 如果虎嗅feed当天无数据，**额外尝试虎嗅搜索**补漏：`/huxiu/search/AI`、`/huxiu/search/职业`、`/huxiu/search/社会`
- 简报的入选优先顺序：这三个主题的内容 **优先级等同于赛道内核心信号**，不应被边缘化

### GitHub 开源趋势（一手社区信号，L1.5）

> **定位**：介于 L1（官方）和 L2（独立分析）之间。GitHub star 增长是最真实的一手信号——这是开发者在用脚投票。每日扫描，筛选与三个赛道直接相关的项目，每天每个赛道推荐1个。\n\n**获取方式**：

```bash
# 按 star 数搜索（无需认证，直接调 API）
SINCE=$(date -d'90 days ago' +%Y-%m-%d)
curl -s "https://api.github.com/search/repositories?q=AI+agent+created:%3E${SINCE}&sort=stars&per_page=20" | python3 -c "
import json,sys; data=json.load(sys.stdin)['items']
for r in data: print(f\"{r['full_name']} ⭐{r['stargazers_count']} | {r.get('description','')[:80]}\")"
```

**筛选标准（2026-08-16 更新，用户明确要求 top 级优先）**：
- **🔴 top 级优先铁律（2026-08-16 用户拍板）**：GitHub 推荐**必须优先推星数 top 级的大项目（star ≥ 10K）**，而不是同类里随便找一个新的就推。用户原话：「要优先先把 top 级的、星数多的（1万以上）的先推给我，而不是同类的里面找到了就直接揪一个过来」。**执行方式**：① 搜索时不限创建时间（或放宽到 3 年），直接 `sort=stars` 取星数最高的候选；② 每个赛道优先选 star ≥ 10K 的项目；③ 只有 top 级通道全被历史库覆盖（都推荐过了）时，才降级到「近 180 天新项目 + star ≥ 500」通道兜底。
- **特征来源**：用户点名 gc-minimal-zine-poster / scenes-gathered-zine / daily-photo-playground 三个项目，特征是：①**图片创作类**（海报/插画/设计/排版）②**较新的项目**（近半年新建）③**与内容创作直接相关**（AI 生成图像/海报）
- **⚠️ 用户点名项目 → 提取特征进搜索，禁止硬编码进推荐（2026-08-07 用户纠正）**：用户提到几个具体项目时（如海报三件套），正确做法是**提炼共同特征（类别/新旧/相关性）成为搜索方向**，**不是**把这三个 repo 硬编码成"必推清单"。曾误建 `~/.hermes/priority-repos.json` 硬编码 3 个 repo，被用户纠正「不是让它这三个特定项目放进去，是提取特征放到筛选标准」。硬编码会让推荐池固化、失去发现新项目的能力。特征 → 搜索词 → 持续发现，这条链路才是对的。
- **通道0（新增，优先）：top 级大项目** — GitHub API 搜索不限创建时间（或 `created:>3年前`），`sort=stars` 降序，每赛道候选里取 star ≥ 10K 的
- **通道1（原主通道，兜底）：近半年新项目** — `created:>180天前`（半年内新项目）+ star ≥ 500 + 与三个赛道直接相关（**特别是图片创作/内容创作类项目优先**）+ 有实质内容（不是纯列表/awesome-list）
- **周新增通道：GitHub Trending 周榜** — 抓 `https://github.com/trending?since=weekly`，覆盖"一周新增几百上千 star"的项目（2026-08-07 新增，用户要求）
- **兜底通道：GitHub Trending 每日榜** — 若 API 搜索去重后为空（历史库已覆盖），抓 `https://github.com/trending?since=daily` 每日榜单（约13个repo），排除历史库后取第一个未推荐过的
- **保证铁律：每天至少推荐 1 个**，禁止写「今日无新达标项目」——放宽窗口（90→180天→不限）、降门槛（1K→500）、换 Trending 榜，总有一个通道能出结果
- **🆕 补充通道：HelloGitHub 月刊（2026-08-16 用户指定为 AI/IT 问题优先学习源）**——`521xueweihan/HelloGitHub`（⭐171K）每月 28 日发刊（https://hellogithub.com/periodical），按语言/类别收录有趣+入门级项目。**定位**：它帮我们做「有趣」初筛，我们在这个池子里按「赛道相关性 + 真拆过真用过」二次筛选，两层互补。**用法**：每月 28 日新刊后扫当期（web_extract hellogithub.com/periodical/volume/N 或 GitHub content/HelloGitHubN.md），挑 2-3 个与三赛道相关的写入飞书推荐清单表（来源=HelloGitHub月刊），可写的进选题池。**注意**：HelloGitHub 无公开量化筛选标准、人工主编制、不唯星数（485 星也收录），其「有趣」≠ 我们「赛道相关」，不要照单全收。筛选模型详见 `references/hellogithub-sourcing.md`

**输出到简报**：精选 1-2 个项目，放入各赛道底部的 **🛠️ 项目推荐**。每个项目必须包含：项目名、⭐Stars、1 句话为什么对赛道有用、如何落地。**必须跨日去重**——跟昨日简报中出现过的 `org/repo` 不重复。

**搜索关键词调整说明**：用户当前关注❶AI内容创作❷企业AI❸AI产业。GitHub 搜索九方向（2026-08-07 扩展，按用户工作任务+生活兴趣相关度；⚠️ 实际查询已按 API 5-OR 上限精简，见下方 curl 命令为准）：
1. AI agent
2. AI coding
3. AI 内容创作（image+video generation）
4. **AI skill 类**（agent skills + claude code skills + codex skills）
4b. **AI 方法论 skill 类（2026-08-15 用户确认）**：从「5个AI方法论Skills」爆款笔记（女娲nuwa/darwin/鲁班luban/MrBeast/费曼，收藏比190%）提炼——"造Skill→进化→打磨→传播→讲清楚"生命周期类、人物视角蒸馏类（perspective skill）、REDSkill/vibecoding 生态类、方法论文案类。**用户要求：这类 skill 属于同一类且作者整理好可分享，纳入日报 GitHub 推荐**。搜索词：methodology skill + skill distillation + perspective skill + red skill + skill development
5. **skill 图片创作类**（poster+zine+illustration+creative+design+visual，从用户点名的海报项目 gc-minimal-zine-poster 等提炼）
6. **skill 视频创作/内容创作/自媒体社交类**（实际查询：video creation + video generation + social media + content creation）— 用户做自媒体运营，强相关
7. **skill 股票/财经/投资类**（stock + finance + trading + investment + market data + etf）— 用户做 A股ETF 投资，强相关
8. **趣味/生活/创意类**（fun + creative + interesting + art + toy）— 用户要求推荐好玩有意思的项目，不只围着工作转
9. **电影/娱乐/育儿/家庭生活类**（movie + cinema + entertainment + parenting + family）— 用户关注电影娱乐、育儿教育、家庭生活

### L3 信源（聚焦补充）

| # | 源 | feed 地址 | 语言 | 状态 | 备注 |
|---|-----|----------|------|:----:|------|
| 1 | **The Decoder** — AI | `https://the-decoder.com/feed/` | EN | ✅ | **2026-09-23 取代 VentureBeat**：VB 的 feed 被 Cloudflare 按客户端指纹拦（走代理也 429）、且内容停更在 8/27；The Decoder 直连可用、AI 行业媒体定位最接近（10 条/次，含融资/模型发布/行业趋势） |
| 2 | **IT之家** | `https://www.ithome.com/rss` | ZH | ✅ | 中文科技全品类，AI/Coding/消费电子。覆盖阿里/腾讯/字节AI产品发布、评测、定价等36氪未覆盖的细节。数据量大，LLM生成阶段过滤 |
| 3 | **The Verge AI** | `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml` | EN | ✅ | **2026-07-23 新增**。消费级AI新闻，覆盖AI创作工具消费者趋势，放L3做赛道①补充 |

**Hacker News 关键词流**（hnrss.org 间歇可用时的备用方案）：

| 领域 | 直接访问 | 说明 |
|------|---------|------|
| AI 应用 | `https://hn.algolia.com/api/v1/search?query=RAG&tags=story` | Algolia 搜索 API 免费，返回 JSON |
| AI创作工具 | `https://hn.algolia.com/api/v1/search?query=AI+image+generation&tags=story` | Algolia 搜索 API 免费，返回 JSON |

hnrss.org 连续 3 次失效后自动切换到 Algolia API 方案。译，中文）

| # | 源 | RSSHub 路由 | 状态 | 说明 |
|---|-----|------------|:----:|------|
| 1 | 36氪 快讯 | `/36kr/newsflashes` | ✅ | 实时快讯 |
| 2 | 36氪 热榜 | `/36kr/hot-list/24` | ✅ | 24h 热榜；噪音偏高 |
| 3 | 虎嗅 资讯 | `/huxiu/article` | ✅ | 内部 API 绕过 WAF。⚠️ **覆盖盲区**：此路由拉的是 huxiu.com 网站 feed，**不是** 虎嗅APP 微信公众号的全部内容。公众号首发/独占的文章可能在网站 feed 中遗漏（2026-07-06 实测：一篇公众号文章在 50 条 feed 中未出现，但通过 `/huxiu/search/:kw` 可搜到）。如需更完整覆盖，需配合搜索路由使用。 |
| 4 | 知乎 热榜 | `/zhihu/hot` | ✅ | 热榜 |
| 5 | 知乎 AI 话题 | `/zhihu/topic/19551275` | ⚠️待验 | 机器学习话题，质量优于热榜 |

### 中文域补充（非 RSS，现有工作流）

| # | 源 | 获取方式 | 状态 | 说明 |
|---|-----|---------|:----:|------|
| 1 | 晚点LatePost | browser_navigate 首页 | ⚠️ | 独家信源，无 RSS |
| 2 | 微信公众号(精选) | Python 直连 `mp.weixin.qq.com`（需 `__biz`） | ⚠️ | 仅预选账号增量监控 |

### 英文社区信号源（last30days + Tavily，2026-08-29 新增）

> 详细安装/配置/已知限制见 `references/last30days-tavily-integration.md`。

| 源 | 获取方式 | 覆盖 |
|---|---|---|
| Reddit | last30days keyless 模式 | 用户真实讨论/痛点 |
| Hacker News | last30days Algolia API | 技术趋势/前沿信号 |
| YouTube | Tavily API（`include_domains: youtube.com`） | 视频话题热度验证 |
| X/Twitter | Tavily API（`include_domains: x.com`） | 行业热点/争论 |

**统一调研脚本**：`python3 ~/.hermes/scripts/research_merge.py "话题" --days 7`，四平台统一时间窗口。

### 已知无 RSS 的源（黑名单，不发起抓取）

| 源 | 原因 | 替代 |
|----|------|------|
| Anthropic News | 官方已下线 RSS | 邮件订阅 / 官网定向抓取 |
| The Batch (DeepLearning.AI) | 从未提供公开 RSS | 邮件订阅 |
| Import AI (Jack Clark) | RSS 端点已 404 | 邮件订阅 |

---


<!-- 来源 L432-L450 -->
## 周期性健康检查（每周一次）

每周执行全量信源校验：

```bash
# 遍历所有 L1-L4 feed URL
for feed in "https://openai.com/news/rss.xml" \
            "https://huggingface.co/blog/feed.xml" \
            ...; do
  STATUS=$(curl -sI --max-time 10 "$feed" -o /dev/null -w '%{http_code}')
  echo "$feed → $STATUS"
done
```

- 失效源自动降级为 `inactive`
- 3 次连续失效 → 发送告警

---


<!-- 来源 L1611-L1625 -->
## RSSHub 管道（L2 中文源的统一拉取通道）

| 路由 | 用途 | 状态 |
|------|------|:----:|
| `/36kr/newsflashes` | 36氪快讯 — 实时AI/商业快讯 | ✅ |
| `/36kr/hot-list/24` | 36氪热榜 — 消费趋势+产业热点 | ✅ |
| `/huxiu/article` | 虎嗅 — 企业/商业深度 | ✅ |
| `/zhihu/hot` | 知乎热榜 — 泛互联网趋势 | ✅ |

---

## 信源健康检查（每周执行）

```bash
#!/bin/bash

<!-- 补充：来源 L392-L431（信源接入前验证 + 候选源自验流程） -->
## 信源接入前验证

> 📋 完整评估流程见 `references/rss-sources.md`（含 curl 探测命令、SPA 检测、重定向跟随、决策分流表、v8.0 实测结果记录）。

每个状态为 `⚠️待验` 的 feed，首次纳入时必须执行：

### 验证步骤

```bash
# 1. 连通性检查
STATUS=$(curl -sI --max-time 10 "<feed_url>" -o /dev/null -w '%{http_code}')
# 200 = 通过，其他 = 标记 inactive

# 2. 内容有效性检查
curl -s --max-time 10 "<feed_url>" | python3 -c "
import sys
body = sys.stdin.read()
# 检查是否为合法 RSS/Atom（含 <rss 或 <feed 标签）
if '<rss' in body[:500] or '<feed' in body[:500]:
    print('VALID')
elif 'cloudflare' in body[:500].lower() or 'captcha' in body[:500].lower():
    print('BLOCKED_WAF')
elif len(body) < 100:
    print('EMPTY')
else:
    print('UNKNOWN:', body[:200])
"
```

### 候选源自验流程

对 `RSSHub Radar 探测` 标记的源：

1. 取站点首页源码，查 `<link rel="alternate" type="application/rss+xml">`
2. 试常见路径：`/feed`、`/rss`、`/feed.xml`、`/atom.xml`
3. 查 RSSHub Radar 是否有现成路由
4. 两者皆无 → 标记 `no-feed`

---

