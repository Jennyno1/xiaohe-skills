# 静态站 UI 改动：真机验收配方

目的：改完 UI（布局/样式/可达性/交互）后，用**量数**证明改到位，而不是靠看图。适用于 `Jennyno1/ai-briefing-site` 这类纯静态站（HTML/CSS/原生 JS + `data/*.json`）。

## 0. 前置：本地起服务（必做）
```bash
# 发布集目录里跑（构建产物）
python3 ~/.hermes/scripts/build_site_publish.py --src <site 源目录> --out /tmp/site_pub --json
cd /tmp/site_pub && python3 -m http.server 8899   # 后台跑
```
⚠️ **不要用 `file://` 打开**：页面里的 `fetch('data/manifest.json')` 会被浏览器拦，页面停在加载态，量到的是空页（会得出「全页无内容」的假结论）。

## 1. 量布局与可达性（browser_exec + CDP）
```python
cdp('Emulation.setDeviceMetricsOverride', width=390, height=844, deviceScaleFactor=2, mobile=True)
js("new Promise(r=>setTimeout(r,400))")          # 等渲染完再量
print(js("""(() => {
  const de = document.documentElement;
  const t  = document.getElementById('theme-toggle').getBoundingClientRect();
  return JSON.stringify({
    viewport: de.clientWidth,
    overflow: de.scrollWidth - de.clientWidth,        // 验收线：== 0
    toggleRight: Math.round(t.right),                  // 验收线：<= viewport
    toggleH: Math.round(t.height),
    btnH: Math.round(document.querySelector('.d-btn').getBoundingClientRect().height),  // >= 44
    vpFont: getComputedStyle(document.querySelector('.vp-card h3')).fontFamily.slice(0,30)
  });
})()"""))
cdp('Emulation.clearDeviceMetricsOverride')      # 再测桌面
```
常用量：`scrollWidth` vs `clientWidth`、控件 `rect.left/right`（是否被挤出屏）、`getComputedStyle(...)` 的 `borderRadius/borderTopWidth/fontFamily/fontSize/backgroundColor`、`::after` 的 `inset`（热区扩展）。

## 2. 验交互（事件派发，不靠手点）
```python
# 焦点在目标容器外 → 不应被劫持；容器内 → 应生效
js("document.body.focus(); document.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true}))")
# 比 before/after 的 aria-current 值即可
```
也可以直接验状态：`document.querySelector('.d-btn[aria-current]').getAttribute('data-date')`（应等于 `aria-current="date"` 的那期）。

## 3. 长图存证 + 空图自检（自己看不到图时必须做）
```python
import base64
r = cdp('Page.captureScreenshot', format='png', captureBeyondViewport=True)
open('/tmp/site_dark.png','wb').write(base64.b64decode(r['data']))
```
```python
from PIL import Image
im = Image.open(p).convert('L')
px = list(im.getdata())
print(im.size, sum(px)/len(px), sum(1 for c in im.histogram() if c>0))
# 浅色整页灰度均值 ~240、深色 ~32、灰阶覆盖 200+ = 有真实内容；接近 255/0 且灰阶数极少 = 白/黑图
```
交付时按「过程物 → 群文件」发，不要塞云盘归档夹。

## 4. 改前必查的三类「静默坏法」
```bash
# ① 改了标签/类名 → 样式表里旧标签选择器还在吗（存在即整条样式作废）
grep -n "\.vp-card h4\|\.vp-card h3" style.css
# ② 收敛了 token（圆角/颜色）→ @media 块里还有硬编码覆盖吗
grep -n "border-radius" style.css
# ③ 用了变量 → 它真的定义过吗（未定义会静默回退）
grep -n -- "--radius-ctl\|--hairline-strong" style.css
```

## 5. 验收线速查
| 项 | 线 | 量法 |
|---|---|---|
| 窄屏无横向滚动 | `scrollWidth - clientWidth == 0` | CDP 390px 视口 |
| 关键控件可见可点 | `rect.right <= viewport && rect.left >= 0` | 同上 |
| 触控目标 | computed height ≥ 44px | 同上（本体不能变大就扩热区） |
| 语义标签样式落地 | computed font-family/font-size == 设计值 | 改标签后必查 |
| 对比度 | 正文 ≥ 4.5:1，图形/大字号 ≥ 3:1 | 两色亮度公式，深浅两套都算 |
| 键盘作用域 | 容器外不响应、容器内响应 | 事件派发 + 状态对比 |
| 历史栈 | 首载 `replaceState`、交互 `pushState` | 读代码 + 点一次看 hash |

## 6. 三条“看起来改对了”的隐患（实测踩过）

1. **没写规则的元素会静默退回浏览器默认**。同类元素只有部分模块显式写了字体规格时，漏掉的那个会拿到 UA 默认（`h2` = 700 加粗 + `1.5em` 字号 + 继承正文行高），远看像“这个模块的标题格外重”。
   - 查法：把同类元素全部量一遍（`fontSize/fontWeight/fontFamily/lineHeight` 四个一起量），**出现不一致的先列出来**，不要凭看图判断是设计意图。
   - 修法：把完整规格写进**共用选择器**（如 `.sec-head h2`），而不是逐个模块打补丁——否则下次新增模块又漏。
2. **对齐的验收线是“正文列边界”，不是整页框架**。顶栏动作区、页脚、区块边缘要对齐的是**正文列的 left/right**，不是 `body` 的内边距。量法：先取一个正文段落或正文容器的 `rect.left/right` 作为基准，再量待对齐元素，**偏差应为 0**；同时把两侧都量（常见错法：只对了一边，另一边差出一百多像素，或对齐了整页框架而没对齐正文列）。
3. **降低视觉权重靠色阶，不靠 `opacity`**。页脚/次级文字要“弱化”时，先算出目标灰在白底/深底下的实色对比度：用 `opacity` 会把实际渲染对比度压到 AA 线（4.5:1）以下，而用**恰好在线上方的专档灰**（深浅各一个 token）既更安静又不丢可读性。验收时把两套主题的对比度都算一遍，别只算浅色。

对比型双块（如“共识/分歧”类并列模块）的交付验收：两块**各自独立底色**（共用一个底色看不出对比，会被打回）+ 块间留间距 + 标题色点与各自底色同源；底色挂内容盒而不是整个 section，否则板块头会被推得不与其余板块对齐。
