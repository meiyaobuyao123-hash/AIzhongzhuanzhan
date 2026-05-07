/* All sections below the hero, kept as small focused components.
   Order on the page (driven by app.jsx):
     2  Trust strip
     3  Features 3×2
     4  Live demo (code + terminal)
     5  Client compatibility row
     6  Pick by category 3×2
     7  Channel transparency banner
     8  We don't do
     9  Pricing preview
    10  FAQ
    11  Final CTA + Footer
*/

const { useState: useStateS, useEffect: useEffectS, useMemo: useMemoS, useRef: useRefS } = React;

/* ─── 2 · Trust strip ───────────────────────────────────────────── */

function TrustStrip() {
  return (
    <section className="trust-strip">
      <div className="trust-inner">
        {window.PRISM_TRUST_METRICS.map((m, i) => (
          <div key={i} className={`trust-item ${m.highlight ? 'highlight' : ''}`}>
            <div className="trust-num display">{m.num}</div>
            <div className="trust-label">
              <span>{m.label}</span>
              <span className="mono trust-en">{m.en}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ─── 3 · Features 3×2 ──────────────────────────────────────────── */

function FeaturesGrid() {
  return (
    <section className="features" id="features">
      <SectionHeader
        kicker="为什么选 Prism"
        title="把同行不敢明说的事 · 写在合同里"
        sub="Why Prism · what others quietly avoid, we write into the contract."
      />
      <div className="features-grid">
        {window.PRISM_FEATURES.map((f, i) => (
          <article key={i} className="feature-card">
            <FeatureIcon name={f.icon} />
            <h3 className="feature-title display">
              {f.title}
              <span className="mono feature-en">{f.en}</span>
            </h3>
            <p className="feature-body">{f.body}</p>
            <div className="feature-glow" aria-hidden="true" />
          </article>
        ))}
      </div>
    </section>
  );
}

function FeatureIcon({ name }) {
  // Tiny abstract glyphs that match each feature's idea
  const common = { width: 28, height: 28, viewBox: '0 0 28 28', fill: 'none' };
  const stroke = 'url(#fi-grad)';
  const grad = (
    <defs>
      <linearGradient id="fi-grad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#8B5CF6"/>
        <stop offset="50%" stopColor="#06B6D4"/>
        <stop offset="100%" stopColor="#EC4899"/>
      </linearGradient>
    </defs>
  );
  return (
    <span className="feature-icon">
      {name === 'price' && (
        <svg {...common}>{grad}
          <circle cx="14" cy="14" r="10" stroke={stroke} strokeWidth="1.5"/>
          <path d="M11 17.5h6M11 13.5h6M11 9.5h6" stroke={stroke} strokeWidth="1.4" strokeLinecap="round"/>
        </svg>
      )}
      {name === 'channel' && (
        <svg {...common}>{grad}
          <path d="M5 14h6m6 0h6" stroke={stroke} strokeWidth="1.4" strokeLinecap="round"/>
          <circle cx="14" cy="14" r="3.2" stroke={stroke} strokeWidth="1.4"/>
          <circle cx="5"  cy="14" r="1.5" fill={stroke}/>
          <circle cx="23" cy="14" r="1.5" fill={stroke}/>
        </svg>
      )}
      {name === 'shield' && (
        <svg {...common}>{grad}
          <path d="M14 4 L23 8 V14 C23 19 19 23 14 24 C9 23 5 19 5 14 V8 Z" stroke={stroke} strokeWidth="1.5" strokeLinejoin="round"/>
          <path d="M10 14 L13 17 L18 11" stroke={stroke} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      )}
      {name === 'plug' && (
        <svg {...common}>{grad}
          <rect x="6"  y="9" width="6" height="10" rx="2" stroke={stroke} strokeWidth="1.4"/>
          <rect x="16" y="9" width="6" height="10" rx="2" stroke={stroke} strokeWidth="1.4"/>
          <path d="M12 14h4" stroke={stroke} strokeWidth="1.4" strokeLinecap="round"/>
          <path d="M9  6v3M19 6v3M9 19v3M19 19v3" stroke={stroke} strokeWidth="1.4" strokeLinecap="round"/>
        </svg>
      )}
      {name === 'failover' && (
        <svg {...common}>{grad}
          <circle cx="8"  cy="14" r="2.5" stroke={stroke} strokeWidth="1.4"/>
          <circle cx="20" cy="9"  r="2.5" stroke={stroke} strokeWidth="1.4"/>
          <circle cx="20" cy="19" r="2.5" stroke={stroke} strokeWidth="1.4"/>
          <path d="M10.5 13l7-3M10.5 15l7 3" stroke={stroke} strokeWidth="1.3"/>
          <path d="M18 7l3 2-3 2" stroke={stroke} strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      )}
      {name === 'observe' && (
        <svg {...common}>{grad}
          <rect x="4" y="6" width="20" height="14" rx="2" stroke={stroke} strokeWidth="1.4"/>
          <path d="M7 16l4-4 3 3 5-7" stroke={stroke} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      )}
    </span>
  );
}

/* ─── 4 · Live demo: code + streaming terminal ──────────────────── */

function LiveDemo() {
  const [lang, setLang] = useStateS('python');
  const [streamText, setStreamText] = useStateS('');
  const fullResponse = '一行代码切到 Claude · 同样的代码切到 GPT-5。\n你的客户端、你的提示词、你的 prompt cache 全都一行不用改。';
  const tickRef = useRefS(null);

  useEffectS(() => {
    let i = 0;
    setStreamText('');
    if (tickRef.current) clearInterval(tickRef.current);
    tickRef.current = setInterval(() => {
      i += 1;
      setStreamText(fullResponse.slice(0, i));
      if (i >= fullResponse.length) clearInterval(tickRef.current);
    }, 28);
    return () => clearInterval(tickRef.current);
  }, [lang]);

  const codeSamples = {
    python:
`from openai import OpenAI
client = OpenAI(
    base_url="https://api.prism.ai/v1",
    api_key="sk-prism-…",
)
stream = client.chat.completions.create(
    model="claude-sonnet-4.5",
    messages=[{"role":"user","content":"演示一下"}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")`,
    node:
`import OpenAI from "openai";
const client = new OpenAI({
  baseURL: "https://api.prism.ai/v1",
  apiKey: process.env.PRISM_KEY,
});
const stream = await client.chat.completions.create({
  model: "claude-sonnet-4.5",
  messages: [{ role: "user", content: "演示一下" }],
  stream: true,
});
for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? "");
}`,
    curl:
`curl https://api.prism.ai/v1/chat/completions \\
  -H "Authorization: Bearer sk-prism-…" \\
  -H "Content-Type: application/json" \\
  --no-buffer \\
  -d '{
    "model": "claude-sonnet-4.5",
    "messages": [{"role":"user","content":"演示一下"}],
    "stream": true
  }'`,
  };

  return (
    <section className="live-demo" id="demo">
      <SectionHeader
        kicker="接入演示"
        title="改一行 base URL · 跑遍 200+ 模型"
        sub="Same SDK. New base URL. Done."
      />
      <div className="ld-grid">
        <div className="ld-code">
          <div className="ld-tabs">
            {[['python', 'Python'], ['node', 'Node.js'], ['curl', 'curl']].map(([k, v]) => (
              <button
                key={k}
                className={`ld-tab mono ${lang === k ? 'active' : ''}`}
                onClick={() => setLang(k)}
              >{v}</button>
            ))}
            <button className="ld-copy mono" onClick={() => navigator.clipboard?.writeText(codeSamples[lang])}>
              复制
            </button>
          </div>
          <pre className="ld-block mono">{codeSamples[lang]}</pre>
        </div>

        <div className="ld-terminal">
          <div className="ld-term-head">
            <span className="cw-dot d1"/>
            <span className="cw-dot d2"/>
            <span className="cw-dot d3"/>
            <span className="cw-title mono">prism · streaming response</span>
            <span className="ld-streaming"><span className="ld-streaming-dot"/>streaming</span>
          </div>
          <div className="ld-term-body mono">
            <span className="ld-prompt">$</span> python demo.py
            <div className="ld-stream">{streamText}<span className="ld-caret"/></div>
          </div>
          <div className="ld-term-foot mono">
            <span>p50 412ms</span>
            <span className="dot">·</span>
            <span>cost $0.0034</span>
            <span className="dot">·</span>
            <span>routed to <em>Anthropic 官方 API · us-east-1</em></span>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─── 5 · Client compatibility row ──────────────────────────────── */

function ClientStrip() {
  return (
    <section className="clients" id="clients">
      <SectionHeader
        kicker="客户端适配"
        title="你的客户端 · 零改造接入"
        sub="Your existing tools work as-is."
      />
      <div className="client-row">
        {window.PRISM_CLIENTS.map((c, i) => (
          <ClientTile key={i} client={c} />
        ))}
      </div>
    </section>
  );
}

function ClientTile({ client }) {
  const [flipped, setFlipped] = useStateS(false);
  return (
    <div
      className={`client-tile ${flipped ? 'flipped' : ''}`}
      onMouseEnter={() => setFlipped(true)}
      onMouseLeave={() => setFlipped(false)}
      onClick={() => setFlipped(f => !f)}
    >
      <div className="client-front">
        <ClientGlyph name={client.name} />
        <span className="client-name">{client.name}</span>
      </div>
      <div className="client-back mono">
        {client.config}
      </div>
    </div>
  );
}

function ClientGlyph({ name }) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  const hue = h % 360;
  return (
    <span
      className="client-glyph"
      style={{
        background: `linear-gradient(135deg, hsla(${hue}, 70%, 55%, 0.4), hsla(${(hue+60)%360}, 70%, 55%, 0.4))`,
        borderColor: `hsla(${hue}, 70%, 55%, 0.5)`,
      }}
    >
      {name[0]}
    </span>
  );
}

/* ─── 6 · Pick by category ──────────────────────────────────────── */

function CategoryGrid() {
  return (
    <section className="categories" id="models">
      <SectionHeader
        kicker="按场景挑模型"
        title="不用看 200 张卡片 · 我们替你挑了"
        sub="Curated picks by use case · skip the model spreadsheet."
      />
      <div className="cat-grid">
        {window.PRISM_CATEGORIES.map(cat => <CategoryCard key={cat.id} cat={cat}/>)}
      </div>
      <div className="cat-foot">
        <a href="#models-full" className="cta-ghost">查看全部 200+ 模型 →</a>
      </div>
    </section>
  );
}

function CategoryCard({ cat }) {
  return (
    <article className="cat-card">
      <header className="cat-head">
        <h3 className="cat-title display">
          {cat.title}
          <span className="mono cat-en">{cat.en}</span>
        </h3>
        <p className="cat-why">{cat.why}</p>
      </header>
      <ul className="cat-picks">
        {cat.picks.map((p, i) => (
          <li key={i} className="cat-pick">
            <span className="cat-pick-glyph"><ClientGlyph name={p.provider}/></span>
            <div className="cat-pick-body">
              <div className="cat-pick-row">
                <span className="cat-pick-name">{p.model}</span>
                <span className="mono cat-pick-price">{p.price}</span>
              </div>
              <div className="cat-pick-tip">{p.tip}</div>
            </div>
          </li>
        ))}
      </ul>
      <div className="cat-glow" aria-hidden="true"/>
    </article>
  );
}

/* ─── 7 · Channel transparency banner ───────────────────────────── */

function ChannelBanner() {
  const keys = Object.keys(window.PRISM_CHANNEL_EXAMPLES);
  const [active, setActive] = useStateS(keys[0]);
  const example = window.PRISM_CHANNEL_EXAMPLES[active];

  return (
    <section className="channels" id="channels">
      <SectionHeader
        kicker="渠道明牌"
        title="我们告诉你每个模型走的是哪条路"
        sub="Every channel · region · health · policy · in plain sight."
      />

      <div className="ch-toggle">
        {keys.map(k => (
          <button
            key={k}
            className={`ch-tog-btn ${k === active ? 'active' : ''}`}
            onClick={() => setActive(k)}
          >
            {window.PRISM_CHANNEL_EXAMPLES[k].name}
          </button>
        ))}
      </div>

      <div className="ch-flow">
        <div className="ch-node user">
          <div className="ch-node-icon">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <circle cx="11" cy="8"  r="3.5" stroke="currentColor" strokeWidth="1.4"/>
              <path d="M3 19c1.5-3.5 5-5 8-5s6.5 1.5 8 5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
            </svg>
          </div>
          <div className="ch-node-label">客户请求</div>
          <div className="mono ch-node-en">user request</div>
        </div>

        <div className="ch-line ch-line-1" aria-hidden="true"/>

        <div className="ch-node prism">
          <div className="ch-node-icon iridescent-text" style={{fontSize: 20, fontFamily: 'var(--font-display)', fontWeight: 700}}>P</div>
          <div className="ch-node-label">Prism 路由器</div>
          <div className="mono ch-node-en">router</div>
        </div>

        <div className="ch-arc">
          {example.channels.map((ch, i) => (
            <div key={i} className={`ch-card arc-${i+1}`}>
              <div className="ch-card-head">
                <span className="ch-card-name">{ch.name}</span>
                <span className={`ch-health h-${ch.health}`}>{ch.health}</span>
              </div>
              <div className="ch-card-meta">
                <div><span className="meta-k">region</span><span className="meta-v mono">{ch.region}</span></div>
                <div><span className="meta-k">p50</span><span className="meta-v mono">{ch.p50}ms</span></div>
                <div><span className="meta-k">weight</span><span className="meta-v mono">{ch.weight}%</span></div>
              </div>
              <div className="ch-card-policy">{ch.policy}</div>
              <div className="ch-weight-bar">
                <div className="ch-weight-fill" style={{width: `${ch.weight}%`, background: 'var(--iridescent)'}}/>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="ch-foot">
        <span>每条请求的真实路由结果，控制台请求详情里都查得到。</span>
        <a className="link-arrow" href="#docs">了解路由策略 →</a>
      </div>
    </section>
  );
}

/* ─── 8 · We don't do ───────────────────────────────────────────── */

function NotDoing() {
  return (
    <section className="not-doing" id="not-doing">
      <SectionHeader
        kicker="边界 · 我们不做"
        title="同行做的脏活 · 我们一件都不做"
        sub="Four things we refuse to do — even if they pad the margin."
      />
      <div className="nd-grid">
        {window.PRISM_NOT_DOING.map((it, i) => (
          <article key={i} className="nd-card">
            <div className="nd-cross" aria-hidden="true">✕</div>
            <h3 className="nd-title display">
              {it.title}
              <span className="mono nd-en">{it.en}</span>
            </h3>
            <p className="nd-body">{it.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

/* ─── 9 · Pricing preview ───────────────────────────────────────── */

function PricingPreview() {
  const [model, setModel] = useStateS(window.PRISM_HERO_MODELS[1]); // Sonnet 4.5
  const [tokens, setTokens] = useStateS(100_000);
  const cost = ((tokens / 1_000_000) * (model.priceIn + model.priceOut * 3)).toFixed(4); // dummy weighted
  const officialCost = (cost * 1).toFixed(4); // same — that's the point

  return (
    <section className="pricing" id="pricing">
      <SectionHeader
        kicker="定价"
        title="充 1 万到账 9995 · 0% 加价"
        sub="Inference cost = price. Top-up fee 0.05% (the lowest in industry, only covers bank transfer cost)."
      />
      <div className="price-grid price-grid-2">
        <PriceCard
          tier="Self-serve"
          featured
          price="按量付费"
          tagline="充值即用 · 万 5 手续费 · 0% 加价"
          features={[
            '全部 200+ 模型',
            'OpenAI / Anthropic / Gemini 协议',
            '高优先级路由 + prompt cache 透传',
            '限速按充值阶梯 60 → 1200 RPM',
            '支付宝 / 微信 / USDT 充值',
            '5% 邀请返佣',
          ]}
          cta="立即注册"
          ctaHref="#signup"
        />
        <PriceCard
          tier="Team"
          price="联系销售"
          tagline="对公合同 · 专票 · SLA · 私有渠道"
          features={[
            'Self-serve 全部能力',
            '对公收款 + 月结合同',
            '增值税专票',
            '私有上游渠道（独占容量）',
            'SLA 99.95% + 7×24 工单',
            '专属客户经理 + 数据不出境承诺',
          ]}
          cta="联系销售"
          ctaHref="#contact"
        />
      </div>

      <div className="price-calc">
        <div className="pc-head">
          <span className="kicker mono">实时计算器 · live calculator</span>
          <h3 className="pc-title display">看看你这次会花多少钱</h3>
        </div>
        <div className="pc-controls">
          <label className="pc-field">
            <span className="pc-label">选择模型</span>
            <select
              className="pc-input"
              value={model.id}
              onChange={e => setModel(window.PRISM_HERO_MODELS.find(m => m.id === e.target.value))}
            >
              {window.PRISM_HERO_MODELS.map(m => <option key={m.id} value={m.id}>{m.display}</option>)}
            </select>
          </label>
          <label className="pc-field">
            <span className="pc-label">每月 tokens（输入+输出）</span>
            <input
              className="pc-input mono"
              type="number"
              min="1000"
              step="10000"
              value={tokens}
              onChange={e => setTokens(Math.max(0, parseInt(e.target.value) || 0))}
            />
          </label>
          <div className="pc-result">
            <div className="pc-result-row">
              <span>Prism 价</span>
              <span className="display pc-num">${cost}</span>
            </div>
            <div className="pc-result-row pc-result-secondary">
              <span>vs 官方价</span>
              <span className="mono">±0.00 · 完全一致</span>
            </div>
          </div>
        </div>
        <div className="pc-note">
          Inference 按 <code>price_in × token_in + price_out × token_out</code> 精确计算，与上游一致。
          充值时另收 <code>0.05%</code> 手续费（充 1 万到账 9995）。每条请求扣费写进 <code>usage_logs</code>，月底可下载对账 CSV。
        </div>
      </div>

      <PaymentMethods />
    </section>
  );
}

function PaymentMethods() {
  const [copied, setCopied] = useStateS('');
  const copy = (text, label) => {
    navigator.clipboard?.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(''), 1800);
  };

  const TRC_ADDR = 'TT24g41HLptouzxGycZxQKmWaTENK4K4HG';
  const SOL_ADDR = '66p5tnV6Fd7x5QmRE6X772PMVmVUVgozRzATJ4Ns9iQn';
  const EVM_ADDR = '0xC862ff9Fd79D180950E546DBB8b108d5c9c38582';

  return (
    <div className="pay-row">
      <div className="pay-head">
        <span className="kicker mono">充值方式 · payment methods</span>
        <h3 className="pay-title display">6 种通道 · 一律万 5 手续费</h3>
        <p className="pay-sub mono">Pay any way you want · same 0.05% fee · top up $5 minimum.</p>
      </div>

      <div className="pay-grid">
        <PayCard icon="alipay" title="支付宝" en="Alipay" desc="国内个人首选 · 实时到账" badge="即将开放" />
        <PayCard icon="wechat" title="微信支付" en="WeChat Pay" desc="国内个人 · 实时到账" badge="即将开放" />
        <PayCard icon="bank" title="对公转账" en="Bank wire" desc="Team 套餐专享 · 增值税专票 · 月结" badge="Team only" />

        <div className="pay-card pay-card-crypto">
          <div className="pay-card-head">
            <span className="pay-icon pay-icon-trc">T</span>
            <div>
              <div className="pay-card-title">
                USDT (TRC20)
                <span className="pay-card-pill">推荐</span>
              </div>
              <div className="pay-card-en mono">国内首选 · 链上费 ≈ $1</div>
            </div>
          </div>
          <div className="pay-addr-row">
            <code className="pay-addr mono" title={TRC_ADDR}>{TRC_ADDR}</code>
            <button className="pay-copy mono" onClick={() => copy(TRC_ADDR, 'trc')}>
              {copied === 'trc' ? '已复制' : '复制'}
            </button>
          </div>
          <div className="pay-warn">⚠️ 仅 Tron / TRC20 网络 · 地址以 T 开头</div>
        </div>

        <div className="pay-card pay-card-crypto">
          <div className="pay-card-head">
            <span className="pay-icon pay-icon-sol">◎</span>
            <div>
              <div className="pay-card-title">USDT (Solana)</div>
              <div className="pay-card-en mono">USDT-SPL · ~$0.001 链上费</div>
            </div>
          </div>
          <div className="pay-addr-row">
            <code className="pay-addr mono" title={SOL_ADDR}>{SOL_ADDR}</code>
            <button className="pay-copy mono" onClick={() => copy(SOL_ADDR, 'sol')}>
              {copied === 'sol' ? '已复制' : '复制'}
            </button>
          </div>
          <div className="pay-warn">⚠️ 仅 Solana 网络 · 用错网络资金丢失</div>
        </div>

        <div className="pay-card pay-card-crypto">
          <div className="pay-card-head">
            <span className="pay-icon pay-icon-evm">⬢</span>
            <div>
              <div className="pay-card-title">USDT (EVM)</div>
              <div className="pay-card-en mono">BSC / Polygon / Arbitrum / ERC20</div>
            </div>
          </div>
          <div className="pay-addr-row">
            <code className="pay-addr mono" title={EVM_ADDR}>{EVM_ADDR}</code>
            <button className="pay-copy mono" onClick={() => copy(EVM_ADDR, 'evm')}>
              {copied === 'evm' ? '已复制' : '复制'}
            </button>
          </div>
          <div className="pay-warn">推荐 BSC / Polygon · ERC20 链上费贵</div>
        </div>
      </div>

      <div className="pay-foot mono">
        最低 $5 起充 · 余额永不过期 · 7 天无理由退款 · 详见 <a href="https://github.com/meiyaobuyao123-hash/AIzhongzhuanzhan/blob/main/docs/payment-methods.md" target="_blank" rel="noreferrer">支付方式文档</a>
      </div>
    </div>
  );
}

function PayCard({ icon, title, en, desc, badge }) {
  return (
    <div className="pay-card">
      <div className="pay-card-head">
        <span className={`pay-icon pay-icon-${icon}`}>
          {icon === 'alipay' && '支'}
          {icon === 'wechat' && '微'}
          {icon === 'bank' && '银'}
          {icon === 'stripe' && 'S'}
        </span>
        <div>
          <div className="pay-card-title">{title}</div>
          <div className="pay-card-en mono">{en}</div>
        </div>
      </div>
      <div className="pay-card-desc">{desc}</div>
      {badge && <div className="pay-badge">{badge}</div>}
    </div>
  );
}

function PriceCard({ tier, price, tagline, features, cta, ctaHref, featured }) {
  return (
    <article className={`price-card ${featured ? 'featured' : ''}`}>
      {featured && <div className="price-ribbon">推荐</div>}
      <header className="price-head">
        <div className="price-tier display">{tier}</div>
        <div className="price-cost-eq mono">cost = price</div>
        <div className="price-amount display">{price}</div>
        <div className="price-tagline">{tagline}</div>
      </header>
      <ul className="price-list">
        {features.map((f, i) => <li key={i} className="price-li"><Check/>{f}</li>)}
      </ul>
      <a href={ctaHref} className={featured ? 'cta-primary' : 'cta-ghost'}>
        {cta} <Arrow2/>
      </a>
      {featured && <div className="price-glow" aria-hidden="true"/>}
    </article>
  );
}

/* ─── 10 · FAQ ──────────────────────────────────────────────────── */

function FAQ() {
  const [open, setOpen] = useStateS(0);
  return (
    <section className="faq" id="faq">
      <SectionHeader
        kicker="FAQ"
        title="常见问题"
        sub="The questions you'd ask your finance team before signing."
      />
      <div className="faq-list">
        {window.PRISM_FAQ.map((it, i) => (
          <div key={i} className={`faq-item ${i === open ? 'open' : ''}`}>
            <button className="faq-q" onClick={() => setOpen(o => o === i ? -1 : i)}>
              <span className="faq-q-text">{it.q}</span>
              <span className="faq-q-icon" aria-hidden="true">{i === open ? '−' : '+'}</span>
            </button>
            <div className="faq-a"><p>{it.a}</p></div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ─── 11 · Final CTA + Footer ───────────────────────────────────── */

function FinalCTA() {
  return (
    <section className="final-cta" id="signup">
      <div className="fcta-card">
        <div className="fcta-eyebrow mono">ready when you are</div>
        <h2 className="fcta-title display">充 1 万到账 9995 · 立刻接入 200+ 模型</h2>
        <p className="fcta-sub">0% 加价 · 万 5 手续费 · 微信 / 支付宝 / USDT / 对公全通道</p>
        <div className="fcta-row">
          <a className="cta-primary" href="#signup">立即注册 <Arrow2/></a>
          <a className="cta-ghost" href="#docs">读 5 分钟 Quick Start</a>
        </div>
        <div className="fcta-glow" aria-hidden="true"/>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <Logo/>
          <div>
            <div className="footer-brand-name display">Prism</div>
            <div className="footer-brand-tag">透明的 AI 模型聚合网关</div>
          </div>
        </div>
        <nav className="footer-cols">
          <FCol title="产品" items={['模型列表','定价','文档','控制台','状态页']}/>
          <FCol title="开发者" items={['API Reference','SDK','Quick Start','客户端适配','开源组件']}/>
          <FCol title="公司" items={['关于我们','博客','加入我们','联系我们']}/>
          <FCol title="法律" items={['服务条款','隐私政策','数据政策','合规白皮书']}/>
        </nav>
      </div>
      <div className="footer-bottom mono">
        <span>© 2026 Prism Gateway</span>
        <span className="dot">·</span>
        <span>cost = price · always</span>
        <span className="dot">·</span>
        <span>京 ICP 备 占位号</span>
      </div>
    </footer>
  );
}

function FCol({ title, items }) {
  return (
    <div className="fcol">
      <div className="fcol-title mono">{title}</div>
      <ul>{items.map((it, i) => <li key={i}><a href="#">{it}</a></li>)}</ul>
    </div>
  );
}

/* ─── shared bits ───────────────────────────────────────────────── */

function SectionHeader({ kicker, title, sub }) {
  return (
    <header className="sec-head">
      {kicker && <div className="kicker mono">{kicker}</div>}
      <h2 className="sec-title display">{title}</h2>
      {sub && <p className="sec-sub mono">{sub}</p>}
    </header>
  );
}

function Logo({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" style={{display:'block'}}>
      <defs>
        <linearGradient id="lg-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%"  stopColor="#8B5CF6"/>
          <stop offset="35%" stopColor="#06B6D4"/>
          <stop offset="70%" stopColor="#EC4899"/>
          <stop offset="100%" stopColor="#F59E0B"/>
        </linearGradient>
      </defs>
      <path d="M 16 4 L 28 26 L 4 26 Z" stroke="url(#lg-grad)" strokeWidth="1.5" fill="none" strokeLinejoin="round"/>
      <path d="M 1 16 L 11 16" stroke="rgba(255,255,255,0.6)" strokeWidth="1" strokeLinecap="round"/>
      <path d="M 22 18 L 31 14" stroke="#8B5CF6" strokeWidth="1" strokeLinecap="round"/>
      <path d="M 22 19 L 31 18" stroke="#06B6D4" strokeWidth="1" strokeLinecap="round"/>
      <path d="M 22 20 L 31 22" stroke="#EC4899" strokeWidth="1" strokeLinecap="round"/>
      <path d="M 22 21 L 31 26" stroke="#F59E0B" strokeWidth="1" strokeLinecap="round"/>
    </svg>
  );
}

function Check() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path d="M3 7.5l3 3 5-7" stroke="url(#fi-grad)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function Arrow2() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path d="M2 7h8m-3-3 3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
