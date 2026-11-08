# GitHub 项目入库规范 v2

> 最后更新: 2026-09-08  
> 维护脚本: `~/.hermes/scripts/sync_gh_repos.py`

---

## 一、飞书表字段结构 (15字段)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 项目名称 | text | org/repo 格式，如 `langchain-ai/langchain` |
| 项目描述 | text | 中文，有实质信息，不用 GitHub API 原文 |
| 推荐理由 | text | 简短说明价值，**禁止包含星数** |
| 项目类型 | select | skill/框架/工具/内容源/平台/书籍/数据集/其他 |
| Stars | number | 纯数字，type=2，不用 "200K" |
| Fork数 | number | 纯数字，type=2 |
| 主要语言 | text | Python/JavaScript 等 |
| 创建时间 | text | YYYY-MM-DD |
| 最近推送 | text | YYYY-MM-DD |
| 是否归档 | text | 是/否 |
| 推荐来源 | text | daily/hellogithub/manual |
| 入库日期 | text | YYYY-MM-DD |
| 来源追踪 | text | cron_id 或手动标记 |
| 备注 | text | 补充信息 |
| 验证状态 | select | 待验证/已验证/已过期 |

---

## 二、字段写入陷阱 (7条)

### 陷阱 1: Stars/Fork数必须传 int，不能传 "200K"
```python
# ❌ 错误
{'fields': {'Stars': '200K', 'Fork数': '20K'}}

# ✅ 正确
{'fields': {'Stars': 200000, 'Fork数': 20000}}
```
**原因**: 飞书 Bitable 字段类型 type=2 (number)，传字符串会报错或存储异常。

---

### 陷阱 2: 推荐理由禁止包含星数
```python
# ❌ 错误
'推荐理由': 'GitHub 热门项目，⭐162k，Master the command line'

# ✅ 正确
'推荐理由': '命令行艺术指南，收录 Linux/Mac 最佳实践'
```
**原因**: 星数动态变化，写入后会误导读者。

---

### 陷阱 3: 项目描述用日报格式，不用 GitHub API 原文
```python
# ❌ 错误 (GitHub API 原文)
'项目描述': 'The agent engineering platform.'

# ✅ 正确 (中文日报格式)
'项目描述': 'LangChain 框架核心库，支持 LLM 应用开发、Agent 构建、RAG 管道'
```
**原因**: GitHub 描述多为英文且简略，需转换为有实质信息的中文描述。

---

### 陷阱 4: 全字段一次性创建
```python
# ❌ 错误 (建空记录再补)
POST /records  # 先创建空记录
PUT /records/id  # 再更新

# ✅ 正确 (一次性写入所有字段)
POST /records, json={'fields': {所有字段}}
```
**原因**: 减少 API 调用次数，避免部分写入导致的数据不一致。

---

### 陷阱 5: 不存在的字段不要写入
```python
# ❌ 错误
{'fields': {' nonexistent_field': 'value'}}

# ✅ 正确 (只写飞书表实际有的 15 个字段)
{'fields': {'项目名称': '...', '项目描述': '...'}}
```
**原因**: 飞书 API 会忽略未知字段或返回错误。

---

### 陷阱 6: 项目类型从 GitHub API 动态解析
```python
def detect_project_type(gh_info):
    topics = [t.lower() for t in gh_info.get('topics', [])]
    lang = (gh_info.get('language') or '').lower()
    desc = (gh_info.get('description') or '').lower()
    all_text = ' '.join(topics) + ' ' + lang + ' ' + desc
    
    # 用完整词匹配，避免子串误判！
    # ❌ 错误: 'deep-learning' 包含 'learning' → 误判为书籍
    # ✅ 正确: 用 split() 分词后匹配
    if any(kw in all_text.split() for kw in ['book', 'textbook', 'e-book']):
        return '书籍'
```
**原因**: 飞书表项目类型是单选字段，需准确分类。

---

### 陷阱 7: GitHub API rate limit 处理
```python
# 认证用户: 5000次/小时
# 匿名: 60次/小时
# 必须配置 GH_TOKEN 环境变量
```
**原因**: 不带 token 调用会快速触发限流。

---

## 三、去重逻辑

### 权威源: 飞书表
```python
def load_dedup_sets():
    """只检查飞书表（历史库已废弃）"""
    existing_feishu = set()
    # ... 读取飞书表所有项目名称
    return existing_feishu
```

### 已废弃: 本地历史库
```
❌ ~/.hermes/recommended-repos.json  已删除
❌ 不再使用历史库做去重
```

---

## 四、写入模式

### 幂等续写
```python
def upsert_record(repo, gh_info):
    # 1. 先查飞书表是否已存在
    existing = find_in_feishu(repo)
    
    # 2. 存在则更新，不存在则创建
    if existing:
        PUT /records/{record_id}
    else:
        POST /records
```

### 限速策略
```python
time.sleep(0.2)  # 每条记录间隔 200ms
```

---

## 五、项目类型判断逻辑

### 优先级顺序
```
skill > 框架 > 工具 > 内容源 > 平台 > 数据集 > 书籍 > 其他
```

### 关键词映射

| 类型 | 关键词 (完整词匹配) |
|------|---------------------|
| skill | skill, claude-code, agent-skill, cursor-rule |
| 框架 | framework, sdk, library, runtime, engine |
| 工具 | cli, tool, utility, editor, debugger, linter, formatter, terminal, console, web-ui, gui, application |
| 内容源 | content, blog, cms, wiki, knowledge, documentation, newsletter, rss, article, tutorial, course, learning, education, awesome, list, collection, guide |
| 平台 | platform, saas, cloud, hosting, service, api, server, backend, dashboard |
| 数据集 | dataset, data, benchmark, corpus, training-data |
| 书籍 | book, textbook, e-book |

### ⚠️ 子串误判案例 (已修复)

| 仓库 | 误判原因 | 正确类型 |
|------|----------|----------|
| automatic1111/stable-diffusion-webui | `deep-learning` 包含 `learning` | 工具 |
| microsoft/powertoys | `collection` 被误判 | 工具 |
| ringhyacinth/star-office-ui | `work states` 包含 `learning` | 工具 |
| taigrr/spank | `yells back` 包含 `book` | 工具 |

**修复方法**: 使用 `all_text.split()` 进行完整词匹配，避免子串误判。

---

## 六、GitHub API 使用规范

### 必须配置
```bash
# .env 文件
GH_TOKEN=ghp_xxxxxxxxxxxx
```

### 速率限制
- 认证用户: 5000次/小时
- 匿名: 60次/小时
- 建议: 每条记录间隔 200ms

### 错误处理
```python
if r.status_code == 403:
    time.sleep(10)  # rate limit 等待
    # 重试
elif r.status_code == 404:
    # 仓库不存在，跳过
```

---

## 七、相关脚本

| 脚本 | 用途 |
|------|------|
| `sync_gh_repos.py` | 主同步脚本，含自动类型判断 |
| `fix_gh_quality_desc.py` | 批量修复描述质量 |
| `fix_gh_type_direct.py` | 修复 Stars/Fork数类型 |
| `fill_missing_gh_data.py` | 补齐缺失数据 |

---

## 八、统一入口

- **cron**: `deb7e428f689` (daily-content-research)
- **步骤**: 步骤 10.5 "飞书 GitHub 入库"
- **已暂停**: `JOB_ID` (冗余 cron)

---

## 九、数据质量检查

运行以下命令检查数据质量:
```bash
python3 ~/.hermes/scripts/daily_briefing_check.py $(date +%Y-%m-%d)
```

检查项:
- 理由含星数: 0 条
- 英文描述: 0 条
- 空项目类型: 0 条
- 空推荐理由: 0 条
- 泛泛描述: 0 条
- 项目类型误判: 0 条
