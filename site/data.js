// Mock data for Prism homepage
// Numbers are illustrative — replace with real values from upstream pricing pages.

window.PRISM_HERO_MODELS = [
  { id: 'claude-opus-4.5',  display: 'Claude Opus 4.5',  provider: 'anthropic', priceIn: 15,   priceOut: 75,   p50: 420, ctx: '200K' },
  { id: 'claude-sonnet-4.5', display: 'Claude Sonnet 4.5', provider: 'anthropic', priceIn: 3,    priceOut: 15,   p50: 320, ctx: '200K' },
  { id: 'gpt-5',             display: 'GPT-5',             provider: 'openai',    priceIn: 8,    priceOut: 32,   p50: 410, ctx: '400K' },
  { id: 'gemini-3-pro',      display: 'Gemini 3 Pro',      provider: 'google',    priceIn: 2.5,  priceOut: 10,   p50: 380, ctx: '2M'   },
  { id: 'deepseek-v4',       display: 'DeepSeek V4',       provider: 'deepseek',  priceIn: 0.27, priceOut: 1.1,  p50: 360, ctx: '128K' },
  { id: 'kimi-k2',           display: 'Kimi K2',           provider: 'moonshot',  priceIn: 0.6,  priceOut: 2.4,  p50: 340, ctx: '256K' },
];

window.PRISM_PROVIDERS_MARQUEE = [
  'OpenAI', 'Anthropic', 'Google', 'xAI', 'DeepSeek', 'Moonshot',
  'Zhipu', 'Alibaba', 'Meta', 'Mistral', 'Cohere', 'Qwen',
];

window.PRISM_TRUST_METRICS = [
  { num: '200+',    label: '前沿模型', en: 'frontier models' },
  { num: '60+',     label: '上游 provider', en: 'upstream providers' },
  { num: '< 380ms', label: 'p50 延迟', en: 'median latency' },
  { num: '99.95%',  label: '可用性', en: 'uptime' },
  { num: '0%',      label: '加价',  en: 'markup', highlight: true },
];

window.PRISM_FEATURES = [
  {
    icon: 'price',
    title: '明牌定价',
    en: 'Transparent pricing',
    body: '上游成本就是你的成本。每个模型的真实倍率和上游折扣都公开，没有暗扣，没有隐藏费率。',
  },
  {
    icon: 'channel',
    title: '渠道明牌',
    en: 'Channels in plain sight',
    body: '每个模型走的是 Anthropic 直连、Bedrock、Vertex 还是私有渠道，请求级可查。',
  },
  {
    icon: 'shield',
    title: '只做 API · 不切账号',
    en: 'API-only · no slicing',
    body: '不偷 Pro/Max OAuth token，不污染你的 Memory 和对话历史。每条请求都是干净的 API 调用。',
  },
  {
    icon: 'plug',
    title: '客户端零改造',
    en: 'Zero-change client switch',
    body: 'Claude Code · Cursor · Codex · ChatBox · LobeChat —— 改一行 base URL 就能跑。',
  },
  {
    icon: 'failover',
    title: '多 provider 自动切',
    en: 'Auto failover',
    body: '上游故障 30 秒内自动切到备份渠道，按价格-平方反比加权选最优路径。',
  },
  {
    icon: 'observe',
    title: '可观测面板',
    en: 'Observable dashboard',
    body: '实时用量、p50/p95、按 Key/Project 拆分、按渠道命中率 —— 一切在你眼前。',
  },
];

window.PRISM_CLIENTS = [
  { name: 'Claude Code', config: 'ANTHROPIC_BASE_URL=https://api.prism.ai/anthropic' },
  { name: 'Cursor',      config: 'Settings → Models → Custom OpenAI base URL' },
  { name: 'Codex',       config: 'OPENAI_API_BASE=https://api.prism.ai/v1' },
  { name: 'Continue',    config: 'apiBase: "https://api.prism.ai/v1"' },
  { name: 'Cline',       config: 'OpenAI Compatible · base URL' },
  { name: 'ChatBox',     config: 'API Host = https://api.prism.ai' },
  { name: 'LobeChat',    config: 'base_url + sk-prism-... key' },
  { name: 'FastGPT',     config: 'OpenAI 接入 · base_url' },
  { name: 'Aider',       config: '--openai-api-base https://api.prism.ai/v1' },
  { name: 'Roo Code',    config: 'OpenAI Compatible · custom base' },
];

window.PRISM_CATEGORIES = [
  {
    id: 'coding',
    title: '写代码',
    en: 'Coding',
    why: '工具调用稳定 · 长上下文足 · 中英文代码混排自然',
    picks: [
      { model: 'Claude Sonnet 4.5', provider: 'anthropic', tip: '默认首选，工具调用最稳', price: '$3 / $15' },
      { model: 'Qwen3 Coder',       provider: 'alibaba',   tip: '中文注释+代码混合最佳，便宜 1/6', price: '$0.5 / $2' },
      { model: 'GPT-5 mini',        provider: 'openai',    tip: '性价比兜底，速度快', price: '$1.2 / $4.8' },
    ],
  },
  {
    id: 'reasoning',
    title: '复杂推理',
    en: 'Reasoning',
    why: '数学、研究、长链条思考 —— 慢一点但要准',
    picks: [
      { model: 'o3-pro',          provider: 'openai',    tip: '数学/科研最强，慢但准', price: '$20 / $80' },
      { model: 'DeepSeek R2',     provider: 'deepseek',  tip: '推理 + 中文最佳，1/15 价格', price: '$0.55 / $2.2' },
      { model: 'Gemini 3 Pro',    provider: 'google',    tip: '长链推理 + 200 万上下文', price: '$2.5 / $10' },
    ],
  },
  {
    id: 'vision',
    title: '多模态',
    en: 'Vision',
    why: '图像/视频/音频理解，不只是看见，是看懂',
    picks: [
      { model: 'Gemini 3 Pro',     provider: 'google',    tip: '视频/图像/音频通吃', price: '$2.5 / $10' },
      { model: 'Claude Opus 4.5',  provider: 'anthropic', tip: '图表理解最准，文档解析强', price: '$15 / $75' },
      { model: 'Qwen3 VL',         provider: 'alibaba',   tip: '中文场景视觉首选，便宜', price: '$0.6 / $2.4' },
    ],
  },
  {
    id: 'cheap',
    title: '极速 + 便宜',
    en: 'Cheap & fast',
    why: '高频调用 / 后台批处理 / 便宜出量',
    picks: [
      { model: 'GLM-5 Air',         provider: 'zhipu',    tip: '$0.1/M 输入，p50 200ms', price: '$0.1 / $0.4' },
      { model: 'Gemini 3 Flash',    provider: 'google',   tip: '1M 上下文还便宜', price: '$0.3 / $1.2' },
      { model: 'GPT-5 nano',        provider: 'openai',   tip: 'OpenAI 生态兜底', price: '$0.15 / $0.6' },
    ],
  },
  {
    id: 'long',
    title: '长上下文',
    en: 'Long context',
    why: '整本书、整个 codebase、长会议纪要塞进去',
    picks: [
      { model: 'Gemini 3 Pro',      provider: 'google',    tip: '2M tokens，业内最长', price: '$2.5 / $10' },
      { model: 'Kimi K2',           provider: 'moonshot',  tip: '256K，国内站稳定', price: '$0.6 / $2.4' },
      { model: 'Claude Sonnet 4.5', provider: 'anthropic', tip: '200K + prompt cache 神器', price: '$3 / $15' },
    ],
  },
  {
    id: 'embed',
    title: '嵌入向量',
    en: 'Embeddings',
    why: '检索 / RAG / 语义相似度的底座',
    picks: [
      { model: 'text-embedding-4',  provider: 'openai',  tip: '通用首选',                   price: '$0.02 / -' },
      { model: 'Cohere Embed v4',   provider: 'cohere',  tip: '多语言检索质量更高',          price: '$0.10 / -' },
      { model: 'Qwen3 embedding',   provider: 'alibaba', tip: '中文特化',                   price: '$0.05 / -' },
    ],
  },
];

window.PRISM_CHANNEL_EXAMPLES = {
  'claude-opus-4.5': {
    name: 'Claude Opus 4.5',
    provider: 'Anthropic',
    channels: [
      { name: 'Anthropic 官方 API',  region: 'us-east-1',   p50: 412, weight: 60, health: 'ok',       policy: '不训练 · 30 天日志' },
      { name: 'AWS Bedrock',          region: 'us-west-2',   p50: 438, weight: 25, health: 'ok',       policy: '不训练 · 0 日志' },
      { name: 'GCP Vertex AI',        region: 'europe-west4',p50: 510, weight: 15, health: 'degraded', policy: '不训练 · 0 日志' },
    ],
  },
  'gpt-5': {
    name: 'GPT-5',
    provider: 'OpenAI',
    channels: [
      { name: 'OpenAI 官方 API',      region: 'us',          p50: 408, weight: 70, health: 'ok',       policy: '不训练 · 30 天日志' },
      { name: 'Azure OpenAI',         region: 'eastus2',     p50: 430, weight: 30, health: 'ok',       policy: '不训练 · 0 日志' },
    ],
  },
  'gemini-3-pro': {
    name: 'Gemini 3 Pro',
    provider: 'Google',
    channels: [
      { name: 'Google AI Studio',     region: 'us-central1',     p50: 372, weight: 50, health: 'ok', policy: '不训练 · 0 日志' },
      { name: 'GCP Vertex AI',        region: 'asia-southeast1', p50: 388, weight: 50, health: 'ok', policy: '不训练 · 0 日志' },
    ],
  },
};

window.PRISM_NOT_DOING = [
  {
    title: '不账号切片',
    en: 'No subscription slicing',
    body: '不偷 Pro/Max OAuth token 切片对外卖。每条请求走干净的 API，不污染你的 Memory 也不会把你的对话和别人混在同一账号里。',
  },
  {
    title: '不暗中降级',
    en: 'No silent downgrade',
    body: '高峰期不偷换模型版本（Sonnet 当 Opus 卖、4o 当 5 卖是行业陋习）。每条响应里都明示真实模型 ID。',
  },
  {
    title: '不私扣余额',
    en: 'No hidden fees',
    body: 'Token 计算公式公开，扣费按上游响应的 usage 字段精确计算。月底对账可下载 CSV，与你期望对得上。',
  },
  {
    title: '不藏渠道',
    en: 'No black-box routing',
    body: '每条请求走的是哪个上游、哪个 region、上游的 latency 和 health 状态，控制台请求详情里都查得到。',
  },
];

window.PRISM_FAQ = [
  {
    q: 'Prism 和直接调官方 API 有什么区别？',
    a: '同样的 API，多了：（1）多上游故障切换；（2）支付宝/微信充值；（3）多模型一个 Key；（4）按 Key/Project 用量面板。价格保持和上游一致，我们不在 inference 上加钱。',
  },
  {
    q: '"0% 加价" 你们怎么活？',
    a: '充值费 5%（行业常规）+ 企业 SLA / 私有渠道 / 可观测增值服务。OpenRouter 已经验证过这条路能走通到年化 1 亿美元。',
  },
  {
    q: '能开发票吗？支持对公收款吗？',
    a: 'Team 套餐起支持对公转账 + 增值税专票。个人/Developer 走支付宝/微信不开票（你也大概率不需要）。',
  },
  {
    q: '我用 Claude Code / Cursor / Codex 能直接接入吗？',
    a: '可以。Claude Code 改 ANTHROPIC_BASE_URL，Cursor/Codex 改 OPENAI_API_BASE，剩下不变。',
  },
  {
    q: '数据会被训练吗？日志保留多久？',
    a: '默认所有上游均选"不训练"政策渠道；日志保留 30 天用于对账，企业客户可选 0 日志渠道（Bedrock / Vertex）。',
  },
  {
    q: '出现故障怎么办？',
    a: '单 provider 故障 30 秒内自动切到备份渠道，全平台年累计停机承诺 < 4.4 小时（99.95%）。Team 套餐含 SLA 赔付条款。',
  },
];
