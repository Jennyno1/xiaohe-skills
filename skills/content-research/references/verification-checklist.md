# 简报验证清单

## 手动测试后必跑（2026-08-20 实证，08-31 补充）

1. 检查 `~/hermes-output/content-research/content-research-YYYY-MM-DD.md` 时间戳和大小是否为新生成
2. 检查 `最大共识与分歧`模块是否出现 `## 📊` / `### 🔵` / `### 🔴` 标题
3. 检查引用事件是否为 `▸ 引用N：` 格式并单独分行
4. 检查 `/tmp/all_deduped.json` 素材总数是否 ≥30 条、来源是否 ≥3 个
5. **📖推荐阅读必须存在**：`grep "📖" content-research-YYYY-MM-DD.md` 返回结果 ≥1

> ⚠️ 2026-08-31 实证：mimo-v2.5 在长文生成时会跳过最后一个模块（📖推荐阅读），需手动检查后补写。这是 flash 模型的已知弱点，pro 模型较少出现。

## Cron 自动执行后检查

```bash
# 检查模块完整性
BRIEFING=~/hermes-output/content-research/content-research-$(date +%Y-%m-%d).md
for emoji in "🎯" "🤖" "💼" "🎨" "⭐" "📊" "📖"; do
  count=$(grep -c "$emoji" "$BRIEFING" 2>/dev/null)
  echo "$emoji: ${count:-0} 次"
done
```
