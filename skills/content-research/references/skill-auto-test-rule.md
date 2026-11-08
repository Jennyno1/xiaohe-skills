# Skill 修改后自动测试规则

## 触发条件

修改 content-research 技能（SKILL.md / scripts/ / references/）后自动触发。

## 验证清单

每次修改后必须执行以下验证，发现问题自动修复：

### 1. SKILL.md → 脚本一致性
- SKILL.md 中新增的信源/路由/字段名，同步检查 `parse_all_feeds.py` 是否已更新
- 新增的 curl 拉取命令是否在步骤1中存在
- 新增的解析逻辑是否在步骤3的 inline script 中存在

### 2. 模板完整性
- 输出模板中的所有模块（🎯 / ❶❷❸📌🔍💡 / 🛠️ 项目推荐 / 📎 推荐阅读 / 信息源+日期）是否都在
- 模板格式是否符合当前铁律（赛道内不放链接、①②编号、▸列表、底部信源）

### 3. 配置一致性
- 信源表（L1/L2/L3 表格）与拉取命令（步骤1）条目数是否一致
- RSSHub 路由列表与步骤4 的命令是否一致

### 4. 功能测试
- 跑一遍 `python3 parse_all_feeds.py` 确认能解析不报错
- 检查新增信源的输出条目是否出现在 deduped 结果中

### 5. Cron 同步检查
- 修改 skill 后，cron job 的 embedded prompt 不会自动更新
- 需要手动 `cronjob action=update` 刷新 cron 的 prompt 和 model 配置

## 铁律

修改任何 skill 后，必须先跑验证再报告完成。发现问题自动修复，不留到用户指出。
