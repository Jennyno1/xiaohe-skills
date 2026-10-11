# 快速上手（5 分钟）

目标：跑出你的第一份三赛道简报。

## 0. 前置

| 项 | 要求 |
|---|---|
Agent | Hermes / Claude Code / Codex 等任意能读 `SKILL.md` 并执行 shell 的 Agent |
Python | 3.9+（多数脚本用标准库） |
可选依赖 | `pip install requests`（GitHub 数据补齐用）；需 RSSHub 时自备实例地址 |

## 1. 安装

```bash
# Hermes
hermes skills install Jennyno1/xiaohe-skills/skills/content-research

# 其他 Agent：复制目录
git clone https://github.com/Jennyno1/xiaohe-skills
cp -r xiaohe-skills/skills/content-research ~/.claude/skills/     # 换成你的 agent 目录
```

## 2. 配置

```bash
export CONTENT_RESEARCH_OUTPUT_DIR=~/content-research-output
mkdir -p "$CONTENT_RESEARCH_OUTPUT_DIR"
export GH_TOKEN=ghp_xxx     # 可选：有它才能拿到精确星数
```

## 3. 跑一次（手动）

把下面这句交给你的 Agent：

> 读 `content-research/SKILL.md`，按其中的 8 步流程生成今天的三赛道简报，产物写到 `$CONTENT_RESEARCH_OUTPUT_DIR`。

或直接跑采集脚本，先看数据是否能拿到：

```bash
cd <技能目录>/scripts
python3 parse_all_feeds.py --help     2>/dev/null || python3 parse_all_feeds.py
```

## 4. 验收（这一步别跳）

```bash
# 用自带的校验器检查产物
python3 scripts/daily-briefing-check.py --report "$CONTENT_RESEARCH_OUTPUT_DIR/content-research-<日期>.md"
# exit 0 = 合规；1 = 不合规（按输出提示修）；2 = 文件错误
```

校验器会检查：模块完整性、格式铁律、引用数量、字数、共识/分歧结构等。**先让它过，再谈投递。**

## 5. 接自己的投递（可选）

本 Skill 只产出文件。要推送到你的渠道时，在你的 Agent / 定时任务里加一步：

```
生成完 → 调 daily-briefing-check.py（exit 0）→ 把产物摘要 POST 到你的 webhook / 邮件 / IM
```

## 常见坑

| 现象 | 处理 |
|---|---|
星数是 `N/A` | 没配 `GH_TOKEN`，或 GitHub API 被限流；脚本会走 shields 兜底并标注来源 |
采集为空 | 多数源需要 RSSHub 实例；先确认你的 RSSHub 地址可达 |
校验器报模块缺失 | Agent 跳步了——按 `SKILL.md` 的 8 步流程重跑，不要让它"就地编" |
