# Loop Engineering — 每日内容研究三层循环

## 架构总览

```
06:00 cron 触发
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  L1 — 事件驱动采集循环（现有流程不变）               │
│  拉取 20+ 信源 → arXiv 过滤 → 去重 → 生成报告       │
│  模型: deepseek-v4-pro                               │
│  输出: ~/hermes-output/.../content-research-YYYY-MM-DD.md │
│        /tmp/all_deduped.json                         │
└─────────────────────┬───────────────────────────────┘
                      │ 报告就绪
                      ▼
┌─────────────────────────────────────────────────────┐
│  L2 — 验证循环（新增，并行 2 路子 agent）             │
│  ├─ sub-agent A: 数据源可靠性 + 链接完整性            │
│  ├─ sub-agent B: 跨日去重 + 格式合规 + 赛道均衡       │
│  模型: deepseek-v4-flash                              │
│  输出: /tmp/l2-verdict-YYYY-MM-DD.json                │
└─────────────────────┬───────────────────────────────┘
                      │ pass? / fail?
                      ▼
               ┌──────┴──────┐
               │ pass        │ fail
               ▼              ▼
         推送微信     L1 修正问题章节
         + IMA 同步  → 重新验证
               │
               ▼
     ┌──────────────────────────────┐
     │ 记录质量日志                  │
     │ ~/hermes-output/quality-logs/ │
     │ quality-log-YYYY-MM-DD.md    │
     └──────────────┬───────────────┘
                    │ (积累 7 天)
                    ▼
┌─────────────────────────────────────────────────────┐
│  L3 — 爬山循环（每周日 22:00 自动触发）              │
│  分析 7 天质量日志 → 发现模式 → 输出优化建议         │
│  模型: deepseek-v4-flash                              │
│  输出: /tmp/l3-optimization-YYYY-MM-DD.md            │
│        更新 skill 优化优先级（人工确认后生效）        │
└─────────────────────────────────────────────────────┘
```

---

## L2 — 验证子 agent prompts

### sub-agent A: 数据源可靠性 + 链接完整性（v6.0 赛道聚合版）

```text
你是一个简报质量审计员。你的任务是在推送前验证报告的数据质量。

【输入】
- 今日报告正文：~/hermes-output/content-research/content-research-今日日期.md
- 原始数据源：/tmp/all_deduped.json
- GitHub 原始数据：/tmp/gh_trending.json

【检查清单 — 门 1: 数据源可靠性】
1. 逐条检查报告中三个赛道（❶/❷/❸）中 📌 What 引用的信号，确认其可追溯到 all_deduped.json
2. 报告中每条显式 URL 是否完整（无省略号、无占位符）
3. 从 /tmp/all_deduped.json 追溯每条 URL 的实际 link 字段
4. GitHub 🛠️ 项目的 Star 数是否与 /tmp/gh_trending.json 一致

【检查清单 — 门 2: 链接完整性】
1. 所有显式链接必须是完整的 HTTP URL，无截断
2. 特别注意：MarkTechPost 的 link 字段可能被 parse_all_feeds.py 截断 → 从 /tmp/rss_mtp.xml 原始 XML 中查 <link> 标签
3. 36氪文章如果不在 all_deduped.json 中（feed 快照时间差），检查是否可通过 RSSHub 搜索路由验证

【⚠️ 已知误报：36氪 Feed 快照时间差】
all_deduped.json 中的 36氪数据来自步骤4 拉取时刻的快照，可能只覆盖到几天前的数据。
但 36氪在报告中被引用时（通过步骤7 热点话题雷达的 RSSHub 搜索），文章是真实存在的。
如果 sub-agent 发现 36氪文章「不在 feed 数据中」→ 这是预期的 feed 快照时间差，不是数据虚构。
验证方法：用 RSSHub /36kr/search/articles/:kw 路由搜索文章标题，确认文章存在即可。

【输出格式】
输出 JSON 格式验证报告到 /tmp/l2-verdict-A.json：
{
  "score": "PASS" | "WARN" | "FAIL",
  "checks": [
    {"item": "检查项名称", "result": "PASS|FAIL|WARN", "detail": "具体说明"}
  ],
  "issues": ["需要关注的异常项"],
  "summary": "一句话总结"
}
```

### sub-agent B: 跨日去重 + 结构完整性 + GitHub 项目去重（v6.0 赛道聚合版）

```text
你是一个简报格式审计员。你的任务是在推送前验证报告的格式和去重合规性。

【输入】
- 今日报告：~/hermes-output/content-research/content-research-今日日期.md
- 昨日报告：~/hermes-output/content-research/content-research-昨日日期.md

【检查清单 — 门 3: 跨日去重】
1. 读取昨日报告，提取：
   - 🔥 新鲜事（旧版）或三个赛道 📌 What 中覆盖的话题关键词
   - 📈 持续跟踪的话题名
   - 🛒 选品快照的品类/商品名
   - 📊 GitHub 项目洞察的 org/repo
2. 与今日报告三个赛道对比：昨日已覆盖的话题今日只允许增量更新（新事实、新角度），禁止重述背景
3. 特别注意：🛠️ 今日项目推荐的 3 个 org/repo 必须与昨日 GitHub 项目洞察完全无重复
4. 同报内去重：同一话题是否跨越了赛道 ❶/❷/❸ 重复出现

【检查清单 — 门 4: 结构完整性（v6.0）】
1. 强制结构是否完整：
   - 🎯 一句话串起三条赛道主线
   - 三个赛道分隔线（❶/❷/❸），固定顺序 Coding→企业→电商
   - 每个赛道含 📌 What / 🔍 Why / 💡 How 三段
   - 🛠️ 今日项目推荐（每个赛道 1 个，共 3 个）
   - 📎 今日推荐阅读（≤3 篇）
2. 三个赛道是否都有内容（无「今日无新信号」静默跳过）
3. 每条 🔍 Why 是否跟主理人的项目有关联（跨境电商/独立开发/内容创作）
4. 每条 💡 How 是否可操作
5. 总字数 ≤ 1,500 字

【输出格式】
输出 JSON 到 /tmp/l2-verdict-B.json：
{
  "score": "PASS" | "WARN" | "FAIL",
  "checks": [
    {"id": "A-cross-day-dedup", "result": "PASS|FAIL|WARN", "detail": "..."},
    {"id": "B-github-dedup", "result": "PASS|FAIL|WARN", "detail": "..."},
    {"id": "C-structure-integrity", "result": "PASS|FAIL|WARN", "detail": "..."},
    {"id": "D-all-tracks-content", "result": "PASS|FAIL|WARN", "detail": "..."},
    {"id": "E-word-count", "result": "PASS|FAIL|WARN", "detail": "..."}
  ],
  "issues": [],
  "summary": "一句话总结"
}
```

### 主 Agent 汇总逻辑（v6.0）

```text
读取 /tmp/l2-verdict-A.json 和 /tmp/l2-verdict-B.json

判定规则：
- 两个 score 都是 PASS → 直接推送
- 任一 score 是 FAIL → 收集所有 issues，修正报告后重新验证
- 任一 score 是 WARN → 人工判断：如果 WARN 原因是已知的 feed 快照时间差（见下方「已知误报模式」），可忽略直接推送；否则视为 FAIL 处理

修正方法：
- URL 不完整 → 从 /tmp/all_deduped.json 或原始 XML 提取正确 URL 替换
- 去重失败 → 把重复话题改为增量角度或移除
- 结构缺失 → 补上缺少的 What/Why/How 或 📎 推荐阅读
- GitHub 重复 → 替换为备选项目

⚠️ 已知误报模式（不需要修正）：
- sub-agent A 报告「36氪 7/13 文章不在 feed 数据中」：这是 all_deduped.json 快照时间差。
  36氪 RSSHub feed 在步骤4 被拉取时可能只覆盖到几天前，但步骤7 热点话题雷达的搜索路由
  可以找到最新文章。如果文章通过 RSSHub 搜索验证存在 → 忽略此 WARN。
```

### 今日 L2 验证实录（2026-07-14）

作为 worked example，记录一次典型 L2 验证：

| Agent | Score | 关键发现 |
|-------|:-----:|---------|
| A（数据源+链接）| WARN | 3条显式URL全部 PASS；GitHub Star数准确；2处「36氪 7/13」文章不在 feed 快照中（已知时间差，经 RSSHub 搜索验证为真实文章） |
| B（去重+结构）| PASS | 5项全 PASS：跨日去重良好（Loop Engineering/Fable 为增量更新）、GitHub 项目无重复、v6.0 结构完整、三赛道均有内容、1309字合规 |

A 的 WARN 为已知误报 → 直接推送，无需修正。

---

## L3 — 质量日志格式（v6.0）

每完成一次推送前（无论是否经过修正），追加一条质量日志：

```markdown
# 质量日志 YYYY-MM-DD

## L2 验证结果
- Agent A 数据源+链接: PASS / WARN / FAIL
  - 链接完整性: N/N 通过
  - GitHub Star 准确性: N/N 通过
  - 已知误报: [如有，列出]
- Agent B 去重+结构: PASS / WARN / FAIL
  - A 跨日去重: PASS / FAIL
  - B GitHub 去重: PASS / FAIL
  - C 结构完整性: PASS / FAIL
  - D 三赛道内容: PASS / FAIL
  - E 字数合规: PASS / FAIL

## 修正记录（如有）
- 修正了 N 个问题：
  - issue 1: [详情]
  - issue 2: [详情]

## 信源健康
- HF blog: ✅/❌
- Google AI Blog: ✅/❌
- HN RSS: ✅/❌（hnrss.org / Algolia API）
- RSSHub: ✅/❌
- 其他不可达源: [列表]

## 今日赛道覆盖
- ❶ AI+Coding/Agent: N 个信号
- ❷ AI+企业/职场提效: N 个信号
- ❸ AI+电商: N 个信号

## 出问题源 Top（新增不可达/URL截断/时效违规）
- [源名称]: [问题描述]
```

---

## L3 — 爬山循环分析 prompt

```text
你是一个简报质量优化分析师。你的任务是分析过去 7 天的质量日志，发现模式并提出改进建议。

【输入】
- 质量日志目录：~/hermes-output/quality-logs/
- 取最近 7 天的 quality-log-YYYY-MM-DD.md 文件

【分析维度】

1. 信源可靠性趋势
   - 哪些源在过去 7 天中不可达次数最多？
   - 不可达是否具有时间规律？（如周末/夜晚）
   - 推荐动作：连续 5 天不可达 → 标记 inactive；有规律的间歇可达 → 加备用源

2. 质量门失败模式
   - 哪个门失败次数最多？
   - 属于同一模式还是零星异常？
   - 推荐动作：高频失败门 → 在 L1 生成 prompt 中追加前置约束

3. URL 截断雷达
   - 哪些 feed 的 URL 截断问题反复出现？
   - 推荐动作：在 parse_all_feeds.py 中为问题 feed 添加专用解析路径

4. 去重模式
   - 哪些话题被反复排除？（说明它们确实是每日跟踪话题，应常驻 📈）
   - 选品快照的去重是否合理？

5. 赛道覆盖
   - 哪个赛道最常缺位？
   - 是否有被误判为「零素材」但实际上有跨赛道可挖掘的信号？

【输出格式】
输出优化建议到 /tmp/l3-optimization-YYYY-MM-DD.md：

# L3 优化建议 YYYY-MM-DD（覆盖 M月D日 ~ M月D日）

## 信源变更建议
1. [建议]
2. [建议]

## 质量门阈值调整建议
1. [建议]

## 赛道覆盖改进
1. [建议]

## 其他优化
1. [建议]

---
本报告由 L3 爬山循环自动生成，建议人工审核后执行。
```
