# GitHub 项目入库 - 踩坑记录与修复档案

> 创建时间: 2026-09-08  
> 状态: 已完成修复

---

## 一、问题发现过程

### 1.1 初始问题 (用户提供截图反馈)
用户发现以下问题:
- 项目描述是 `"项目名 - AI Agent 相关开源项目"` 这种泛泛之谈
- 推荐理由包含星数 (如 `⭐162k`)
- 项目类型判断错误 (如 stable-diffusion-webui 被判断为"书籍")

### 1.2 根本原因分析
1. **泛泛描述**: 之前的批量修复脚本使用了过于简单的模板 `"项目名 - AI Agent 相关开源项目"`
2. **星数问题**: 未过滤推荐理由中的星数信息
3. **类型误判**: `detect_project_type()` 函数使用子串匹配，导致 `deep-learning` 包含 `learning` 被误判为书籍

---

## 二、修复措施

### 2.1 架构清理

| 操作 | 文件 | 状态 |
|------|------|------|
| 删除本地历史库 | `~/.hermes/recommended-repos.json` | ✅ 已删除 |
| 移除历史库依赖 | `sync_gh_repos.py` | ✅ 已修复 |
| 移除历史库检查 | `daily_briefing_check.py` | ✅ 已修复 |
| 注释历史库引用 | `collect_daily_feeds.sh` | ✅ 已修复 |
| 暂停冗余 cron | `44264f5d1abf` | ✅ 已暂停 |

### 2.2 数据质量修复

#### 修复 1: 理由含星数 (12条)
- 使用 GitHub API 重新获取项目信息
- 生成不含星数的推荐理由
- 成功修复 11/12 条 (deepseek-harness API 404)

#### 修复 2: 英文描述 (60+条)
- 分批调用 GitHub API 获取描述
- 转换为中文格式
- 受 rate limit 限制，分批处理

#### 修复 3: 泛泛描述 (77条)
- 编写 `fix_gh_quality_desc.py` 脚本
- 为知名项目预定义高质量描述
- 其余项目通过 GitHub API 获取并转换

#### 修复 4: 项目类型误判 (4条)
- 发现 `detect_project_type()` 使用子串匹配导致误判
- 案例:
  - `automatic1111/stable-diffusion-webui`: `deep-learning` 包含 `learning` → 误判为书籍
  - `microsoft/powertoys`: `collection` 被误判
  - `ringhyacinth/star-office-ui`: `work states` 包含 `learning`
  - `taigrr/spank`: `yells back` 包含 `book`
- 修复: 改用 `all_text.split()` 进行完整词匹配
- 调整优先级: 书籍移到数据集之后

### 2.3 代码修复

#### `sync_gh_repos.py` 修复
```python
# 修复前 (错误)
if any(kw in all_text for kw in ['book', 'tutorial', 'course', 'learning', ...]):
    return '书籍'

# 修复后 (正确)
# 用完整词匹配，避免子串误判
if any(kw in all_text.split() for kw in ['book', 'textbook', 'e-book']):
    return '书籍'
```

#### 新建修复脚本
- `fix_gh_quality_desc.py`: 质量描述生成
- `fix_gh_type_direct.py`: 类型修复
- `fix_gh_compliance.py`: 合规检查

---

## 三、最终数据状态

### 3.1 规范检查结果
| 检查项 | 修复前 | 修复后 |
|--------|--------|--------|
| 总记录数 | 234 | 233 |
| 理由含星数 | 12 | 0 ✅ |
| 英文描述 | 60+ | 0 ✅ |
| 空项目类型 | 1 | 0 ✅ |
| 空推荐理由 | 1 | 0 ✅ |
| 泛泛描述 | 77 | 0 ✅ |
| 项目类型误判 | 4 | 0 ✅ |

### 3.2 项目类型分布
```
工具: 91条
skill: 83条
框架: 21条
其他: 13条
数据集: 10条
内容源: 8条
平台: 7条
```

---

## 四、规范沉淀

### 4.1 规范文件
- **位置**: `~/.hermes/skills/digital-twin/content-research/references/github-write-rules.md`
- **内容**: 15字段结构 + 7条陷阱规则 + 去重逻辑 + 写入模式 + 类型判断逻辑

### 4.2 自动化防护
- `sync_gh_repos.py` 已内置:
  - `detect_project_type()`: 自动解析项目类型 (已修复)
  - `generate_chinese_desc()`: 自动生成中文描述
  - `generate_reason()`: 自动生成理由 (不含星数)

---

## 五、经验总结

### 5.1 踩坑记录
1. **子串匹配陷阱**: 字符串包含操作 `in` 会匹配子串，必须用 `split()` 分词后匹配
2. **飞书 API 类型陷阱**: Stars/Fork数必须传 int，传 "200K" 会存储异常
3. **GitHub API 限流**: 认证用户 5000次/小时，需合理控制请求频率
4. **历史库混淆**: 本地历史库与飞书表数据不一致，必须以飞书表为权威源

### 5.2 最佳实践
1. **写入前校验**: 检查字段类型、格式、内容质量
2. **分批处理**: 大数据量时分批处理，避免超时
3. **幂等操作**: 使用 upsert 模式，避免重复写入
4. **日志记录**: 记录每次操作的成功/失败状态

---

## 六、后续维护

### 6.1 定期检查
```bash
# 检查数据质量
python3 ~/.hermes/scripts/daily_briefing_check.py $(date +%Y-%m-%d)
```

### 6.2 新写入规范
- 新入库项目自动遵循 `github-write-rules.md`
- `sync_gh_repos.py` 已内置所有规范检查

---

## 附录: 相关文件清单

| 文件 | 用途 |
|------|------|
| `~/.hermes/scripts/sync_gh_repos.py` | 主同步脚本 |
| `~/.hermes/scripts/fix_gh_quality_desc.py` | 质量描述修复 |
| `~/.hermes/scripts/fix_gh_type_direct.py` | 类型修复 |
| `~/.hermes/scripts/fill_missing_gh_data.py` | 缺失数据补齐 |
| `~/.hermes/skills/digital-twin/content-research/references/github-write-rules.md` | 规范文档 |
| `~/.hermes/skills/digital-twin/content-research/references/github-troubleshooting.md` | 本文件 |
