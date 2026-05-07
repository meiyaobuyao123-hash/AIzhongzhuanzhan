# /models 页迭代 Prompt（v2 · 重构内容架构）

> 这是给 Claude design 的**迭代 prompt**，用于把 v1 的 OpenRouter 克隆式
> 模型卡片网格，重构为更贴合 Prism 价值主张的内容架构。
> 视觉系统（tokens / 字体 / 3D 酒店风 / 卡片样式 / 抽屉）**完全保留**。

## 为什么要改 v1

v1 的页面（`Prism Models.html`）核心问题：

1. **Job-to-be-done 错位**：用户来 `/models` 不是为了"看你有多少"，是为了"我该用哪个"。当前 28 张卡片网格让用户自己做调研
2. **差异化埋得太深**：渠道透明（Channels）是 Prism 区别于低价站的核心卖点，目前需要点开抽屉、切到 Channels tab 才能看到
3. **OpenRouter 克隆感**：视觉不同，但信息架构完全一样（卡片网格 + 过滤器 + 抽屉）
4. **没体现 "一个 Key" 的核心承诺**：在罗列"我有多少"，没有让用户**感受到**"切换有多简单"

## 新架构总览

| 段 | 解决什么 | 与 v1 的差异 |
|---|---|---|
| Hero + 实时切模型 demo | 让用户当场看到"换 model 字段"多简单 | v1 是静态标题；v2 是交互演示 |
| 按场景挑模型（6 张精选卡）| "我该用哪个" | v1 让用户自己过滤；v2 直接给推荐 |
| 渠道透明 banner（提级）| 主打差异化 | v1 埋在二级抽屉；v2 提到主页 |
| 完整模型矩阵（紧凑 table）| 长尾全集查询 | v1 是卡片网格主菜；v2 退化为参考表 |
| 客户端快捷接入 | 引流到 docs | v1 没有；v2 新增 |
| Final CTA | 注册转化 | 复用 |

## Prompt 全文（直接复制粘贴到 Claude design）

```
Refactor the existing /models page (Prism Models.html). Keep ALL the existing
visual system intact: color tokens, typography, the iridescent gradient, the
nebula/starfield background, the 3D-hotel-lobby aesthetic, card styling, the
Drawer component, the FilterBar component. Don't redesign — restructure.

The current page is too close to an OpenRouter clone (filterable card grid of
~28 models). It doesn't reflect Prism's actual value proposition. Rewrite the
content architecture to lead with picking, not browsing. Reuse existing
components where possible; build new sections on top of the same design system.

# New page architecture (in order)

## Section 1: Hero — "switching is one line"
Replace the current static title with an interactive demonstration.
- Headline (display 56-64px): "选好模型，剩下的事交给一行代码。"
  with "一行代码" rendered in iridescent gradient
- Subhead: "200+ 前沿模型 · 一个 OpenAI 兼容 endpoint · 随时切换不改代码"
- English mono subtitle: "Pick a model. Change one string. That's it."
- Right side (40% width): a live "model picker" widget:
  - A code block showing a Python snippet with the model= line highlighted
  - Above the code: 6 small model pill buttons (GPT-5 / Claude Opus 4.5 /
    Gemini 3 Pro / DeepSeek V4 / Kimi K2 / Grok 4)
  - Clicking a pill swaps the model= string with a smooth typing animation
    and instantly updates a tiny stat row below (price/M, p50, ctx)
  - Caption under the widget: "↑ click any model to swap. Same code, same
    response shape. No SDK change."
- Below hero: thin marquee of provider glyphs at 50% opacity (reuse existing)

This section IS the page's core message. Spend pixel budget here.

## Section 2: 按场景挑模型 (Curated picks by use case)
A 3×2 grid of large category cards. Each card has:
- A use-case title in display font: e.g. "写代码 / Coding"
- One sentence: why this category exists
- 2-3 model "chip rows" inside the card, each with:
  - Model name + provider glyph
  - One-liner: when to pick this over the other
  - Mini price tag
- Bottom: "为什么是它们？" expandable note with 1-2 sentences of rationale
- Hover: existing iridescent gradient border + 3D tilt

Six categories with sample picks:

1. **写代码 / Coding** —
   - Claude Sonnet 4.5 — 默认首选，工具调用稳，长上下文够
   - Qwen3 Coder — 中文注释/代码混合最自然，便宜 1/6
   - GPT-5 mini — 性价比兜底，速度快

2. **复杂推理 / Reasoning** —
   - o3-pro — 数学/科研最强，慢但准
   - DeepSeek R2 — 推理 + 中文最佳，价格 1/15
   - Gemini 3 Pro — 长链推理 + 200 万上下文

3. **多模态 / Vision** —
   - Gemini 3 Pro — 视频/图像/音频通吃，2M 上下文
   - Claude Opus 4.5 — 图表理解最准，文档解析强
   - Qwen3 VL — 中文场景视觉首选，便宜

4. **极速 + 便宜 / Cheap & Fast** —
   - GLM-5 Air — 输入 ¥0.7/M，p50 200ms
   - Gemini 3 Flash — 1M 上下文还便宜
   - GPT-5 nano — OpenAI 生态兜底

5. **长上下文 / Long Context** —
   - Gemini 3 Pro — 2M tokens
   - Kimi K2 — 256K，国内站稳定
   - Claude Sonnet 4.5 — 200K + prompt cache 神器

6. **嵌入向量 / Embeddings** —
   - text-embedding-4 — 通用首选
   - Cohere Embed v4 — 多语言/检索质量更高
   - Qwen3 embedding — 中文特化

This section replaces the old card grid as the primary "discovery" mechanism.

## Section 3: 渠道透明 banner (promote from drawer)
A standalone full-width section. Take the "Channels transparency" feature out
of the drawer and surface it here as Prism's signature:

- Title: "我们告诉你每个模型走的是哪条路。"
- Subtitle: "Bedrock · Vertex · 官方 API · 私有渠道 —— 每条都明牌。"
- Below: a horizontal mini-display showing a single model's routing flow:
  "User request → Prism gateway → [3 channel cards arranged in arc]"
  - Each channel card mini-shows: provider, region, p50, health, weight bar
  - Use the existing channel-row visual style, just smaller and arranged in a
    diagonal/3D arc (consistent with hotel-lobby aesthetic)
- A toggle below lets the user switch between 3 example models to see different
  routing setups (Claude Opus 4.5 / GPT-5 / Gemini 3 Pro)
- CTA: "查看任意模型的渠道详情 →" links to scroll into the table below

This is the brand differentiator made visible at the top level.

## Section 4: 完整模型矩阵 (Compact table, NOT cards)
The full 200+ list, but as a dense reference table — not a card grid. Users
who want to drill down come here; users who don't want to never see it.

- Above the table: existing FilterBar (provider chips / capability chips /
  search / sort) — reused as-is, but feels secondary now
- Table headers (sticky): 模型 | 厂商 | 上下文 | 输入 ¥/M | 输出 ¥/M | p50 | 能力 | 渠道数 | [操作]
- Each row is single-line, terse, scan-friendly. Hover row: iridescent micro-glow
  on the row background.
- 操作 column: a small "→" icon button that opens the existing Drawer
  (Playground/Code/Pricing/Channels tabs) — Drawer reuse stays
- Footer of table: "查看全部 200+ 模型 →" (currently shows top 30)

The visual treatment should make this clearly secondary to Section 2/3 —
narrower max-width, more muted typography.

## Section 5: 客户端快速接入 (Client compatibility shortcut)
Compact horizontal strip — not a full grid this time. Just 8 client logo tiles
in a single row with mouse-track parallax (Claude Code / Cursor / Codex /
Continue / Cline / ChatBox / LobeChat / Aider). Click any → goes to docs page.
Headline: "你的客户端，零改造接入。"

## Section 6: Final CTA
Reuse existing iridescent banner pattern.
"充 1 万到账 9995 · 立刻接入全部 200+ 模型 · 0% 加价 · 万 5 手续费"
[立即注册] CTA + small print "微信/支付宝/USDT/对公全通道 · 无需信用卡"

# Important notes for the AI

- DO NOT redesign tokens, typography, or the dark/iridescent aesthetic
- DO reuse: BrandMark, FilterBar, ModelCard (in Section 2 only, modified),
  Drawer, EmptyState — these are already built and good
- The interactive hero widget (live model swap) is the highest-priority new
  element. Get it right first.
- Section 2's cards are larger and richer than the old ModelCard — they're
  category cards, not model cards. Build a new component for them
  (CategoryCard) with 3 nested model mini-rows
- Section 3's channel arc visualization is new — build a new component
  (ChannelArc) that uses the existing channel-row styling but in a 3D arc layout
- Section 4 is a new compact ModelTable component (no card grid here)
- Mobile: Section 1 widget collapses to vertical, Section 2 grid → 1-col,
  Section 3 arc → vertical list, Section 4 table → horizontal scroll

# What to remove
- The current full-page card grid as the primary content
- The empty state in its current form (will only show inside Section 4 table now)

# Voice
Same as before: 简洁、有力、不油腻。No "海量"、"震撼" type marketing fluff.
Numbers concrete. Bilingual (Chinese primary, English mono subtitle).
```

## 投喂方式

1. 在 Claude design 同一项目里（已经有 tokens.css / styles.css / Drawer / FilterBar / ModelCard 那个项目），新开一轮对话
2. 把上面 ``` 包起来的 prompt 全文复制进去
3. 第一稿出来后看 Section 1（Hero 实时切模型 demo）做得怎么样，那是这一稿成败的关键
4. 如果 Section 3 的渠道弧形图不到位，单独追加："refine the channel arc — make the 3 channel cards arranged in a 3D arc with depth, like cards floating in a hotel lobby; reference Apple iCloud's keyframe animation aesthetic"
