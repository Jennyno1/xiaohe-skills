# Ad-hoc 手动执行流程 + 触发条件原文

> 来源：`SKILL.md` （当时版本） 原文搬迁（2026-09-16 鲁班打磨，来源行号 [(13, 143)]）
> 本文件由 SKILL.md 原样切分，内容未做改动，仅移除已废弃的重复段落标注。

<!-- 来源 L13-L143 -->
## 触发条件
- 每日定时 06:00 自动执行（cron job: `daily-content-research`）
- 手动指令："今天的内容研究（报告）发一下" / "找选题" / "今日热点" / "竞品分析" / "跑今天的简报"

> ⚠️ **手动请求 vs cron 差异**：手动请求时 cron job 可能处于暂停状态。不要假设 cron 已自动生成了报告——先检查 `~/hermes-output/content-research/content-research-YYYY-MM-DD.md` 是否存在，如果不存在则按下方 💡 **Ad-hoc 执行流程** 手动跑。
>

> ⚠️ **手动测试 cron 时必须强制重新生成完整版（2026-08-20 实证，08-30 扩展为自动执行也受影响）**：如果当天的 `content-research-YYYY-MM-DD.md` 已存在，模型只输出微信摘要。验证新格式必须先删文件。🔴 **链式故障**：旧文件阻塞采集→IMA未同步→GitHub飞书表为空→项目重复，三个问题同一根因。操作见 `references/pitfalls.md`。

> 📋 **手动测试后的验证清单（2026-08-20 实证）**：
> 1. 检查 `~/hermes-output/content-research/content-research-YYYY-MM-DD.md` 时间戳和大小是否为新生成
> 2. 检查 `最大共识与分歧`模块是否出现 `## 📊` / `### 🔵` / `### 🔴` 标题
> 3. 检查引用事件是否为 `▸ 引用N：` 格式并单独分行
> 4. 检查 `/tmp/all_deduped.json` 素材总数是否 ≥30 条、来源是否 ≥3 个

## 💡 Ad-hoc 执行流程（手动请求专用）

当 cron 未运行或用户手动请求简报时，按此流程执行：

### 1. 检查现有报告
```bash
ls ~/hermes-output/content-research/content-research-$(date +%Y-%m-%d).md
```
如果存在 → **发送微信精简摘要版**（按「两版输出规范 → 二、精简版（微信推送）」模板，从完整版提炼 ~250-300 字），🔴 **禁止直接甩完整版文件内容**（2026-08-06 教训：手动补发六大模块完整版被用户纠正「微信上面我只要看摘要」）。不重新生成。
如果不存在 → 继续。

### 2. 跨日去重准备（P0 — 必须执行）
```bash
YESTERDAY=$(date -d"yesterday" +%Y-%m-%d)
cat ~/hermes-output/content-research/content-research-${YESTERDAY}.md 2>/dev/null || echo "no yesterday report"
```
> ⚠️ **昨日报告缺失回退（2026-08-15 实证）**：若 `content-research-昨日.md` 不存在（前一天 cron 漏跑），**回退到最近一份已有报告**做去重：`ls ~/hermes-output/content-research/content-research-*.md | sort | tail -1`。8/15 运行无 08-14 报告，即用 08-13 报告的话题列表去重（并把 GitHub 项目去重也基于该报告的 org/repo + recommended-repos.json 历史库）。
提取昨日简报中各赛道📌最新动态的话题列表 + ⭐GitHub推荐的org/repo + 📖推荐阅读的文章标题/URL/核心事件。
**这些话题今天禁止在同赛道重复出现，只允许在🔍洞察发现/💡落地行动写增量。⭐推荐过的org/repo禁止重复推荐。📖推荐阅读中已出现过的文章/事件也禁止重复推荐——即使换了一篇解读同一事件的文章也不行（同一事件只能推荐一次，除非有重大新进展）。**

### 3. 数据采集（同 cron 步骤 0-1）
- 检查 RSSHub 是否运行：`curl -s --max-time 5 http://localhost:12000/36kr/newsflashes | head -c 50`
- 拉取所有 L1-L4 feed XML（同 cron 中的 curl 命令，分多个 `terminal()` 调用并行执行）
- 运行 `python3 ~/.hermes/skills/digital-twin/content-research/scripts/parse_all_feeds.py`

### 4. 素材审查与热点补漏（同步骤 7）
- 检查 `/tmp/all_deduped.json` 的内容
- 用 RSSHub 36氪搜索补漏关键词：GPT-5.6 / 具身智能 / Agent 等
- **扫描 36氪热榜条目**：从中提取消费趋势/硬件热卖等潜在的 🛒 选品信号（如"语音输入戒指 OASIS 走红"这类可进选品快照的信号）

### 5. 报告生成（⚠️ 优先用 pro 模型）
内容研究报告是复杂数据合成任务，**优先用 PRO 模型（`~/.hermes/models.yaml → text.pro`）生成**。flash 模型在长文结构化输出时易跳过强制章节。三种方式：

**方式 A — delegate_task（推荐，当前为 pro 时）**：
```python
context = f"""
昨日已覆盖话题（禁止入🔥）：[GPT-5.6定档7/7, Fable 5回归, ...]
今日素材摘要：[把 /tmp/all_deduped.json 中的高质量条目分类列举]
...格式要求，读者画像，去重规则全部传递...
"""
# delegate_task 本身无法指定模型——如果 session 已是 pro 才会走 pro
```

**方式 B — 直接编写（当前为 pro 时）**：直接按输出模板编写。

**方式 C — flash 降级（仅 ad-hoc 场景）**：如果当前 session 是 flash 且无法切到 pro（ad-hoc 即时请求），可以直接编写但必须在完成后执行强制验收：
1. 所有 🔥 新鲜事的 URL 是否完整（无省略号、无占位符）——从 `/tmp/all_deduped.json` 逐条追溯
2. 所有强制模块（🎯 + 3赛道 + 🛠️项目推荐 + 📎推荐阅读）是否都有内容，无静默跳过
3. 是否覆盖全部 3 个赛道
4. 跨日去重是否严格执行

### 6. 链接质量门（P0 — 必须执行）
报告中的所有链接必须是 **从 feed 数据提取的实际完整 URL**。禁止出现：
- `https://openai.com/index/...`（带省略号）
- `[来源名]` 代替链接
- 任何不含实际 href 的占位符

验证方法：从 `/tmp/all_deduped.json` 中提取对应条目的 `link` 字段。

### 7. 保存与推送
```bash
# 保存到输出目录
cat > ~/hermes-output/content-research/content-research-$(date +%Y-%m-%d).md

# 推送摘要到微信（只发摘要，不带 .md 文件）
```

> 🔴 **🔴 Ad-hoc 手动跑报告前必须先声明改动范围（2026-08-21 用户反馈）**：用户说「手动跑一遍」时，agent 默认会把完整报告重写（替换赛道内容、GitHub 推荐、推荐阅读、信息源），但用户预期可能只是「再生成一次」。**修改前必须先用一句话列改动清单**：
> - 「会用子代理重写 ❶❷❸ 三个赛道 + 重选 GitHub 推荐 + 重写推荐阅读 + IMA 同步 + 微信精简版，是否照办？」
> - 如果用户说「只改共识分歧」，那就只动共识/分歧，其他段落一字不改
> - 实测 2026-08-21 用户问「确认一下你其他地方没有修改吧」才意识到改了太多——下次要主动声明

### 8. ⚠️ IMA 笔记同步（强制 — 容易被遗忘的最终步骤）
报告生成并保存后，**必须执行 IMA 同步**：

```bash
SKILL_DIR="~/.hermes/skills/ima-skill"
OPTS=$(printf '{"clientId":"%s","apiKey":"%s"}' "$IMA_OPENAPI_CLIENTID" "$IMA_OPENAPI_APIKEY")
REPORT_PATH="$HOME/hermes-output/content-research/content-research-$(date +%Y-%m-%d).md"

CONTENT=$(python3 -c "
import sys
with open('$REPORT_PATH', 'rb') as f:
    data = f.read()
for enc in ['utf-8', 'gbk', 'gb2312']:
    try:
        sys.stdout.write(data.decode(enc))
        break
    except: continue
")

node "$SKILL_DIR/ima_api.cjs" "openapi/note/v1/import_doc" \
  "{\"content_format\":1,\"content\":$(echo "$CONTENT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")}" \
  "$OPTS"
```

> ⚠️ 这是容易被跳过的关键步骤。报告推送给用户后，**必须在同一轮回复中执行 IMA 同步**，不要等到下一次调用。

## 聚焦赛道（v7.0 重构）

三大赛道如下，其他全部砍掉：

| 赛道 | 覆盖范围 |
|------|---------|
| **❶ AI内容创作** | 如何利用AI产品/工具/模型/技术辅助内容创作生产流水线，包括：竞品调研、选题分析、爆款拆解、AI生图、AI生视频、AI生文案、多平台分发、数据监控、增长策略等。**不再包含电商选品/店铺运营内容**。数据源：AI工具发布动态、内容创作平台更新、多模态模型进展 |
| **❷ 企业职场AI应用赋能** | AI办公提效工具、Agent工作流、企业AI部署（阿里云百炼等）、AI自动化实操。数据源：Simon Willison、The Decoder、IT之家 |
| **❸ AI产业与技术动态** | 大模型发布（OpenAI/阿里/其他）、AI行业格局、AI基础设施、芯片/算力、前沿研究。数据源：OpenAI、阿里云、arXiv、Latent Space |

> 已删除的旧赛道：育儿教育、创业好物、家居美学 — 2026-07-03 用户决策收敛。
>
> **补充关注方向（不入赛道，仅触发事件提醒）**：
> - **具身智能/机器人** — 不单独出分析，但重大事件（IPO、融资≥$1B、政策变化）需在 📡 趋势信号 或 ⚠️ 风险提示 中提及
> - **AI 监管/合规** — 涉及 C 端 Agent 封禁、数据安全法规、出口管制等需强制加入 ⚠️ 风险提示

---

