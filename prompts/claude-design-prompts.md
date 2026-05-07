# Claude design 提示词包 —— AI 中转站营销站

> 一站式 AI 模型聚合中转站的完整营销站设计提示词。包含品牌候选、设计系统、6 个分页提示词。
> 使用方式：先用第 0 节选定品牌、第 1 节确认设计系统，再把第 2-7 节逐页投喂给 Claude design。

---

## 0. 品牌候选

请从下面任选一个，作为 `{{BRAND}}` 在后续提示词里替换。

### 主推（推荐度从高到低）

| 候选 | 中文 | 含义 | 与"3D 酒店风"契合度 | 备注 |
|---|---|---|---|---|
| **Prism** | 棱镜 | 一束光经过棱镜分成全光谱 = 一个 API 分发到所有模型 | ★★★★★ | 视觉强项：玻璃折射、彩虹光谱可作为视觉主线；中英双语都自然 |
| **Nimbus** | 流光 / 灵云 | 极光、流体光带；现代感强 | ★★★★☆ | 视觉强项：粒子流体、光带；适合做主视觉动画 |
| **Mesh** | 织 / 网格 | 把所有模型织成一张网 | ★★★★☆ | 视觉强项：3D wireframe 网格；技术圈友好 |
| **Axiom** | 公理 | "AI 世界的公理基础设施"，稳重感 | ★★★☆☆ | 视觉强项：极简几何；偏商务 |
| **百模 / BaiMo** | 百模 | "百模一站"，最直白的中文叙事 | ★★★☆☆ | 适合主打国内市场、不想要英文壳的方案 |

### Slogan 候选（任选 1 主 1 副）

英文向（用作 hero 副标题、社交媒体）：
- "All models. One key."
- "200+ models, one endpoint."
- "The last AI gateway you'll need."
- "Where every model converges."
- "One prism, every spectrum of AI."（仅 Prism 适用）

中文向（用作 hero 主标题、官网正文）：
- "一个 Key，链接所有 AI"
- "所有模型，一个入口"
- "200+ 模型，一个 API"
- "你的 AI 一站式入口"
- "把所有 AI 装进一个 Key"
- "光谱级 AI 网关"（仅 Prism 适用）

**默认推荐组合**（后续提示词使用此组合作为示例）：
- 品牌：**Prism**
- 中文主：**一个 Key，链接所有 AI**
- 英文副：**One prism, every spectrum of AI.**

---

## 1. 设计系统（Master Prompt）

> 这是第一条提示词，先投给 Claude design 让它建立设计系统语境，后续分页 prompt 会复用这套 token。

```
You are designing a marketing site for {{BRAND}} (棱镜 / Prism), an AI gateway
that aggregates 200+ frontier models (GPT-5, Claude Opus 4.5, Gemini 3, Grok,
DeepSeek, Qwen, etc.) behind a single OpenAI-compatible API. Target audience:
Chinese developers, indie hackers, and small AI product teams. Brand tone:
high-tech, premium, slightly playful — think Linear meets Anthropic meets
Vercel, with a dash of Apple keynote 3D motion.

# Design language: "3D Hotel-Lobby Futurism"
The site should feel like walking into the lobby of a futuristic hotel run by
an AI: glassy, luminous, generous in negative space, with deliberate 3D motion
that draws the eye but never blocks reading.

# Color tokens (use as CSS variables)
--bg-base:        #050510   /* near-black with violet undertone */
--bg-surface:     #0B0B1F   /* cards, panels */
--bg-elevated:    #15152E   /* hover/active surfaces */
--border-subtle:  rgba(255,255,255,0.06)
--border-glow:    rgba(139,92,246,0.35)

--text-primary:   #F5F5FA
--text-secondary: #A8A8C0
--text-muted:     #6E6E8C

--accent-violet:  #8B5CF6   /* primary CTA */
--accent-cyan:    #06B6D4   /* secondary highlight */
--accent-magenta: #EC4899   /* tertiary highlight, prism dispersion */
--accent-amber:   #F59E0B   /* status / pricing emphasis */

# Iridescent gradient (the brand's signature)
linear-gradient(135deg, #8B5CF6 0%, #06B6D4 35%, #EC4899 70%, #F59E0B 100%)
Use this gradient on: hero headline accent words, primary CTA, model-card
borders on hover, the prism logo itself.

# Typography stack
- Display: "Sora", "Geist", "Inter Tight", system-ui, sans-serif
  (weight 600-800, slight negative letter-spacing for headlines)
- Body: "Inter", "思源黑体 / Source Han Sans CN", system-ui
  (weight 400-500, line-height 1.65)
- Mono: "JetBrains Mono", "IBM Plex Mono", monospace
  (used for code blocks, model IDs, API endpoints)

# Motion language
- Default easing: cubic-bezier(0.16, 1, 0.3, 1)  /* "ease-out-expo" */
- Default duration: 600ms for entrance, 200ms for hover
- Hero: a slowly rotating glass prism (Three.js / R3F), refracting an
  incoming light beam into a 7-color spectrum that fans out behind the
  headline; the spectrum lines morph into the logos of supported models.
- Section transitions: parallax with depth-of-field blur as user scrolls
- Hover states: subtle 1.02x scale + glow halo (radial-gradient blur)
- CTA: pulsing iridescent glow at 2s interval, accelerates on hover

# 3D & WebGL elements (must include at least 3 of these)
1. Hero: rotating glass prism with light dispersion (Three.js)
2. Models section: floating 3D cards in a curved arc, each with the model's
   provider logo embossed; mouse-track parallax
3. Pricing section: liquid metal sphere that morphs as you toggle pricing tier
4. Architecture section: animated SVG/WebGL diagram of "user → Prism gateway →
   60+ providers", with packets flowing along edges
5. Background: subtle starfield + slow-drifting nebula clouds (low opacity)
6. Section dividers: a sweeping iridescent light beam scrolling horizontally

# Layout primitives
- Container max-width: 1280px, side padding 24px (mobile) / 64px (desktop)
- Grid: 12-col with 24px gutter
- Card radius: 16px (large), 12px (medium), 8px (small)
- Border style: 1px solid var(--border-subtle), with var(--border-glow) on hover
- Shadow: soft inner glow on dark surfaces, never harsh drop shadows

# Accessibility & quality bar
- All animations honor prefers-reduced-motion
- Color contrast AA on all body copy
- Bilingual ready: every block must accept both Chinese and English variants;
  Chinese is primary, English subtitle in --text-secondary
- Mobile-first responsive, breakpoints at 640 / 768 / 1024 / 1280

# Content tone
- Chinese: 简洁、有力、不油腻，避免营销腔；可以有少量"开发者梗"
- English: confident, technical, never marketing-fluffy
- Numbers always concrete: "200+ 模型" not "海量模型"; "p50 延迟 < 380ms"
  not "极速响应"
```

---

## 2. 首页（Homepage / Landing Page）

```
Design the homepage of {{BRAND}} using the design system established earlier.
Single long page, scrolls vertically, with these sections in order:

## Section 1: Hero (full viewport height, 100vh)
- Top-left: brand mark (a stylized prism that disperses a light ray)
- Top-right: nav links — "模型 Models", "定价 Pricing", "文档 Docs",
  "控制台 Console", with a [立即开始 / Get Started] primary CTA button
- Center-left: massive headline (display, 72-96px desktop, 40-48px mobile):
  "一个 Key，链接所有 AI"
  with the words "所有 AI" rendered in the iridescent gradient with
  a subtle prism-refraction shimmer
- Subheadline (Inter 20-24px, --text-secondary):
  "GPT-5 · Claude · Gemini · DeepSeek · Qwen · Grok ——
   200+ 前沿模型，一个 OpenAI 兼容 API 直连"
- English subtitle (mono, --text-muted, smaller):
  "One prism, every spectrum of AI."
- CTA group:
  - Primary [立即注册 · 充 1 万到账 9995] in iridescent gradient
  - Secondary [查看模型列表] ghost button
- Right side (or behind the headline on a separate z-layer):
  the rotating 3D glass prism, refracting a horizontal light beam
  into a 7-color spectrum that fans out across the viewport
- Bottom: a thin scrolling marquee of provider logos (OpenAI, Anthropic,
  Google, xAI, DeepSeek, Moonshot, Zhipu, Alibaba, ...) at 50% opacity,
  drifting right-to-left

## Section 2: Trust strip (compact, ~120px tall)
A single row of 4-6 metrics, each a number + caption:
- "200+ 模型"
- "60+ 上游 provider"
- "p50 延迟 < 380ms"
- "99.95% 可用性"
- "对公开票 · 数据不出境"
Numbers in display font, captions in body. Subtle vertical dividers.

## Section 3: 为什么选 {{BRAND}}（Features grid, 3×2）
Six feature cards in a grid. Each card: icon (animated SVG), title,
2-line description. On hover, card lifts with iridescent glow border.

1. **多模型一个 Key** — 200+ 模型同一接口，切换只需改 model 字段
2. **OpenAI 完全兼容** — Claude Code / Cursor / Codex / ChatBox 一键接入
3. **路由智能 + 故障自动切换** — 多 provider 加权负载，30s 内自动 failover
4. **明牌定价 · 无暗扣** — 模型倍率全公开，不偷换不降级
5. **企业合规** — 对公收款 · 增值税专票 · 数据不出境承诺
6. **可观测面板** — 实时用量、p50/p95、按 Key/Project 拆分

## Section 4: 接入演示（Live demo / code section）
Left side: 一行代码切换模型. A code block with tab switcher
"Python | Node.js | curl". Pre-filled with a working example:

  from openai import OpenAI
  client = OpenAI(
      base_url="https://api.{{BRAND}}.ai/v1",
      api_key="sk-..."
  )
  resp = client.chat.completions.create(
      model="claude-opus-4.5",   # ← change to gpt-5 / gemini-3-pro / ...
      messages=[{"role":"user","content":"Hello"}]
  )

Right side: a "live" terminal mock that streams the response with a typing
animation, showing latency and cost in real time at the bottom.

## Section 5: 支持的客户端（Client matrix）
A horizontal row of "tile" cards, each showing a popular client logo:
Claude Code, Cursor, Codex, Continue, Cline, ChatBox, LobeChat, FastGPT,
ChatWise, Aider. On hover, the tile flips to show a one-line config snippet
(e.g. for Claude Code: ANTHROPIC_BASE_URL=https://api.{{BRAND}}.ai/anthropic).

## Section 6: 模型预览（Models preview, scrollable）
A horizontal carousel of model cards with the iridescent gradient border on
hover. Each card: provider logo (top-left), model name (display font),
context window, input/output price, [开始使用] mini-CTA.
Show ~6 cards visible, with [查看全部 200+ 模型 →] link to /models.

## Section 7: 定价预览（Pricing preview）
2-column comparison: Self-serve / Team.
Self-serve: 按量付费 / 0% 加价 / 万 5 手续费（充 10000 到账 9995）/ 全部 200+ 模型 / 高优先级路由 + prompt cache 透传 / 邀请返佣 5%
Team: 对公合同 / 增值税专票 / 私有上游渠道 / SLA 99.95% / 专属客户经理 / 数据不出境承诺
Each card has a [查看完整定价 →] link. **没有 Free 档**（不送免费额度，第一笔就是充值）。

## Section 8: FAQ（Accordion, 6-8 items）
- {{BRAND}} 和直接调官方 API 有什么区别？
- 价格是怎么算的？有没有暗扣或降级？
- 能开发票吗？支持对公收款吗？
- 我用 Claude Code / Cursor / Codex 能直接接入吗？
- 数据会被训练吗？日志保留多久？
- 出现故障怎么办？SLA 是什么？

## Section 9: Final CTA
Massive iridescent gradient banner: "充 1 万到账 9995 · 立刻接入 200+ 模型"
with [立即注册] CTA and small print "0% 加价 · 万 5 手续费 · 微信/支付宝/USDT/对公全通道"

## Section 10: Footer
- Brand mark + 一句话定位
- Columns: 产品 / 文档 / 公司 / 法律
- 备案号占位、社交链接（GitHub / Twitter / 即刻 / 知乎 / 公众号二维码）
- 底部版权 + bilingual switch

# Important
- Hero 3D prism is the centerpiece — it must be visually impressive even on
  mid-tier laptops; provide a static fallback for prefers-reduced-motion
- Every section has subtle parallax + scroll-triggered fade-in
- The page should be scannable in 30 seconds but reward deeper reading
```

---

## 3. 模型列表页（Models）

```
Design the /models page of {{BRAND}}. This is the page where developers
research and pick a model. Inspired by openrouter.ai/models, but with
the 3D-hotel-lobby aesthetic.

## Layout
- Top: title "200+ 模型，按需选择" + subtitle "All major frontier and open
  models in one place"
- Below title: filter bar (sticky on scroll):
  - Provider chips (OpenAI / Anthropic / Google / xAI / DeepSeek / Moonshot /
    Zhipu / Alibaba / Meta / Mistral / Cohere / Qwen / ...)
  - Capability chips (Chat / Tool use / Vision / Audio / Embeddings / Reasoning)
  - Sort dropdown (Recommended / Cheapest / Lowest latency / Newest)
  - Search input (model name / id)

## Model grid
Card grid, 3-col desktop / 2-col tablet / 1-col mobile. Each card:
- Provider logo (top-left)
- Model name (display, e.g. "Claude Opus 4.5")
- Model ID in mono (e.g. "anthropic/claude-opus-4.5")
- Tags row: context window (e.g. "200K"), modality icons
- Pricing line: "$15 / $75 per 1M tokens (in/out)"
- Latency badge: "p50 420ms" with green dot
- Capabilities: tool use ✓ vision ✓ cache ✓
- [Try it →] button that opens a side-drawer playground

Card has the iridescent gradient border on hover, and a soft 3D tilt
effect tracking the cursor (max 8deg). Background of each card is
a subtle gradient unique to its provider color.

## Side drawer (when [Try it] clicked)
Slides in from the right, 480px wide. Contains:
- Model header (logo, name, id)
- Tabs: "Playground / Code / Pricing detail / Channels"
- Playground: simple chat input, streams response
- Code: copy-paste snippets in Python/Node/curl
- Channels: ⚠️ TRANSPARENCY FEATURE — list the actual upstream channels
  this model is routed to (e.g. "Anthropic 官方 API · Bedrock us-west-2 ·
  Vertex europe-west4"), with health/latency/policy badges
- Pricing detail: input price, output price, prompt cache price (if any),
  multiplier vs official

## Important
- The "Channels" transparency tab is a brand differentiator — show it
  prominently and tastefully
- Performance: virtualize the grid if more than 60 cards visible
- Empty state when no filter matches: a sad rotating prism + "未找到匹配模型"
```

---

## 4. 定价页（Pricing）

```
Design the /pricing page of {{BRAND}}. Tone: confident transparency.

## Hero strip
"充 1 万到账 9995 · 0% 加价 · 万 5 手续费"
Subtitle: "Inference 全部按上游真实成本结算，万分之五手续费仅覆盖银行通道费。"

## Section A: 两档套餐对比（Plan comparison）
Two large cards side-by-side. **没有 Free 档**：注册不送 token，第一笔就是充值。

### Self-serve  ← featured
- 按量付费，0% 加价
- 充值手续费 0.05%（充 10000 到账 9995）
- 全部 200+ 模型 · OpenAI / Anthropic / Gemini 协议
- 高优先级路由 + prompt cache 透传
- 限速按累计充值阶梯 60 → 1200 RPM
- 支付宝 / 微信 / USDT 充值
- 5% 邀请返佣
- [立即注册]

### Team
- Self-serve 全部能力
- 对公收款 + 月结合同 + 增值税专票
- 私有上游渠道（独占容量）
- SLA 99.95% + 7×24 工单
- 专属客户经理 + 数据不出境承诺
- [联系销售]

## Section B: 模型倍率明细表（Model rate table）
Tagline: "每个模型的真实成本都在这里。我们一分钱不加。"
A clean table with sticky header:
| 模型 | 上下文 | 输入 (¥/M tokens) | 输出 (¥/M tokens) | vs 官方 | Prompt cache | 上游渠道 |
Show top 20 popular models. 「vs 官方」一栏永远是「= 一致」。Below table: "查看全部 200+ 模型 →"
link to /models.

## Section C: 充值方式
A row of icons: 支付宝 / 微信支付 / USDT / 对公转账 / Stripe (海外)
Below: "最低充值 $5 · 万分之五手续费 · 余额永不过期 · 7 天无理由退款"

## Section D: 倍率计算演示（Live calculator）
A small interactive widget:
- Dropdown: 选择模型
- Input: 输入 token 数（input + output）
- Output: 实时计算的人民币 / 美元价格 + "vs 官方价格 -X%"

## Section E: 企业 / 团队 FAQ
- 能开增值税专票吗？什么时候开？
- 数据会被训练吗？我们的合规承诺是什么？
- 私有渠道是什么意思？
- 如何申请月结合同？
- 有 SLA 赔付吗？

## Visual notes
- Section A 的 Team 卡片应该有 subtle 3D 倾斜，比另外两个稍微"重"一点
- Section B 的表格鼠标 hover 一行时，该行 background 出现 iridescent 微光
- Section D 的 calculator 输出数字时有 count-up 动画
```

---

## 5. 文档入口页（Docs landing）

```
Design the /docs landing page. Real docs may live elsewhere (Apifox /
Mintlify / GitBook), this page is the curated entry point.

## Hero
"开始使用 {{BRAND}} · 5 分钟接入"
Three big cards: "Quick Start" / "客户端接入" / "API 参考"

## Section: Quick start (3 steps)
Step 1: Sign up & get API key (with screenshot mock)
Step 2: Replace base URL — code snippet for Python/Node/curl
Step 3: Make your first call — code snippet + animated terminal output

## Section: 客户端接入矩阵
Grid of 10-12 client logos (Claude Code, Cursor, Codex, Continue, Cline,
ChatBox, LobeChat, FastGPT, Aider, OpenWebUI, ChatWise, Dify). Each card,
when clicked, expands to show the env vars / config snippet for that client.

This is the "客户端无感切换" differentiator made visible.

## Section: 主题指南卡片
- 错误码与重试策略
- 路由策略与故障切换
- Prompt cache 怎么省钱
- 流式输出 / Tool use / Vision
- BYOK（自带 Key）
- 用量监控与计费

Each card with a small animated icon, minimal copy, link to the deep doc.

## Section: SDK / 开源组件
GitHub-style card row showing official SDKs and code samples:
- {{BRAND}} Python SDK
- {{BRAND}} TypeScript SDK
- {{BRAND}} CLI
- 示例仓库（带 ⭐ 数）

## Footer area
"找不到答案？" → 加入开发者社群 (Discord / 飞书 / 微信群二维码) + 工单
```

---

## 6. 控制台（Console / Dashboard, post-login）

```
Design the post-login console at /console. This is where developers
manage their account day-to-day. Same dark aesthetic but more functional;
3D motion is dialed down to ~30%.

## Layout
- Left sidebar (240px): logo, nav (Overview / API Keys / Models /
  Usage / Billing / Logs / Settings), bottom user pill
- Top bar: search, balance display (with [充值] CTA), notifications, user menu
- Main: page content area

## Overview page (default landing)
- Top row: 4 metric cards
  - 当前余额 ($X.XX) [充值]
  - 本月调用 (3.2M tokens)
  - 本月成本 (¥248.50)
  - 平均延迟 (412ms)
- Middle: 双轴图表 — 调用次数（柱）+ 成本（线）, last 30 days
  Use the iridescent gradient on the line, neutral gray on bars.
- Right side panel: "最近请求" — last 10 requests with status, model,
  tokens, latency, cost
- Bottom: "推荐操作" cards — 第一次接入 / 启用 prompt cache / 邀请好友返佣

## API Keys page
- Table of keys: name, key (masked, hover to reveal copy), created at,
  last used, scope (model whitelist), [禁用] [删除]
- [+ 新建 Key] button opens a modal with: name, model whitelist multi-select,
  rate limit, expiry, IP allowlist

## Usage page
- Filters: 时间范围 / 模型 / Key / Project
- Stacked area chart by model (top 10 + others)
- Heatmap: 24×30 grid of hourly usage for past 30 days
- Table: per-request log with download CSV

## Billing page
- 余额 + 充值历史
- 套餐当前状态
- 发票管理（企业用户）
- 支付方式

## Visual notes
- Console uses --bg-base background but slightly less saturated;
  productivity > spectacle
- Charts: gradient fills with --accent-violet → --accent-cyan,
  tooltips with glass-morphism background
- Empty states: a small dimmed rotating prism + a friendly tip
```

---

## 7. 登录 / 注册（Auth）

```
Design /login and /signup pages for {{BRAND}}.

## Layout
Split-screen: left 60% is the form, right 40% is a tall artistic 3D scene
showing the brand prism from a different angle (slow rotation, ambient).

## Login form
- {{BRAND}} logo top-left
- "登录 {{BRAND}}" headline
- Subtitle: "继续你的多模型 AI 之旅"
- OAuth buttons: GitHub / Google / 微信扫码 / 飞书
- Divider "或使用邮箱"
- Email input + password input
- [登录] iridescent gradient CTA
- Below: 忘记密码 · 还没有账号？立即注册
- Bottom small print: 登录即同意 服务条款 · 隐私政策

## Signup form
- "创建你的 {{BRAND}} 账号"
- Subtitle: "注册后充值即用 · 万分之五手续费 · 0% 加价"
- Same OAuth buttons
- Email + password + 邀请码（选填，标注"使用邀请码双方各得 5% 充值返佣"）
- Checkbox: 我已阅读并同意 服务条款
- [创建账号]
- 下方："邀请好友 · 双方各得 5% 充值返佣"提示卡

## Right side artwork
- 3D prism, rotating 0.05 rad/s, refracting an incoming beam
- Particles drifting upward in the background
- Subtle text overlay quotes (rotating every 8s):
  - "200+ 模型，一个 Key"
  - "Claude Code · Cursor · Codex 全适配"
  - "明牌定价 · 不暗扣 · 不降级"

## Visual notes
- Form fields: 1px border --border-subtle, focus = --border-glow
- Errors in --accent-magenta with shake animation
- Mobile: collapse artwork to a thin top banner with the prism only
```

---

## 8. 投喂顺序与微调建议

1. **第一轮**：把第 1 节（Master Prompt）单独投喂，让 Claude design 先建立设计系统语境，输出一组 design tokens / 组件预览即可
2. **第二轮**：投喂第 2 节（首页），这是最重要的一稿；如果第一稿 3D prism 不到位，单独再发一条："refine the hero 3D prism — make the dispersion more pronounced and the rainbow more saturated, reference Apple's iPhone keynote 3D motion"
3. **第三轮起**：剩下分页可以并行投喂。每次替换一次 `{{BRAND}}` 占位
4. **微调常用 prompt 句式**：
   - "make it more {luminous / restrained / playful}"
   - "increase / decrease the 3D intensity"
   - "reference {linear.app / vercel.com / openrouter.ai} for {section}"
   - "make Chinese typography tighter"
   - "add more whitespace around the hero"

---

## 9. 关键参考站（喂给 Claude design 时可以引用）

| 参考维度 | 站点 |
|---|---|
| 3D 动效与玻璃质感 | linear.app, anthropic.com, some.run |
| 暗色科技感排版 | vercel.com, supabase.com, resend.com |
| 模型聚合页面结构 | openrouter.ai/models |
| 中文极简但不土 | deepseek.com, kimi.moonshot.cn |
| 企业级信任感 | stripe.com, openai.com/api |
| 控制台/dashboard | linear.app/inbox, vercel.com/dashboard |

---

## 10. 待用户后续决策

1. **品牌名定稿**：从第 0 节 4-5 个候选挑 1 个，告诉我，我可以再加一稿"基于此品牌的视觉细化方案"（logo 的几何方案、品牌色微调）
2. **域名查询**：定品牌后立刻查 `.ai` / `.com` / `.cn` 域名是否可注册（建议 .ai 或 .com 优先）
3. **本地化策略**：是否要做中英双语 toggle？还是中文为主、英文仅做技术文档？
4. **首期 MVP 范围**：第一版上线只做 首页 + 注册登录 + Console 三页，还是六页都做？
