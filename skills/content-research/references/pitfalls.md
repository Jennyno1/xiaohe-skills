# 执行层坑位库（cron / 链式故障 / 手动测试）

> 本文件由 4 份同主题文档合并而成（2026-09-17）。合并理由：坑位按时间散成四份，检索时要翻四个文件；合并后一处可查，且每节标注原始出处。
> 各节正文逐字保留原内容，标题处标注原始文件名，便于回溯与检索。

## 本文件包含

- 〔原 `cron-manual-test-pitfall.md`〕
- 〔原 `cron-model-routing-pitfall.md`〕
- 〔原 `v8-execution-pitfalls.md`〕
- 〔原 `stale-file-chain-failure-2026-08-30.md`〕

---


## 〔原 `cron-manual-test-pitfall.md`〕

# 内容日报 cron 旧文件陷阱（含手动测试 + 自动执行）

## 问题

只要 `content-research-YYYY-MM-DD.md` 文件已存在，无论原因是手动测试还是前次执行残留，模型都会跳过数据采集和完整版生成，只输出微信精简摘要。

**影响范围远不止手动测试**：2026-08-30 实证——8/29 手动测试生成了 `content-research-2026-08-30.md`（提前创建了第二天的文件），导致 8/30 凌晨 06:00 正式 cron 找到该文件后直接跳过采集，用旧数据生成了摘要。

### 链式故障（2026-08-30 实证）

旧文件导致的**不只是内容重复**，而是整条下游链条断裂：

```
旧文件存在 → cron 跳过采集和生成 → 用旧报告发微信摘要
  ├─ IMA 笔记未同步（没有新报告可同步）
  ├─ sync_gh_repos.py 判定"无新项目"（项目已在历史库）→ 飞书表为空
  └─ 去重逻辑被绕过（未执行 gh search）→ 历史已推荐项目被重复推荐
```

**三个用户可见问题（内容重复 + IMA缺失 + GitHub重复）源自同一个根因。**

## 根因

Cron prompt 虽然写了"完整版写盘 + 微信只发摘要版"，但模型在看到当天报告已存在时，会自行判断"今天工作已经完成"，从而只做摘要输出。这不是偶发行为——是确定性的偷懒。

## 正确测试步骤

### 1. 备份并清除当天报告

```bash
DATE=2026-08-20
FILE=~/hermes-output/content-research/content-research-${DATE}.md

# 备份（防止需要回滚）
cp "$FILE" "${FILE}.bak$(date +%s)" 2>/dev/null

# 删除，强制重新生成
rm -f "$FILE"
```

### 2. 触发 cron 运行

```bash
hermes cron run deb7e428f689
```

或者通过 Hermes API：

```python
cronjob(action='run', job_id='deb7e428f689')
```

### 3. 等待并检查新生成的报告

```bash
ls -lt ~/hermes-output/content-research/ | head -5
```

确认：
- `content-research-YYYY-MM-DD.md` 时间戳是刚才
- 文件大小明显变化（不是旧文件）

### 4. 验证共识与分歧模块（v7.10 格式）

```bash
grep -n "^## 📊\|^### 🔵\|^### 🔴\|引用1：\|引用2：\|引用3：" \
  ~/hermes-output/content-research/content-research-2026-08-20.md
```

应该看到：
- `## 📊 最大共识与分歧`
- `### 🔵 共识解读`
- `### 🔴 分歧解读`
- `▸ 引用1：`
- `▸ 引用2：`
- `▸ 引用3：`

### 5. 验证素材池数量

```bash
python3 -c "
import json, collections, os
path = '/tmp/all_deduped.json'
if os.path.exists(path):
    d = json.load(open(path))
    print(f'素材总数: {len(d)}')
    for src, cnt in collections.Counter(i.get('source','unknown') for i in d).most_common():
        print(f'  {src}: {cnt}')
else:
    print('/tmp/all_deduped.json 不存在')
"
```

> ⚠️ **注意：不可仅仅依赖 cron prompt 中的"完整版写盘"约束** —— 2026-08-20 实测即使 prompt 已写明两级输出，连续两次运行都因旧文件存在而只发摘要。必须先删除旧文件才能真正验证新格式。

## 验证清单（测试后必做）

1. 检查 `~/hermes-output/content-research/content-research-YYYY-MM-DD.md` 时间戳和大小是否为新生成
2. 检查 `最大共识与分歧`模块是否出现 `## 📊` / `### 🔵` / `### 🔴` 标题
3. 检查引用事件是否为 `▸ 引用N：` 格式并单独分行
4. 检查 `/tmp/all_deduped.json` 素材总数是否 ≥30 条、来源是否 ≥3 个

## 什么时候需要这么做

- 修改了报告模板/格式后需要验证新格式
- 修改了 cron prompt 后需要验证新 prompt 是否生效
- 用户说"手动跑一遍测试"时
- **手动测试创建了"明天"的文件后**（如 8/29 测试生成了 8/30 的文件），次日正式 cron 会被阻塞

## 推荐的 cron 硬逻辑（防止自动执行也被阻塞）

在 cron prompt 的步骤 0（启动前检查）中加入文件年龄校验：

```bash
TODAY=$(date +%Y-%m-%d)
REPORT=~/hermes-content/content-research/content-research-${TODAY}.md
if [ -f "$REPORT" ]; then
  AGE_MIN=$(( ($(date +%s) - $(stat -c %Y "$REPORT")) / 60 ))
  if [ "$AGE_MIN" -gt 30 ]; then
    echo "⚠️ 报告文件已存在且超过 ${AGE_MIN} 分钟，疑似旧文件残留，删除后重新生成"
    cp "$REPORT" "${REPORT}.bak$(date +%s)"
    rm -f "$REPORT"
  fi
fi
```

核心思路：文件存在且超过 30 分钟 → 备份 → 删除 → 强制重新采集生成。

## 注意

- 删除前一定要先备份，防止丢失重要版本
- 正式生产环境中此逻辑保护 cron 不被旧文件阻塞
- 如果删除后 cron 仍然只输出精简版，检查 cron prompt 里是否明确写了"必须重新生成完整版并写盘"
- **手动测试后务必清理非当天的报告文件**，否则会阻塞次日自动执行


---


## 〔原 `cron-model-routing-pitfall.md`〕

# Cron Model Routing Pitfall — 2026-08-27

## 问题背景

`models.yaml` 的 `cron:` 段存储了每个 cron job 的权威模型映射，但 **cron job 条目本身的 `model` 字段不自动同步这个映射**。

当 `jobs.json` 里 cron job 的 `model` 字段为 `None` 时，Hermes 使用**当前默认模型**，而不是 models.yaml 的映射。

## 实证案例

### 2026-08-27 06:01:12 日志
```
model=agnes-2.5-flash summary=HTTP 401: Model agnes-2.5-flash is not supported
```
原因：
1. 昨晚（8/26）把默认模型从 `ox-alpha-free` 切到 `agnes-2.5-flash`
2. cron job `deb7e428f689`（daily-content-research）的 `model` 字段是 `None`
3. 今早 06:00 触发时使用了当前默认模型 `agnes-2.5-flash`
4. opencode-go 不支持 agnes-2.5-flash → 401 错误
5. 最终 fallback 到了其他模型，但过程浪费了一次重试

### models.yaml 实际配置（正确但未被读取）
```yaml
cron:
  daily-content-research:
    model: mimo-v2.5-free
    provider: opencode-go
    desc: "每日内容研究简报 (8/21 切 mimo-v2.5-free)"
```

## 修复

```bash
# 查看 jobs.json 里 cron job 的 model 字段
cat ~/.hermes/cron/jobs.json | python3 -c "import sys,json; d=json.load(sys.stdin); [print(j.get('name'), j.get('model')) for j in d if 'daily' in j.get('name','')]"

# 修复：显式指定 model
cronjob action=update --job-id deb7e428f689 --model mimo-v2.5-free --provider opencode-go
```

## 预防措施

每次创建或修改 cron job 时：
1. **必须**显式指定 `--model` 参数
2. 不要用 `model=None`（除非你明确想让 cron 跟随当前默认）
3. 修改 skill 后运行 `cronjob action=update` 确保 prompt 和 model 同步

## 相关文件

- `~/.hermes/models.yaml` — 权威模型映射
- `~/.hermes/cron/jobs.json` — cron job 实际配置（以这里为准）


---


## 〔原 `v8-execution-pitfalls.md`〕

# content-research 执行层 Pitfalls（2026-09-08 更新）

## 新增坑位

### 1. IMA同步成功但check脚本报auth失败（2026-09-08实证）

**问题**：`ima_sync.py` 成功返回 `OK note_id=xxx`，但后续 `daily_briefing_check.py` 报 "IMA 搜索失败: skill auth failed"。

**根因**：check脚本通过搜索IMA笔记列表验证同步，但当前环境IMA搜索接口返回auth失败（可能是权限降级或接口变更）。这是check脚本的局限性，**不代表实际同步失败**。

**铁律**：
- IMA同步以 `ima_sync.py` 的返回结果为准（`OK note_id=xxx` = 成功）
- `daily_briefing_check.py` 的 IMA 搜索失败是已知问题，不阻塞管道
- 检查报告：若 IMA 同步成功但 check 报 auth 失败，在最终输出中注明即可

### 2. GitHub推荐飞书入库去重逻辑（2026-09-08实证）

**问题**：`sync_gh_repos.py` 对已在飞书表中的项目跳过写入（⏭️ 飞书表已有），check脚本报"缺3个项目"。

**根因**：飞书表只有1个新项目入库，其他2个是历史已存在项目被正确跳过。check脚本的"飞书表缺N个项目"是假阳性——它假设当天所有推荐项目都未入库。

**铁律**：
- sync_gh_repos.py 的 "⏭️ 飞书表已有，跳过" = 正常行为（去重正确）
- "✅ 新增 N 个项目" 才是有效入库记录
- check脚本的飞书表校验存在已知假阳性，不阻塞管道

### 3. 微信emoji分行规则（2026-09-08实证）

**问题**：`daily-briefing-check.py` 检查要求 `•` 符号后必须有空行，否则微信会合并显示两行。

**铁律**：
- 🎯要点的3条 `•` 之间必须有空行分隔
- ⭐GitHub推荐的每个项目之间必须有空行分隔
- 否则check脚本报"分行"违规

### 4. recommended-repos.json 文件不存在（2026-09-08实证）

**问题**：`~/.hermes/recommended-repos.json` 不存在，导致GitHub历史去重失效。

**根因**：飞书表已是权威源，本地历史库已废弃。check脚本中读取此文件的逻辑需适配。

**处理**：代码中已加 try/except 捕获，不影响运行。但建议确认是否需要在其他地方建立等效历史去重机制。


---


## 〔原 `stale-file-chain-failure-2026-08-30.md`〕

# Stale File Chain Failure — 2026-08-30 根因分析与修复

## 事故概述

2026-08-30 内容日报 cron 执行后，用户发现三个问题：
1. 微信摘要内容与昨天测试版相同（未重新采集）
2. IMA 笔记未同步、GitHub 飞书表未入库
3. GitHub 推荐项目与历史库重复

**三个问题同一根因：旧报告文件未清理。**

## 根因链路

```
8/29 测试运行生成了 content-research-2026-08-30.md（日期=明天）
     ↓
8/30 06:01 cron 执行
     ↓
agent 发现文件已存在（创建日期=8/29，但文件名是8/30）
     ↓
agent 判定"报告已生成"，跳过数据采集步骤
     ↓
直接用旧报告内容生成微信摘要 → 内容与昨天相同
     ↓
跳过 IMA 同步 → IMA 笔记缺失
     ↓
跳过 GitHub 推荐写入 → 飞书表为空（实际后来查有166条历史记录）
     ↓
去重逻辑被绕过 → 推荐了历史已有的项目
```

## 关键证据

| 证据 | 值 |
|:---|:---|
| 文件创建时间 | `2026-08-29 08:07`（昨天测试时生成） |
| cron 执行时间 | `2026-08-30 06:01` |
| agent 输出 | *"Now generating the WeChat summary from the **existing** full report"* |
| /tmp 素材文件 | 全部不存在（采集步骤未执行） |
| 推荐项目 | 3个全部在 recommended-repos.json 历史库中 |

## 修复措施（（当时版本））

### 1. Cron Prompt Step 0: 报告新鲜度硬校验
在采集步骤前强制执行 bash 检查：
- 文件存在 + 今天创建 → 可使用
- 文件存在 + 非今天创建 → 强制删除，重新采集
- 文件不存在 → 正常全流程

### 2. sync_gh_repos.py 去重升级
- 原：只查飞书表
- 新：飞书表 + recommended-repos.json 历史库双查
- 新增日志：区分"飞书表已有跳过"和"历史库已有跳过"

### 3. 完整性校验脚本
`~/.hermes/scripts/daily_briefing_check.py` 检查 4 项：
1. 报告文件存在性 + 新鲜度
2. IMA 笔记同步
3. 飞书 GitHub 表入库
4. GitHub 项目去重

## 通用教训

**链式故障模式**：cron 任务的输出文件被下游逻辑当作"已完成"标志 → 跳过核心步骤 → 所有依赖链条断裂。

适用于所有会产出文件且有"检查文件是否存在"逻辑的 cron 任务。修复模式：**文件年龄校验（creation date == today）** 比简单存在性检查更可靠。


---
