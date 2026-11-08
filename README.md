# 小禾 Skills · 开源合集

> 别人给你「今天发生了什么」，这里的 Skill 给你「今天该怎么判断」。

这个仓库放我个人在生产中真实运行的 Agent Skill（**剥离私人配置后的公开版**），你可以直接安装、改配置、接自己的运行环境。

## 📦 包含什么

| Skill | 一句话 | 状态 |
|---|---|---|
| [content-research](skills/content-research/) | 每日内容简报：三赛道（AI产业技术 / 企业AI应用 / 内容创作），采集 → 去重 → 生成 → 自检全链路 | ✅ 可用 |
| 更多 Skill | 逐步搬入中 | 🚧 |

## 🚀 安装（以 content-research 为例）

```bash
# 方式一：直接装
hermes skills install Jennyno1/xiaohe-skills/skills/content-research

# 方式二：先订阅本仓库为 skill 源，再浏览/安装
hermes skills tap add Jennyno1/xiaohe-skills
hermes skills search content-research
```

**其他 Agent（Claude Code / Codex / Copilot 等）**：Skill 就是纯文本目录，复制即可：

```bash
git clone https://github.com/Jennyno1/xiaohe-skills
cp -r xiaohe-skills/skills/content-research ~/<你的agent>/skills/
```

## ⚙️ 配置（两分钟）

| 配置 | 作用 | 默认 |
|---|---|---|
`CONTENT_RESEARCH_OUTPUT_DIR` | 简报落盘目录 | `~/content-research-output` |
`GH_TOKEN`（可选） | GitHub 星数精确值；没有时走 shields 徽章兜底并强制标注 | 无 |

```bash
export CONTENT_RESEARCH_OUTPUT_DIR=~/content-research-output
export GH_TOKEN=ghp_xxx          # 可选
```

然后把 `SKILL.md` 交给你的 Agent，让它按里面的流程执行即可。快速上手见 [examples/quickstart.md](examples/quickstart.md)。

## 🧠 这个 Skill 的独特点

1. **三赛道结构**：不是资讯聚合，而是按「AI+产业技术 / AI+企业应用 / AI+内容创作」三条线组织，每条线走 What → Why → How
2. **共识 / 分歧判断层**：采集类项目普遍只给「发生了什么」，这个 Skill 额外做「哪些是共识、哪里有分歧、分歧点在哪」——**这是它的核心差异**
3. **20+ 篇失败模式库**：WAF 拦截、链式故障、去重断裂、RSS 校验……全是真实踩过的坑，不是 happy path
4. **组件化流水线**：预采集脚本 + Agent 只做生成，可移植到任意 Agent 运行时

## 📁 目录结构

```
skills/content-research/
├── SKILL.md            # 入口：触发条件 / 执行流程 / 格式铁律 / 检查点
├── scripts/            # 采集、去重、校验、合并（多数为纯标准库）
└── references/         # 信源目录、输出规范、共识规则、踩坑库（按需读）
```

## ⚠️ 范围说明（诚实披露）

**包含**：采集 → 去重 → 生成 → 自检 的完整引擎与方法论文档。

**不包含**（公开版有意移除）：
- 任何私人通道：消息推送 / 云笔记同步 / 多维表格写回（这些属「运行时壳」，请按自己环境实现）
- 含个人调度细节与私有资源 ID 的运行时文档（脱敏中，后续版本补入）
- 任何凭据、表 ID、个人域名（发布前经强制扫描，0 命中）

**第三方内容边界**：本仓库只提供**生成简报的工具与方法**，不转载、不分发第三方内容原文。生成结果中引用的信息请遵循原出处使用条款，详见 [NOTICE](NOTICE)。

## 📄 许可

代码采用 [MIT](LICENSE) 许可。第三方依赖与内容使用边界见 [NOTICE](NOTICE)。

---

_维护者：[@Jennyno1](https://github.com/Jennyno1) · 这些 Skill 都在真实生产里每天运行，公开版是它们的脱敏镜像。_
