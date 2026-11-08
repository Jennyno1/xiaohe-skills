# GitHub 星数核实 — shields.io 兜底（2026-08-29 实证）

## 问题
内容研究简报要求每个 GitHub 项目的 ⭐ 数必须用 `api.github.com/repos/{owner}/{repo}` 的 `stargazers_count` 整数核实（铁律：API+GH_TOKEN 为首选）。但在共享 IP 或 token 配额耗尽时，REST API 返回 HTTP 403（`API rate limit exceeded`）；token 过期返回 401（`Bad credentials`）。此时无法拿到整数星数。

## 兜底方案
改用 `shields.io` 公开徽章接口取星数——它是不消耗 GitHub 配额的独立公共服务，限流时稳定可用：

```bash
curl -s "https://img.shields.io/github/stars/{owner}/{repo}.json"
# => {"label":"stars","message":"61k","color":"blue","link":[...],"name":"stars","value":"61k"}
```

取 `value` / `message` 字段（如 `61k`、`7.3k`）。这是 GitHub API 实时星数经显示层四舍五入的值，非 trending HTML 或页面缓存值。

## 用法纪律
1. 首选仍是 REST API（`Authorization: Bearer $GH_TOKEN`）拿 `stargazers_count` 整数。
2. 仅当 403/401 时才降级到 shields.io。
3. **🔴 报告里禁止出现技术验证说明**（如"star 数经 shields.io 实时徽章核实；GitHub REST API 当日触发 IP 限流"）——用户明确要求报告干净，这类元信息不应出现在读者面前。2026-08-29 用户纠正。
4. 徽章值是四舍五入显示值（61k/7.3k），与简报 `⭐XXK` 展示格式天然一致；若后续需精确整数，等配额恢复后用 `api.github.com` 补一次。
5. 禁止把 shields.io 当首选源、禁止谎称「已用 API 核实」。
6. **🔴 必须用 GH_TOKEN**：匿名请求只有 60次/小时 core + 10次/分钟 search，几下就限流。带 token 认证后 core=5000/小时。2026-08-29 实测：子代理不带 token 直接 403，加 token 后正常。

## 实测（2026-08-29）
- GitHub REST API（共享 IP，无 token）：HTTP 403 rate limit，无法取数。
- shields.io：`microsoft/autogen` → 61k、`guardrails-ai/guardrails` → 7.3k、`vllm-project/vllm` → 90k，全部成功。
- 同一会话内 shields.io 多次调用稳定，未被限流。
- 注意：`google-deepmind/synthid` 经 shields.io 返回 `repo not found`，说明该路径下仓库不存在——shields.io 也可顺带验证 repo 是否存在。
