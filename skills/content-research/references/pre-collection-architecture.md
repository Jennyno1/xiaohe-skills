# 预采集架构（（当时版本））

> 本文件由 2 份同主题文档合并而成（2026-09-17）。合并理由：两份架构说明标题几乎同名、内容互为补充，分散在两处容易只读一半。
> 各节正文逐字保留原内容，标题处标注原始文件名，便于回溯与检索。

## 本文件包含

- 〔原 `（当时版本）-architecture.md`〕
- 〔原 `pre-collection-architecture-v831.md`〕

---


## 〔原 `（当时版本）-architecture.md`〕

# （当时版本） 架构重构记录 (2026-08-30)

## 问题

v8.2 cron 在 30 轮迭代内无法完成全部任务。SKILL.md 102KB + 20个RSS源采集 + 报告生成 + IMA同步 + 飞书入库 + 校验，迭代数严重不足。

症状：agent 生成了完整版但来不及存盘/IMA同步/飞书入库就超时，微信推送发了全文而非摘要。

## 解决方案：预采集脚本拆分

### 新架构 (（当时版本）)

```
cron 触发
  → collect_daily_feeds.sh (脚本先跑，23秒完成)
    → RSSHub 检查/启动
    → curl 15个RSS源 + 4个RSSHub中文源
    → GitHub趋势扫描
    → parse_all_feeds.py 解析去重
    → 输出 /tmp/all_deduped.json + stdout 采集摘要
  → agent 读 /tmp/all_deduped.json
    → 生成完整版 → 存盘
    → IMA 同步 (ima_sync.py)
    → 飞书 GitHub 入库 (sync_gh_repos.py)
    → 完整性校验 (daily_briefing_check.py)
    → 生成微信摘要版 → 最终回复
```

### 关键文件

| 文件 | 用途 | 位置 |
|:---|:---|:---|
| collect_daily_feeds.sh | 预采集脚本 | ~/.hermes/scripts/collect_daily_feeds.sh |
| daily_briefing_check.py | 完整性校验 | ~/.hermes/scripts/daily_briefing_check.py |
| sync_gh_repos.py | 飞书GitHub表入库 | ~/.hermes/scripts/sync_gh_repos.py |
| ima_sync.py | IMA笔记同步 | skills/digital-twin/content-research/scripts/ima_sync.py |
| parse_all_feeds.py | RSS解析去重 | skills/digital-twin/content-research/scripts/parse_all_feeds.py |

### Cron 配置变更

```json
{
  "script": "~/.hermes/scripts/collect_daily_feeds.sh",
  "prompt": "[精简版：只含报告生成+同步步骤，1312字符]",
  "skills": ["content-research"]
}
```

脚本通过 cron 的 `script` 参数运行，stdout 注入 agent prompt 上方。Agent 读取采集摘要后直接生成报告。

## 30轮迭代约束（铁律）

Hermes cron 的 agent 执行有 30 轮迭代上限。SKILL.md 102KB 加载就消耗大量上下文。经验法则：
- **预采集脚本处理所有 I/O**（curl/RSSHub/解析）：23秒
- **Agent 只做 LLM 推理**（读数据/生成报告/同步）
- 如果 prompt 超过 1500 字符 + skill 超过 50KB，30 轮大概率不够

## sync_gh_repos.py 去重升级 (（当时版本）)

原逻辑：只查飞书表做去重
新逻辑：飞书表 + recommended-repos.json 历史库双查

原因：飞书表可能有记录但历史库没有（或反过来），单查一边会漏。

## 完整性校验脚本

daily_briefing_check.py 自动检查 4 项：
1. 报告文件存在性 + 新鲜度
2. IMA 笔记同步状态
3. 飞书 GitHub 表入库状态
4. GitHub 项目去重（单天内 + 历史库交叉）

exit 0 = 通过，exit 1 = 有问题。

## 教训

1. **旧报告文件必须在 cron 执行前检查并清理** — 08-30 实证：旧文件导致 agent 跳过采集，三个下游全部断裂
2. **30 轮迭代对复杂任务是硬限制** — 不是优化能解决的，必须拆分架构
3. **Agent 的"最终回复"必须明确指定是摘要版** — prompt 中不写"摘要版=最终回复"，agent 就发全文
4. **IMA 同步容易被 agent 跳过** — 即使 prompt 写了"强制"，迭代不够时 agent 会省略。预采集脚本 + 精简 prompt 是更可靠的方案


---


## 〔原 `pre-collection-architecture-v831.md`〕

# 预采集架构 （当时版本） (2026-08-30)

## 背景

v8.2 及之前：agent 在 cron 中同时负责数据采集 + 报告生成 + IMA同步 + 飞书入库。SKILL.md 102KB + prompt 1.8KB 占满 30 轮迭代上限，导致：
- agent 超时 → 只发完整版不发摘要
- IMA 同步被跳过
- 飞书 GitHub 入库未执行
- 报告文件未存盘

## （当时版本） 架构

```
cron 执行流程:
  1. script: collect_daily_feeds.sh (23秒，不消耗 agent 迭代)
     ├── 报告新鲜度检查（STALE→删旧文件）
     ├── RSSHub 检查/启动
     ├── 20+ RSS 源并行 curl
     ├── GitHub 趋势扫描
     ├── parse_all_feeds.py 解析去重
     └── 输出采集摘要到 stdout
  2. agent: 只做生成 + 同步
     ├── 读 /tmp/all_deduped.json
     ├── 读昨日报告去重
     ├── 生成完整版 → 存盘
     ├── IMA 同步
     ├── 飞书 GitHub 入库
     ├── 完整性校验
     └── 微信摘要版 = 最终回复
```

## 关键文件

| 文件 | 用途 |
|------|------|
| `~/.hermes/scripts/collect_daily_feeds.sh` | 预采集脚本 |
| `~/.hermes/scripts/sync_gh_repos.py` | GitHub→飞书入库（含 retry） |
| `~/.hermes/scripts/daily_briefing_check.py` | 完整性校验 |
| `scripts/ima_sync.py` | IMA 笔记同步 |
| `scripts/parse_all_feeds.py` | RSS 解析去重 |

## cron 配置

```json
{
  "name": "daily-content-research",
  "script": "~/.hermes/scripts/collect_daily_feeds.sh",
  "prompt": "[精简版：只含生成+同步步骤]",
  "skills": ["content-research"]
}
```

## 迭代消耗对比

| 版本 | agent 迭代消耗 | 微信输出 | IMA | GitHub入库 |
|------|---------------|---------|-----|-----------|
| v8.2 (旧) | ~28/30 | 完整版(误) | ❌跳过 | ❌跳过 |
| （当时版本） (新) | ~10/30 | 摘要版✅ | ✅ | ✅ |

## 踩坑记录

### 1. 旧报告文件链式故障 (2026-08-30)
- **现象**: 8/30 日报内容与 8/29 测试版相同，IMA没同步，GitHub表空，项目重复
- **根因**: `content-research-2026-08-30.md` 在 8/29 测试时创建，cron 发现文件已存在且"FRESH"（当天创建），跳过采集直接用旧数据
- **修复**: collect_daily_feeds.sh 第一步检查文件创建日期，非今天→强制删除

### 2. sync_gh_repos.py 静默异常 (2026-08-30)
- **现象**: 飞书表有记录但 Stars=0, Fork=0
- **根因**: GitHub API 瞬时网络错误，`except Exception: info = {}` 静默吞异常
- **修复**: 3次 retry + 错误日志 + Stars=0 拒绝入库

### 3. 飞书表去重 ≠ 历史库去重
- **现象**: sync 脚本跳过项目（飞书表已有），但飞书表实际为空
- **根因**: sync 检查飞书表做去重，但某些项目通过其他方式（手动/旧cron）已入库
- **修复**: sync 同时检查 recommended-repos.json 历史库，双查去重

### 4. Agent 发完整版不是摘要
- **现象**: 微信收到几千字全文而非≤600字摘要
- **根因**: agent 迭代耗尽，来不及生成摘要版就超时，直接把完整版当回复
- **修复**: 预采集脚本释放迭代空间，agent 有足够轮次生成摘要


---
