# 工具库 / Weak Signals 框架 / 格式输出管线

> 来源：`SKILL.md` v8.3.0 原文搬迁（2026-09-16 鲁班打磨，来源行号 [(1594, 1610), (1626, 1756)]）
> 本文件由 SKILL.md 原样切分，内容未做改动，仅移除已废弃的重复段落标注。

<!-- 来源 L1594-L1610 -->
## AI 内容创作图像工具库（2026-07-08 整理）

以下 GitHub 项目直接服务于 AI 内容创作的图像制作流程：

| 工具 | ⭐ | 用途 | 工作流阶段 |
|:----|:--:|:----|:---------:|
| rembg | 23.6K | 商品图去背景 | 预处理 |
| ComfyUI | 119.7K | 节点式生图工作流 | 场景生成 |
| Fooocus | 50.7K | 最易用的 SD 界面 | 场景生成 |
| ControlNet | 33.9K | 控制生图构图/边缘 | 场景控制 |
| IP-Adapter（腾讯） | 6.6K | 以图生图，商品特征换背景 | 场景合成 |
| SAM / SAM2 | 54.4K/19.4K | 商品分割/抠图 | 预处理 |
| palxiao/poster-design | 4.7K | 国产海报编辑器，电商封面 | 封面排版 |

---


<!-- 来源 L1626-L1756 -->
# 每周六凌晨 03:00 执行全量信源校验

FEEDS=(
  "https://openai.com/news/rss.xml"
  "https://huggingface.co/blog/feed.xml"
  "https://blog.google/technology/ai/rss/"
  "https://rss.arxiv.org/rss/cs.AI"
  "https://simonwillison.net/atom/everything/"
  "https://www.latent.space/feed"
  "https://magazine.sebastianraschka.com/feed"
  "https://thegradient.pub/rss/"
  "https://www.marktechpost.com/feed/"
  "https://www.technologyreview.com/topic/artificial-intelligence/feed/"
  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"
)

for feed in "${FEEDS[@]}"; do
  STATUS=$(curl -sI --max-time 10 "$feed" -o /dev/null -w '%{http_code}' 2>/dev/null)
  if [ "$STATUS" != "200" ]; then
    echo "⚠️ $feed → $STATUS"
  else
    echo "✅ $feed"
  fi
done
```

---

- **`references/engineering-patterns.md`**：防规则漂移模式 — 任何「禁止 X」类软规则被 LLM 反复违背时的四件套升级方案（结构性隔离 + 反例锚点 + 正例锚点 + 自检命令 + 硬失败判定）。适用范围超出共识/分歧，涵盖所有「禁止 X」类规则。新增/修改规则时按本文件的验收清单逐项打勾。2026-08-21 共识/分歧段落事件罗列漂移修复即按此模式落地；另见同文件节：单点收拢架构。

- **`references/rss-sources.md`**：RSS feed 验证方法论 + 2026-07-08 实测结果（电商/AI企业新源验证记录）
- **`references/loop-engineering.md`**：每日简报 L1-L3 三层循环设计（L2 验证子 agent prompts + L3 爬山循环分析逻辑）。2026-07-13 新增。
- **`references/post-report-verification.md`**：报告发布后 L2 独立验证流程（URL 完整性检查、GitHub Star 数 API 验证、all_deduped.json 交叉追溯、36氪 feed 数据滞后坑位）。2026-07-14 新增。
## 格式输出管线（2026-08-25 新增 — 组件化架构）

> **核心原则：LLM 只管生成内容，格式由脚本控制。** 用户明确要求：不要依赖 LLM 遵守格式规则（会漂移），而是用脚本保证输出格式一致。

### 架构

```
LLM 生成原始内容（JSON/结构化文本）
        ↓
format_report.py（待建）读取原始内容 + daily-briefing-rules.md
        ↓
按规则组装最终 markdown（链接/排版/字数全由脚本控制）
        ↓
daily-briefing-check.py 校验（安全网）
        ↓
推送
```

### 已有文件

| 文件 | 路径 | 用途 |
|------|------|------|
| **格式规范** | `~/.hermes/scripts/daily-briefing-rules.md` | 所有输出格式规则的权威源（链接/引用/排版/字数），含正反例 |
| **格式校验** | `~/.hermes/scripts/daily-briefing-check.py` | 统一校验脚本，覆盖链接/引用/结构/共识/分行/字数 6 类规则。替代零散的 consensus_check.py |

### 待建

- `format_report.py` — 格式化脚本，读取 LLM 原始输出 + rules.md，组装最终报告

### 执行规则

1. **生成前**：读 `daily-briefing-rules.md`（或让子代理读）作为格式参考
2. **生成后**：推送前必跑 `python3 ~/.hermes/scripts/daily-briefing-check.py --report <path>`
3. 退出码 `0` = 合规可交付；`1` = 违规须修正；`2` = 文件错误
4. 违规时可尝试 `--fix` 自动修复（链接移除等），修复后重跑校验

> ⚠️ `consensus_check.py` 的功能已合并进 `daily-briefing-check.py`，新流程统一用后者。旧脚本保留但不再作为独立校验入口。

> ⚠️ **🔥 check脚本/规则文件双路径陷阱（2026-08-28 实证）**：修改 `daily-briefing-check.py` 或 `daily-briefing-rules.md` 时，必须同步更新**三处副本**，否则cron执行用的是旧版：
> 1. `~/.hermes/scripts/daily-briefing-check.py`（**cron实际调用的**）
> 2. `~/hermes-kb/scripts/daily-briefing-check.py`（知识库归档副本）
> 3. `~/.hermes/skills/digital-twin/content-research/scripts/daily-briefing-check.py`（skill副本）
> 三条路径是独立文件（非软链接），改一处不会自动同步。2026-08-28 实证：hermes-kb 副本改了但 `~/.hermes/scripts/` 没改，cron仍按旧的800字上限执行。**修改后务必逐路径 grep 验证**。

---

## 🔶 Weak Signals 分析框架（v8.0 新增 — 底层分析能力，非新栏目）

> **核心原则**：Weak Signals 不是新栏目，是底层分析机制，融入现有 🎯今天要点 / 各赛道 📌🔍 / 🔵共识解读 / 📖推荐阅读。

### Weak Signal 定义

尚未成为主流新闻或行业共识，但已从一手信息/研究人员/开发者/创业者/HN/Reddit/X 等渠道出现，可能预示未来 3-12 个月技术、产品或产业变化的信号。

### 寻找方向
- 多个核心研究人员突然开始讨论同一方向
- 新技术术语快速出现
- 某类 Agent/AI 产品突然受到开发者关注
- 企业 AI 使用方式出现变化
- AI 推理成本出现明显变化
- 模型出现新的能力边界
- 某产业从 PoC 开始向 Production 转移
- 大量用户实际反馈与厂商宣传出现明显差异
- 开源社区突然围绕某项目快速聚集

### 输出要求（不追求数量，每天 0-3 个）

**分析结构**：
- **Signal**：发生了什么异常或新变化？
- **Evidence**：有哪些独立证据支持？
- **Why It Matters**：为什么值得关注？
- **What to Watch**：未来需要继续观察什么指标或事件？

**验证门槛**（必须满足至少一项）：
- 多源证据
- 连续变化
- 关键人物/机构参与
- 数据变化

❌ 单个 X 帖子、Reddit 评论、HN 讨论或个人观点**不能**直接升级为产业趋势。

### 共识解读升级

📊 共识解读栏目从：
- "行业现在普遍怎么看？"

升级为同时回答三个问题：
1. 行业已经形成什么**共识**？
2. 哪些旧共识正在被**打破**？
3. 哪些新共识正在**形成**？
4. 今天出现了什么值得持续跟踪的 **Weak Signal**？

---

