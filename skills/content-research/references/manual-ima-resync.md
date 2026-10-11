# 手动重新同步 IMA 笔记（用户编辑日报后）

## 场景

用户手动编辑 `~/hermes-output/content-research/content-research-YYYY-MM-DD.md`（如补充推荐阅读模板、修正内容），需要重新同步到 IMA 笔记。

## 先核验：用户报「IMA 没同步」时，先取证再动手

用户的报障 ≠ 事实。直接跑 `ima_sync.py` 很危险——若笔记其实已存在，你会在库里留下一篇**删不掉**的重复（OpenAPI 无删除接口）。先做**只读取证**（三步，约一分钟）：

1. 按**日期串** `M月D日` 调 `search_note`（`search_type=0` 标题检索，`start=0,end=20`；end 上限 20，调大报 100001）拿 `note_id`
2. 用同一套 `.env` 凭证调 `get_doc_content`（`target_content_format=0`）读回正文，断言**完整版标志**在：`❶/❷/❸`、`📊 最大共识与分歧`、`📖 推荐阅读`、`引用1`
3. 记下 `create_time` / `modify_time`（Unix 毫秒）——它证明同步发生在当天 06:0x，而不是刚补的

回复时**给证据**（note_id + 创建时间 + 正文字数 + 命中的模块），再问「你是在哪儿没看到」。没有取证就回「已修复/已重导」等于赌。

### 最可能的假报障原因：笔记标题随报告 H1 漂移

笔记标题**不是固定格式**，它来自报告 H1：历史上是「📋每日简报 · M月D日」，改版后变成「每日内容研究简报 · M月D日」。用户按旧习惯在客户端搜「📋每日简报」→ 只搜得到改版以前的笔记 → 自然地报「最近几天没同步」。

- 所以 `ima_sync.py` 的幂等键是**日期串 `M月D日`**，而不是完整标题——**不要**把它「修」回按完整标题检索，那正是早前反复产生重复导入的根因。
- 同理 `daily_briefing_check.py` 的 IMA 校验：搜索词写的是「每日简报 · M月D日」，真正生效的是它对标题里 `M月D日` 的过滤——别因为「搜索词看起来对不上」去改它。
- 用户报「找不到笔记」时，先分清三种情况再动手：**① 标题漂移搜不到**（笔记在）／**② 当天根本没跑**（搜索无命中）／**③ 笔记在但内容不全**（回读断言不过）。三种处置完全不同。

## 工作流

### 1. 定位日报文件

日报文件路径：`~/hermes-output/content-research/content-research-YYYY-MM-DD.md`

> 注意：cron 输出目录 `~/.hermes/cron/output/deb7e428f689/` 下也有同名文件，但 IMA 同步脚本读取的是上面的路径。

### 2. 执行 IMA 同步

```bash
python3 ~/.hermes/skills/digital-twin/content-research/scripts/ima_sync.py $(date +%Y-%m-%d)
```

成功返回：`OK note_id=XXXXX`

### 3. 验证同步结果（用与同步脚本同一套凭证）

⚠️ 不要用 `ima_api.cjs` + `~/.config/ima/*` 那套凭证——实测返回 `200002 skill auth failed`，会让人误判成“同步失败/鉴权坏了”。**审计脚本的凭证要与写入脚本同源**：

```python
# 与 ima_sync.py 同一套：HTTP header 传 ~/.hermes/.env 里的凭证
env = {}
for line in open(os.path.expanduser('~/.hermes/.env'), encoding='utf-8'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1); env[k.strip()] = v.strip().strip('"').strip("'")
H = {'Content-Type': 'application/json',
     'ima-openapi-clientid': env['IMA_OPENAPI_CLIENTID'],
     'ima-openapi-apikey': env['IMA_OPENAPI_APIKEY']}
# POST https://ima.qq.com/openapi/note/v1/get_doc_content
#      {'note_id': note_id, 'target_content_format': 0}
```

**回读必须按内容关键字断言，不能按结构断言：**

1. **先断 `len(content) > 0`**——空回读会让「不含 X」类断言**真空通过**，把「没读到」当成「已修好」（踩过：0 字符回读下“已清除”判定全绿）
2. 纯文本回读（`target_content_format: 0`）会**丢掉 emoji/`##` 等标记**，按 `## 🎯` 解析会得到 0 条而误判成“内容缺失”；改为断言**期望出现的正文关键词**（如要点里的专有名词、赛道名）
3. 最后再断言**不该出现的词已消失**（被修的异常措辞）

## 常见场景

| 场景 | 操作 |
|------|------|
| 补充推荐阅读模块 | 编辑文件 → 运行 ima_sync.py |
| 修正赛道内容 | 编辑文件 → 运行 ima_sync.py |
| 格式调整 | 编辑文件 → 运行 ima_sync.py |
| 重新生成完整版 | 删除旧文件 → 触发 cron → 验证 |
| 已定稿需要重推（当天笔记已存在） | 直接跑 ima_sync.py，幂等会命中 `SKIP`；需覆盖时不要盲目 `--force`（会多出一篇且删不掉），改走“让用户删旧篇后重导” |

## 陷阱

- **同日重复笔记**：`ima_sync.py` 的幂等原先按标题「📋每日简报 · M月D日」检索，但笔记实际标题是报告 H1「每日内容研究简报 · M月D日」→ 搜不到当天笔记 → 又导入一篇。已改为按「M月D日」检索。**若已产生重复，IMA OpenAPI 无删除接口**（只有 search/list/get/import/append），需在 IMA 客户端手动删除旧的那篇。
- **重同步前先看幂等有没有命中**：输出 `OK note_id=…` 说明**没命中**、又新建了一篇；`SKIP note_id=…` 才是命中。先手工 `--force` 会直接制造重复。
- **文件路径混淆**：cron 输出目录的文件是 agent 生成的原始版本，用户编辑的是 `~/hermes-output/content-research/` 下的版本。IMA 同步读取后者。
- **旧文件阻塞**：如果用户编辑后 cron 又重新生成了文件，会覆盖用户的手动编辑。操作前确认文件时间戳。
