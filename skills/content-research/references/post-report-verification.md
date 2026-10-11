# 报告发布后 L2 验证流程

> 用于独立验证已发布内容研究报告的数据源真实性、链接完整性和数字准确性。
> 输出结构化 JSON verdict 到 `/tmp/l2-verdict-<标签>.json`。

## 验证流程（6 步）

### 1. 读取目标报告

```bash
cat ~/hermes-output/content-research/content-research-YYYY-MM-DD.md
```

### 2. 提取所有 URL

从报告中提取三类链接：

- **显式 URL**（`[标题](链接)` 格式）—— 主要出现在「📎 今日推荐阅读」部分
- **GitHub 仓库引用**（`org/repo` 格式 + ⭐Star数）—— 出现在 🛠️ 项目推荐
- **信号来源归属**（如「（36氪 7/13）」「（雷锋网 7/13）」）—— 出现在 📌 What 段落

### 3. 交叉引用 all_deduped.json

```bash
# 对每个显式 URL，在 deduped 数据中搜索确认
python3 -c "
import json
with open('/tmp/all_deduped.json') as f:
    data = json.load(f)
url = 'https://example.com/article-path'
for item in data:
    if url in item.get('link', ''):
        print(f'FOUND: {item[\"title\"]} | {item[\"source\"]} | {item[\"pubDate\"]} | line marker')
        break
else:
    print(f'NOT_FOUND in all_deduped.json: {url}')
"
```

**验证要点**：
- URL 必须完整（无 `...` 省略号、无 `[来源名]` 占位符）
- 对应条目的 `source`、`pubDate` 必须与报告中的归属一致
- Star 数标注必须在报告中是实际数字 ± 合理四舍五入（<5% 偏差）

### 4. HTTP 连通性验证

```bash
# 对每个显式 URL 做 HTTP 200 检查
curl -s -o /dev/null -w "%{http_code}" <url> --connect-timeout 10 --max-time 15 -L
```

**预期**：
- 200 = 可正常访问
- 301/302 = 重定向但可访问（接受）
- 403/404 = 链接失效（标记 FAIL）
- 超时 = 网络问题（标记 WARN）

### 5. GitHub 仓库验证

```bash
# 验证仓库存在 + 获取实际 Star 数
curl -s "https://api.github.com/repos/org/repo" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'stars:{d.get(\"stargazers_count\", \"N/A\")}')
print(f'exists:{\"stargazers_count\" in d}')
"

# 也做 HTTP 访问验证
curl -s -o /dev/null -w "%{http_code}" "https://github.com/org/repo" --connect-timeout 10 --max-time 15 -L
```

**Star 数偏差容差**：
- `7.3K` ↔ 实际 7304 ✓（<1% 偏差）
- `6K` ↔ 实际 5956 ✓（约 0.7% 偏差，合理四舍五入）
- `7.7K` ↔ 实际 7738 ✓（<0.5% 偏差）

### 6. 数据源可追溯性（信号级验证）

检查报告中的每个信号能否在 `all_deduped.json` 中找到来源条目：

```
信号: "GPT-5.6 登陆 Bedrock"
→ 在 deduped JSON 中搜索: "Bedrock", "GPT-5.6", "AWS AI Blog"
→ 确认: source="AWS AI Blog", level="L1", pubDate 与报告一致

信号: "自律公约发布，31家企业联合"
→ 搜: "自律公约", "雷锋网"
→ 确认: title 含"31家企业"，source="雷锋网"，L3
```

## 输出格式

```json
{
  "score": "PASS | WARN | FAIL",
  "checks": [
    {
      "item": "检查项名称",
      "result": "PASS | WARN | FAIL",
      "detail": "详细说明"
    }
  ],
  "issues": [
    "发现的每一个问题作为一条字符串"
  ]
}
```

写入 `/tmp/l2-verdict-<标签>.json`（如 `l2-verdict-A.json` 表示第一轮验证，`l2-verdict-B.json` 表示第二轮）。

## 已知坑位

### 🔥 URL 手写截断（2026-07-18 新增）
- 直接写报告时，容易凭记忆手写 URL 导致截断（如把 `agent-incident-and-most-still-let-agents-share-credentials` 写成 `agent-inc`）
- **唯一正确方式**：所有 URL 必须从 `/tmp/all_deduped.json` 中提取对应条目的完整 `link` 字段，禁止手写
- 验证脚本会自动对比报告 URL 和 deduped JSON 中的实际 URL，不匹配时报告 FAIL

### 36氪 feed 数据滞后
- `/tmp/36kr_hot.json` 和 `/tmp/36kr_news.json` 的 `lastBuildDate` 可能早于报告生成日期
- 2026-07-14 实测：36氪 feed 数据仅覆盖至 7月9日，但报告中有 2 处来源归属标注为「36氪 7/13」
- **结论**：如果报告中的 36氪 attribution 日期晚于 feed 数据的 lastBuildDate，则无法从现有 feed 数据追溯验证。可能是文章发表于 feed 采集之后，也可能是 attribution 误差。标记 WARN 并注明。

### GitHub 仓库不在 raw feed JSON 中
- 报告引用的 GitHub 仓库（🛠️ 项目推荐）可能不在 `/tmp/gh_*.json` 文件中（这些文件是用 `gh search repos` 限定 `created:>90天前` 搜索的）
- 这**不构成数据虚构风险**——star 数通常来自独立的 GitHub API 查询
- 通过 GitHub API 直接验证仓库存在和 star 数即可

### parse_all_feeds.py URL 截断
- `all_deduped.json` 中某些条目的 `link` 字段可能被意外截断（特别是 MarkTechPost 等 feed）
- 对比报告 URL 和 deduped JSON 中的 URL 时，如果 deduped 的 URL 以 `...` 结尾或明显不完整，需查原始 XML
