# last30days + Tavily 多平台调研集成

## 架构

```
research_merge.py (统一入口)
  ├─ last30days 引擎 → Reddit + HN（免费，社区信号）
  └─ Tavily API → YouTube + X/Twitter（需 API key）
```

**脚本路径**：`~/.hermes/scripts/research_merge.py`
**输出目录**：`~/hermes-output/research/`

## 用法

```bash
TAVILY_API_KEY="tvly-dev-xxx" python3 ~/.hermes/scripts/research_merge.py "话题" --days 7
```

## 安装 last30days

```bash
git clone https://github.com/mvanhorn/last30days-skill.git ~/last30days-skill
mkdir -p ~/.hermes/skills/research
ln -sf ~/last30days-skill/skills/last30days ~/.hermes/skills/research/last30days
```

## 配置

### yt-dlp（YouTube 搜索）
引擎用 `--ignore-config`，配置文件不生效。需创建 wrapper：
```bash
cat > ~/.local/bin/yt-dlp << 'EOF'
#!/bin/bash
exec ~/.hermes/hermes-agent/venv/bin/yt-dlp --js-runtimes node "$@"
EOF
chmod +x ~/.local/bin/yt-dlp
```

### Reddit
服务器无浏览器，用 keyless 模式：
```bash
# ~/.config/last30days/.env
LAST30DAYS_REDDIT_BACKEND=keyless
```
403 警告可忽略，arctic-shift 补充路径正常工作（每次7-12条）。

### X/Twitter
需 API key 或浏览器 cookie。无 key 时跳过，用 Tavily 补。

## 已知限制

| 平台 | 状态 | 限制 |
|---|---|---|
| HN | ✅ | Algolia 免费 API |
| Reddit | ✅ | keyless 模式，403 警告可忽略 |
| YouTube | ⚠️ | 搜索能出标题，`--dump-json` 被 bot 检测拦截（需 cookies） |
| X/Twitter | ❌→✅ | 引擎需 API key；Tavily 可搜到（补缺） |
| Polymarket | ✅ | Gamma API 免费 |

## Python 版本

引擎需 **Python 3.12+**。Hermes venv 是 3.11，脚本中必须用 `python3.12` 显式调用，不能用 `sys.executable`。

## 四平台定位差异

| 平台 | 用户画像 | 选题价值 |
|---|---|---|
| HN | 硅谷工程师/创始人 | 前沿技术趋势 |
| Reddit | 全球普通人 | 真实痛点和吐槽 |
| X/Twitter | 媒体人/投资人/KOL | 热点事件和行业争论 |
| YouTube | 全网普通用户 | 验证话题热度（有人做视频=有需求） |
