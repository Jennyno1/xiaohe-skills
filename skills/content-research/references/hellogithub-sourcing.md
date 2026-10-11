# HelloGitHub 月刊 — 筛选模型与用法（2026-08-16 调研）

用户 2026-08-16 指定 HelloGitHub 为「解决 AI/IT 问题的优先学习源」，并加入飞书 GitHub 推荐清单表（来源=HelloGitHub月刊）。本文件沉淀其筛选逻辑与落地用法。

## 基本盘

- 仓库：`521xueweihan/HelloGitHub`，⭐171K，中文项目第一梯队，2016 年创建
- 发刊：每月 28 日，官网 https://hellogithub.com/periodical ，GitHub content/HelloGitHub{N}.md
- 分类目录：C / C++ / Go / Java / JavaScript / Python / Rust / Skills / Swift / AI / Other / Book

## 筛选逻辑（官方无公开量化标准，以下为实际观察归纳）

官方口径（README）：「分享 GitHub 上有趣、入门级的开源项目。兴趣是最好的老师。」

| 维度 | 规律 | 例证（vol.124） |
|---|---|---|
| 星数 | **无下限，不唯星数论** | 收 485 星 LockIME，也收 4.3万星 OpenMontage；569 星 make-look-scanned 也入选 |
| 核心标准 | 「有趣」>「大」>「新」 | 优先收录有话题点的项目（PDF 变扫描件、老 PC 模拟器） |
| 入门友好 | 强调小白能用起来 | 每个项目配中文简介+配图+怎么用 |
| 来源 | 社区推荐/自荐为主 | hellogithub.com/periodical 提交，主编人工筛选 |
| 时效 | 当月 GitHub 上新出彩项目 | 非全站总 star 排名 |
| 多样性 | 每期语言/类型覆盖均衡 | 一个语言区 2-4 个，不偏科 |

**一句话**：HelloGitHub = 主编品味驱动的「有趣+入门级」精选，数据门槛不是硬指标，选题点才是。

## 与自家日报推荐对比（两层互补）

| | HelloGitHub | 日报推荐 |
|---|---|---|
| 驱动 | 人工品味 | 数据（star≥10K） |
| 目标读者 | 泛开源爱好者 | 主理人（AI内容创作者） |
| 输出 | 每月一期全品类 | 每日3个赛道相关 |
| 用法 | 它做「有趣」初筛 | 我们按赛道相关性+真拆过真用过二次筛选 |

## 落地用法（每月 28 日）

1. 拉当月新刊：`web_extract https://hellogithub.com/periodical/volume/N` 或读 GitHub `content/HelloGitHubN.md`
2. 按三赛道挑 2-3 个候选（AI 内容创作 / 企业AI / AI产业）
3. **铁律：只写真拆过真用过的**——自动任务只能列候选+入库，使用痕迹必须用户确认，禁止编造
4. 写入飞书推荐清单表：项目类型按实际（工具/skill/框架/书籍/内容源）、来源=HelloGitHub月刊、带 Fork数+推荐理由
5. 可写的高价值选题补进选题池（状态=待写）

## vol.124 精选（2026-07-28，与三赛道强相关）

- `calesthio/OpenMontage` ⭐4.3w — AI 编程助手变视频工作室（框架，已入表）
- `Nutlope/hallmark` ⭐1.9w — 反 AI 味网页设计 skill（skill，已入表；方法论已落地站外平台内容清单）
- `tt-a1i/archify` ⭐7.5k — AI 代码转架构图 skill（skill，已入表）
- 其余值得留意：tirth8205/code-review-graph ⭐2.7w（代码智能图谱）、gastownhall/gastown ⭐1.7w（多 agent 编排）、dottxt-ai/outlines ⭐1.5w（结构化输出）、karakeep-app/karakeep ⭐2.8w（自托管书签+AI 打标）

## 注意

- HelloGitHub 是「内容源/选题矿」，不是可安装工具——不进「能直接装进 AI agent 的 skill」推荐，但每月可作选题补充
- 已加入 `~/.hermes/reference/learning-resources.md` 置顶（优先学习源）
