// Homepage data — 与后端 model catalog 实时对齐。
// 维护规则：
//   - 这里的 model 必须在 GET /v1/models 真能调出来
//   - 价格写「上游官方价的我们 catalog 落库值」（µ¢/M / 100M = USD/M）
//   - p50 是 ttft 估算值，仅展示用，会随 chain monitor 数据回灌

window.PRISM_HERO_MODELS = [
  { id: 'claude-opus-4-7',         display: 'Claude Opus 4.7',   provider: 'anthropic', priceIn: 15,    priceOut: 75,   p50: 420, ctx: '1M'   },
  { id: 'claude-sonnet-4-6',       display: 'Claude Sonnet 4.6', provider: 'anthropic', priceIn: 3,     priceOut: 15,   p50: 320, ctx: '1M'   },
  { id: 'claude-haiku-4-5',        display: 'Claude Haiku 4.5',  provider: 'anthropic', priceIn: 0.8,   priceOut: 4,    p50: 240, ctx: '200K' },
  { id: 'gpt-5',                   display: 'GPT-5',             provider: 'openai',    priceIn: 1.25,  priceOut: 10,   p50: 410, ctx: '400K' },
  { id: 'gpt-4o',                  display: 'GPT-4o',            provider: 'openai',    priceIn: 2.5,   priceOut: 10,   p50: 380, ctx: '128K' },
  { id: 'deepseek-chat',           display: 'DeepSeek V4',       provider: 'deepseek',  priceIn: 0.27,  priceOut: 1.1,  p50: 360, ctx: '64K'  },
  { id: 'doubao-seed-1-6-250615',  display: 'Doubao Seed 1.6',   provider: 'doubao',    priceIn: 0.111, priceOut: 1.111, p50: 340, ctx: '256K' },
  { id: 'minimax-text-01',         display: 'MiniMax Text-01',   provider: 'minimax',   priceIn: 0.14,  priceOut: 1.11, p50: 380, ctx: '1M'   },
];

// Provider marquee — 只列我们真接了的家
window.PRISM_PROVIDERS_MARQUEE = [
  'Anthropic', 'OpenAI', 'DeepSeek', 'Doubao', 'MiniMax',
];

window.PRISM_TRUST_METRICS = [
  { num: '20+',     label: '可调模型',     en: 'models' },
  { num: '5',       label: '上游 provider', en: 'providers' },
  { num: '1.5%',    label: '充值费率',      en: 'top-up fee' },
  { num: '0%',      label: '加价',         en: 'markup', highlight: true },
];

window.PRISM_FEATURES = [
  {
    icon: 'price',
    title: '明牌定价',
    en: 'Transparent pricing',
    body: '上游成本就是你的成本。每个模型的输入/输出/缓存单价公开写在控制台，没有暗扣。',
  },
  {
    icon: 'channel',
    title: '渠道明牌',
    en: 'Channels in plain sight',
    body: '每条请求走的是哪个上游、哪个区域，控制台请求详情可查。不藏路由。',
  },
  {
    icon: 'shield',
    title: '只做 API · 不切账号',
    en: 'API-only',
    body: '不偷 Pro/Max 订阅切片对外卖。每条请求走干净的开发者 API。',
  },
  {
    icon: 'plug',
    title: '客户端零改造',
    en: 'Zero-change client switch',
    body: 'Claude Code · Cursor · Codex · ChatBox —— 改一行 base URL 就能跑。',
  },
  {
    icon: 'failover',
    title: '多渠道自动切',
    en: 'Auto failover',
    body: '上游故障 30 秒内自动切到备份渠道；按价格²反比加权选最优路径。',
  },
  {
    icon: 'observe',
    title: '可观测面板',
    en: 'Observable dashboard',
    body: '实时用量、按 Key 拆分、按渠道拆分、明细可下载 —— 一切在你眼前。',
  },
];

// 客户端示例 — 都用真实 base URL
window.PRISM_CLIENTS = [
  { name: 'Claude Code', config: 'ANTHROPIC_BASE_URL=https://www.ai100trading.cn/suanli-api' },
  { name: 'Cursor',      config: 'Settings → Custom OpenAI base URL' },
  { name: 'Codex',       config: 'OPENAI_API_BASE=https://www.ai100trading.cn/suanli-api/v1' },
  { name: 'Continue',    config: 'apiBase: "https://www.ai100trading.cn/suanli-api/v1"' },
  { name: 'Cline',       config: 'OpenAI Compatible · base URL' },
  { name: 'ChatBox',     config: 'API Host = https://www.ai100trading.cn/suanli-api' },
  { name: 'LobeChat',    config: 'base_url + sk-prism-... key' },
  { name: 'Aider',       config: '--openai-api-base https://www.ai100trading.cn/suanli-api/v1' },
];

// 按场景挑模型 — 每个 model 都是我们真能调的
window.PRISM_CATEGORIES = [
  {
    id: 'coding',
    title: '写代码',
    en: 'Coding',
    why: '工具调用稳定、长上下文充裕',
    picks: [
      { model: 'Claude Sonnet 4.6',  provider: 'anthropic', tip: '工具调用最稳，1M 上下文', price: '$3 / $15' },
      { model: 'Claude Haiku 4.5',   provider: 'anthropic', tip: '便宜+快，日常够用',       price: '$0.80 / $4' },
      { model: 'DeepSeek V4',        provider: 'deepseek',  tip: '中文+代码混合最佳',       price: '$0.27 / $1.10' },
    ],
  },
  {
    id: 'reasoning',
    title: '复杂推理',
    en: 'Reasoning',
    why: '数学、研究、长链条思考',
    picks: [
      { model: 'Claude Opus 4.7',    provider: 'anthropic', tip: '综合最强，1M 上下文',      price: '$15 / $75' },
      { model: 'OpenAI o3-mini',     provider: 'openai',    tip: '推理性价比高',           price: '$1.10 / $4.40' },
      { model: 'DeepSeek Reasoner',  provider: 'deepseek',  tip: '推理 + 中文，1/30 价格',  price: '$0.55 / $2.19' },
    ],
  },
  {
    id: 'cheap',
    title: '极速 + 便宜',
    en: 'Cheap & fast',
    why: '高频调用 / 后台批处理',
    picks: [
      { model: 'Doubao 1.5 Lite',    provider: 'doubao',    tip: '$0.04/M 输入，国内最便宜', price: '$0.04 / $0.08' },
      { model: 'Doubao Seed 1.6 Flash', provider: 'doubao', tip: '更新一代，速度更快',      price: '$0.02 / $0.21' },
      { model: 'GPT-4o mini',        provider: 'openai',    tip: 'OpenAI 生态兜底',         price: '$0.15 / $0.60' },
    ],
  },
  {
    id: 'long',
    title: '长上下文',
    en: 'Long context',
    why: '长文档、整 codebase、长会议纪要',
    picks: [
      { model: 'Claude Opus 4.7',    provider: 'anthropic', tip: '1M 上下文，工具调用稳',    price: '$15 / $75' },
      { model: 'Claude Sonnet 4.6',  provider: 'anthropic', tip: '1M 上下文性价比之选',      price: '$3 / $15' },
      { model: 'MiniMax Text-01',    provider: 'minimax',   tip: '1M 上下文，国内便宜',      price: '$0.14 / $1.11' },
    ],
  },
];

// 渠道明牌示例 — 用我们真实的 channel 配置（生产 channel 1-5）
window.PRISM_CHANNEL_EXAMPLES = {
  'claude-opus-4-7': {
    name: 'Claude Opus 4.7',
    provider: 'Anthropic',
    channels: [
      { name: 'Anthropic 官方 API', region: 'us-east-1', p50: 420, weight: 100, health: 'ok', policy: '不训练 · 30 天日志' },
    ],
  },
  'gpt-5': {
    name: 'GPT-5',
    provider: 'OpenAI',
    channels: [
      { name: 'OpenAI 官方 API', region: 'us', p50: 410, weight: 100, health: 'ok', policy: '不训练 · 30 天日志' },
    ],
  },
  'deepseek-chat': {
    name: 'DeepSeek V4',
    provider: 'DeepSeek',
    channels: [
      { name: 'DeepSeek 官方 API', region: 'cn', p50: 360, weight: 100, health: 'ok', policy: '不训练 · 30 天日志' },
    ],
  },
  'doubao-seed-1-6-250615': {
    name: 'Doubao Seed 1.6',
    provider: '火山方舟',
    channels: [
      { name: '火山方舟 / Volcengine', region: 'cn-beijing', p50: 340, weight: 100, health: 'ok', policy: '不训练 · 30 天日志' },
    ],
  },
};

window.PRISM_NOT_DOING = [
  {
    title: '不账号切片',
    en: 'No subscription slicing',
    body: '不偷 Pro/Max 订阅 OAuth token 对外卖。每条请求走干净的开发者 API。',
  },
  {
    title: '不暗中降级',
    en: 'No silent downgrade',
    body: '高峰期不偷换模型版本（行业陋习把 Sonnet 当 Opus 卖）。响应里都明示真实模型 ID。',
  },
  {
    title: '不私扣余额',
    en: 'No hidden fees',
    body: 'Token 计算公式公开，扣费按上游 usage 字段精确计算到微分。月底可下载明细对账。',
  },
  {
    title: '不藏渠道',
    en: 'No black-box routing',
    body: '每条请求走的是哪条上游、哪个区域、哪个 region，控制台请求详情都查得到。',
  },
];

// FAQ — 简洁中文，去掉中英混杂、去掉不存在的功能
window.PRISM_FAQ = [
  {
    q: '和直接调官方 API 有什么区别？',
    a: '同一个客户端、同一套代码，多了：多渠道自动故障切换、支付宝/微信/USDC 充值、多家模型一个 Key、按 Key 拆分的用量面板。价格不加价，与上游一致。',
  },
  {
    q: '0% 加价怎么活？',
    a: '充值收 1.5% 手续费（覆盖支付通道 / 商户费 / 链上 gas）。Team 套餐对公月结另计。',
  },
  {
    q: '能开发票吗？',
    a: 'Team 套餐起支持对公转账 + 增值税专票。个人走支付宝/微信/USDC，暂不开票。',
  },
  {
    q: 'Claude Code / Cursor / Codex 怎么接入？',
    a: 'Claude Code 改 ANTHROPIC_BASE_URL，Cursor / Codex 改 OPENAI_BASE_URL，把 key 换成 sk-prism-... 即可，其他不动。详见 quickstart 文档。',
  },
  {
    q: '我的数据会被训练吗？日志保留多久？',
    a: '所有上游都按"不训练"设置；网关日志保留 30 天用于对账。Team 套餐可配 0 日志渠道。',
  },
  {
    q: '出现故障怎么办？',
    a: '单条上游故障，30 秒内熔断切到备份渠道。状态页公示停机记录。',
  },
];
