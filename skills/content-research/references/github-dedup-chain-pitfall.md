# GitHub 推荐去重链（sync_gh_repos.py ↔ content-research）

> 这条链**断过两次**，每次都是「上游还在写、下游已经不看」。任何一环改动都必须跑完文末的验收清单。

## 完整链条（2026-10-10 定型，四环）

```
① 采集层搜候选   gh_recommend_candidates.py      ← 2026-10-10 新建，之前这里是断的
② 过滤历史重复   同脚本内：历史库 + 近30天报告 取并集 → 每赛道 3 个 fresh
③ agent 写文案   只从 /tmp/gh_fresh_candidates.json 的 fresh 列表挑（每赛道 1 个）
④ 落库 + 回写历史  sync_gh_repos.py → 飞书表；rebuild_history_from_feishu() → recommended-repos.json
⑤ 硬校验         daily_briefing_check.py E9c：报告里的项目 ∈ 今天之前的历史 → error
```

## 两次断裂

### ① 2026-09-11：sync 只查飞书表，本地历史库不再被维护
- 现象：已推荐项目被重复推荐
- 修：sync_gh_repos.py 每次同步后调 `rebuild_history_from_feishu()` 重建 `~/.hermes/recommended-repos.json`

### ② 2026-10-10：库重建了，但**消费端被写死成不看**
- 采集脚本第 7 步被改成 `# 历史库已废弃，不再检查` + `HIST_COUNT=0` → 摘要告诉 agent「历史推荐 0 个项目」
- 同一步的 gh 命令还有两个 bug：
  1. `GH_HEADER="-H Authorization: Bearer xxx"` **未加引号** → 展开成 4 个参数 → gh 报
     `unknown shorthand flag: 'H' in -H` → `|| echo '[]'` → **候选文件天天是空数组**
  2. 没带 `--json`（gh 默认输出文本表格，本来也不是 JSON，parser 也读不到）
- 后果链：候选为空 → agent 拿不到任何仓库 → 只能凭印象挑 → 同一项目连推
  （deepseek-harness 10/02·10/07·10/10；KKKKhazix/AIHOT 10/02·10/03·10/05·10/10）
- 修：搜索/去重/选候选全收进 `gh_recommend_candidates.py`（`--json` + `GH_TOKEN` 环境变量），
  并加 E9c 硬校验；prompt 里那句「读历史库去重」改成「只能从 fresh 列表选」。

## 🔴 根因模式（比单次 bug 更重要）

1. **「读取 X 去重」写在 prompt 里 = 白写**。模型不会因为 prompt 写了一行就去读文件；必须让**脚本产出已过滤的结果**（肯定式），或让**校验器硬拦**（阻塞式）。否定式规则（“不要重复”）永远不生效。
2. **静默降级最贵**。`2>/dev/null` + `|| echo '[]'` 把“命令报错”变成了“今天没有新项目”，连续错两周没人发现——每天的报告看起来都“正常”。凡是 `|| echo '[]'` 这种兜底，必须**同时**打一条可被抓取的健康信号（本仓库用 `[gh-cand] ⚠️ GH_SCAN_FAILED:` 前缀）。
3. **shell 里拼 HTTP header 极易错**：工具本身认环境变量（`GH_TOKEN`）就不要手工拼 header；拼了就必须引号。

## 验收清单（改任何一环都跑）

```bash
# 1 候选层：能看到“排除历史重复 N 个”，且三个赛道候选不重复
python3 ~/.hermes/scripts/gh_recommend_candidates.py
head -c 400 /tmp/gh_fresh_candidates.json

# 2 历史库在长（由 sync 回写）
python3 -c "import json;print(len(json.load(open('$HOME/.hermes/recommended-repos.json'))))"

# 3 真阳性：拿一份含历史项目的报告喂校验器 → 必须报 E9c
python3 ~/.hermes/scripts/daily_briefing_check.py --report <含重复项目的报告>

# 4 假阳性：拿一份全新鲜的报告 → E9c 必须为 0
python3 ~/.hermes/scripts/daily_briefing_check.py --report <全新鲜报告> --json | grep 跨日重复
```

⚠️ E9c 的历史口径必须**按日期过滤当天**：飞书表当天那份会在 06:07 入库，不过滤会把每天的合规报告都判成重复（`recommended_before()` 用 `推荐日期 < today_ms`）。
