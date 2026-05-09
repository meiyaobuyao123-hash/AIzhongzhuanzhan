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
const _ts = window.t;  // local alias for t()

/* ─── i18n-driven content lists (replaces data.js for translatable copy) ─ */

const TRUST_LIST = [
  { num: '20+',  labelKey: 'trust.models'    },
  { num: '5',    labelKey: 'trust.providers' },
  { num: '1.5%', labelKey: 'trust.fee'       },
  { num: '0%',   labelKey: 'trust.markup', highlight: true },
];

const FEATURES_LIST = [
  { icon: 'price',    titleKey: 'feature.price.title',    bodyKey: 'feature.price.body'    },
  { icon: 'channel',  titleKey: 'feature.channel.title',  bodyKey: 'feature.channel.body'  },
  { icon: 'shield',   titleKey: 'feature.shield.title',   bodyKey: 'feature.shield.body'   },
  { icon: 'plug',     titleKey: 'feature.plug.title',     bodyKey: 'feature.plug.body'     },
  { icon: 'failover', titleKey: 'feature.failover.title', bodyKey: 'feature.failover.body' },
  { icon: 'observe',  titleKey: 'feature.observe.title',  bodyKey: 'feature.observe.body'  },
];

const NOTDOING_LIST = [
  { titleKey: 'nd.slicing.title',   bodyKey: 'nd.slicing.body'   },
  { titleKey: 'nd.downgrade.title', bodyKey: 'nd.downgrade.body' },
  { titleKey: 'nd.fees.title',      bodyKey: 'nd.fees.body'      },
  { titleKey: 'nd.blackbox.title',  bodyKey: 'nd.blackbox.body'  },
];

const CATEGORIES_LIST = [
  {
    id: 'coding', titleKey: 'cat.coding.title', whyKey: 'cat.coding.why',
    picks: [
      { model: 'Claude Sonnet 4.6', provider: 'anthropic', tipKey: 'cat.coding.tip1', price: '$3 / $15' },
      { model: 'Claude Haiku 4.5',  provider: 'anthropic', tipKey: 'cat.coding.tip2', price: '$0.80 / $4' },
      { model: 'DeepSeek V4',       provider: 'deepseek',  tipKey: 'cat.coding.tip3', price: '$0.27 / $1.10' },
    ],
  },
  {
    id: 'reasoning', titleKey: 'cat.reasoning.title', whyKey: 'cat.reasoning.why',
    picks: [
      { model: 'Claude Opus 4.7',   provider: 'anthropic', tipKey: 'cat.reasoning.tip1', price: '$15 / $75' },
      { model: 'OpenAI o3-mini',    provider: 'openai',    tipKey: 'cat.reasoning.tip2', price: '$1.10 / $4.40' },
      { model: 'DeepSeek Reasoner', provider: 'deepseek',  tipKey: 'cat.reasoning.tip3', price: '$0.55 / $2.19' },
    ],
  },
  {
    id: 'cheap', titleKey: 'cat.cheap.title', whyKey: 'cat.cheap.why',
    picks: [
      { model: 'Doubao 1.5 Lite',       provider: 'doubao', tipKey: 'cat.cheap.tip1', price: '$0.04 / $0.08' },
      { model: 'Doubao Seed 1.6 Flash', provider: 'doubao', tipKey: 'cat.cheap.tip2', price: '$0.02 / $0.21' },
      { model: 'GPT-4o mini',           provider: 'openai', tipKey: 'cat.cheap.tip3', price: '$0.15 / $0.60' },
    ],
  },
  {
    id: 'long', titleKey: 'cat.long.title', whyKey: 'cat.long.why',
    picks: [
      { model: 'Claude Opus 4.7',   provider: 'anthropic', tipKey: 'cat.long.tip1', price: '$15 / $75' },
      { model: 'Claude Sonnet 4.6', provider: 'anthropic', tipKey: 'cat.long.tip2', price: '$3 / $15' },
      { model: 'MiniMax Text-01',   provider: 'minimax',   tipKey: 'cat.long.tip3', price: '$0.14 / $1.11' },
    ],
  },
];

const CHANNEL_EXAMPLES = {
  'claude-opus-4-7': {
    nameKey: 'channels.ex.anthropic_official', providerKey: 'meta.brand_zh',
    channels: [
      { nameKey: 'channels.ex.anthropic_official', region: 'us-east-1', p50: 420, weight: 100, health: 'ok',
        policyKey: 'channels.ex.policy_default' },
    ],
  },
  'gpt-5': {
    nameKey: 'channels.ex.openai_official', providerKey: 'meta.brand_zh',
    channels: [
      { nameKey: 'channels.ex.openai_official', region: 'us', p50: 410, weight: 100, health: 'ok',
        policyKey: 'channels.ex.policy_default' },
    ],
  },
  'deepseek-chat': {
    nameKey: 'channels.ex.deepseek_official', providerKey: 'meta.brand_zh',
    channels: [
      { nameKey: 'channels.ex.deepseek_official', region: 'cn', p50: 360, weight: 100, health: 'ok',
        policyKey: 'channels.ex.policy_default' },
    ],
  },
  'doubao-seed-1-6-250615': {
    nameKey: 'channels.ex.volcengine', providerKey: 'channels.ex.volcengine_provider',
    channels: [
      { nameKey: 'channels.ex.volcengine', region: 'cn-beijing', p50: 340, weight: 100, health: 'ok',
        policyKey: 'channels.ex.policy_default' },
    ],
  },
};

const FAQ_LIST = [
  { qKey: 'faq.q1.q', aKey: 'faq.q1.a' },
  { qKey: 'faq.q2.q', aKey: 'faq.q2.a' },
  { qKey: 'faq.q3.q', aKey: 'faq.q3.a' },
  { qKey: 'faq.q4.q', aKey: 'faq.q4.a' },
  { qKey: 'faq.q5.q', aKey: 'faq.q5.a' },
  { qKey: 'faq.q6.q', aKey: 'faq.q6.a' },
];

/* ─── 2 · Trust strip ───────────────────────────────────────────── */

function TrustStrip() {
  return (
    <section className="trust-strip">
      <div className="trust-inner">
        {TRUST_LIST.map((m, i) => (
          <div key={i} className={`trust-item ${m.highlight ? 'highlight' : ''}`}>
            <div className="trust-num display">{m.num}</div>
            <div className="trust-label">
              <span>{_ts(m.labelKey)}</span>
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
        kicker={_ts('features.kicker')}
        title={_ts('features.title')}
        sub={_ts('features.sub')}
      />
      <div className="features-grid">
        {FEATURES_LIST.map((f, i) => (
          <article key={i} className="feature-card">
            <FeatureIcon name={f.icon} />
            <h3 className="feature-title display">
              {_ts(f.titleKey)}
            </h3>
            <p className="feature-body">{_ts(f.bodyKey)}</p>
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
  const fullResponse = _ts('demo.term_response');
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

  const userMsg = _ts('demo.message_user');
  const codeSamples = {
    python:
`from openai import OpenAI
client = OpenAI(
    base_url="https://www.ai100trading.cn/suanli-api/v1",
    api_key="sk-prism-…",
)
stream = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role":"user","content":"${userMsg}"}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")`,
    node:
`import OpenAI from "openai";
const client = new OpenAI({
  baseURL: "https://www.ai100trading.cn/suanli-api/v1",
  apiKey: process.env.PRISM_KEY,
});
const stream = await client.chat.completions.create({
  model: "claude-sonnet-4-6",
  messages: [{ role: "user", content: "${userMsg}" }],
  stream: true,
});
for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? "");
}`,
    curl:
`curl https://www.ai100trading.cn/suanli-api/v1/chat/completions \\
  -H "Authorization: Bearer sk-prism-…" \\
  -H "Content-Type: application/json" \\
  --no-buffer \\
  -d '{
    "model": "claude-sonnet-4-6",
    "messages": [{"role":"user","content":"${userMsg}"}],
    "stream": true
  }'`,
  };

  return (
    <section className="live-demo" id="demo">
      <SectionHeader
        kicker={_ts('demo.kicker')}
        title={_ts('demo.title')}
        sub={_ts('demo.sub')}
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
              {_ts('demo.copy')}
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
            <span className="ld-streaming"><span className="ld-streaming-dot"/>{_ts('demo.streaming')}</span>
          </div>
          <div className="ld-term-body mono">
            <span className="ld-prompt">$</span> python demo.py
            <div className="ld-stream">{streamText}<span className="ld-caret"/></div>
          </div>
          <div className="ld-term-foot mono">
            <span>{_ts('demo.routed_to')}</span>
            <em>{_ts('demo.routed_via')}</em>
            <span className="dot">·</span>
            <span>{_ts('demo.foot')}</span>
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
        kicker={_ts('clients.kicker')}
        title={_ts('clients.title')}
        sub={_ts('clients.sub')}
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
        kicker={_ts('categories.kicker')}
        title={_ts('categories.title')}
        sub={_ts('categories.sub')}
      />
      <div className="cat-grid">
        {CATEGORIES_LIST.map(cat => <CategoryCard key={cat.id} cat={cat}/>)}
      </div>
      <div className="cat-foot">
        <a href="/api-docs#tag/models" className="cta-ghost">{_ts('categories.see_all')}</a>
      </div>
    </section>
  );
}

function CategoryCard({ cat }) {
  return (
    <article className="cat-card">
      <header className="cat-head">
        <h3 className="cat-title display">
          {_ts(cat.titleKey)}
        </h3>
        <p className="cat-why">{_ts(cat.whyKey)}</p>
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
              <div className="cat-pick-tip">{_ts(p.tipKey)}</div>
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
  const keys = Object.keys(CHANNEL_EXAMPLES);
  const [active, setActive] = useStateS(keys[0]);
  const example = CHANNEL_EXAMPLES[active];

  return (
    <section className="channels" id="channels">
      <SectionHeader
        kicker={_ts('channels.kicker')}
        title={_ts('channels.title')}
        sub={_ts('channels.sub')}
      />

      <div className="ch-toggle">
        {keys.map(k => (
          <button
            key={k}
            className={`ch-tog-btn ${k === active ? 'active' : ''}`}
            onClick={() => setActive(k)}
          >
            {_ts(CHANNEL_EXAMPLES[k].nameKey)}
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
          <div className="ch-node-label">{_ts('channels.user_request')}</div>
        </div>

        <div className="ch-line ch-line-1" aria-hidden="true"/>

        <div className="ch-node prism">
          <div className="ch-node-icon iridescent-text" style={{fontSize: 20, fontFamily: 'var(--font-display)', fontWeight: 700}}>P</div>
          <div className="ch-node-label">{_ts('channels.router')}</div>
        </div>

        <div className="ch-arc">
          {example.channels.map((ch, i) => (
            <div key={i} className={`ch-card arc-${i+1}`}>
              <div className="ch-card-head">
                <span className="ch-card-name">{_ts(ch.nameKey)}</span>
                <span className={`ch-health h-${ch.health}`}>{ch.health}</span>
              </div>
              <div className="ch-card-meta">
                <div><span className="meta-k">{_ts('channels.ex.region_label')}</span><span className="meta-v mono">{ch.region}</span></div>
                <div><span className="meta-k">p50</span><span className="meta-v mono">{ch.p50}ms</span></div>
                <div><span className="meta-k">weight</span><span className="meta-v mono">{ch.weight}%</span></div>
              </div>
              <div className="ch-card-policy">{_ts(ch.policyKey)}</div>
              <div className="ch-weight-bar">
                <div className="ch-weight-fill" style={{width: `${ch.weight}%`, background: 'var(--iridescent)'}}/>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="ch-foot">
        <span>{_ts('channels.foot')}</span>
        <a className="link-arrow" href="/quickstart">{_ts('channels.read_quickstart')}</a>
      </div>
    </section>
  );
}

/* ─── 8 · We don't do ───────────────────────────────────────────── */

function NotDoing() {
  return (
    <section className="not-doing" id="not-doing">
      <SectionHeader
        kicker={_ts('notdoing.kicker')}
        title={_ts('notdoing.title')}
        sub={_ts('notdoing.sub')}
      />
      <div className="nd-grid">
        {NOTDOING_LIST.map((it, i) => (
          <article key={i} className="nd-card">
            <div className="nd-cross" aria-hidden="true">✕</div>
            <h3 className="nd-title display">
              {_ts(it.titleKey)}
            </h3>
            <p className="nd-body">{_ts(it.bodyKey)}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

/* ─── 9 · Pricing preview ───────────────────────────────────────── */

function PricingPreview() {
  const [model, setModel] = useStateS(window.PRISM_HERO_MODELS[1]);
  const [tokens, setTokens] = useStateS(100_000);
  const [contactOpen, setContactOpen] = useStateS(false);
  const cost = ((tokens / 1_000_000) * (model.priceIn + model.priceOut * 3)).toFixed(4);

  return (
    <section className="pricing" id="pricing">
      <SectionHeader
        kicker={_ts('pricing.kicker')}
        title={_ts('pricing.title')}
        sub={_ts('pricing.sub')}
      />
      <div className="price-grid price-grid-2">
        <PriceCard
          tier={_ts('pricing.tier.self.tier')}
          featured
          price={_ts('pricing.tier.self.price')}
          tagline={_ts('pricing.tier.self.tagline')}
          features={[
            _ts('pricing.tier.self.f1'),
            _ts('pricing.tier.self.f2'),
            _ts('pricing.tier.self.f3'),
            _ts('pricing.tier.self.f4'),
            _ts('pricing.tier.self.f5'),
          ]}
          cta={_ts('pricing.tier.self.cta')}
          ctaHref="/signup"
        />
        <PriceCard
          tier={_ts('pricing.tier.team.tier')}
          price={_ts('pricing.tier.team.price')}
          tagline={_ts('pricing.tier.team.tagline')}
          features={[
            _ts('pricing.tier.team.f1'),
            _ts('pricing.tier.team.f2'),
            _ts('pricing.tier.team.f3'),
            _ts('pricing.tier.team.f4'),
            _ts('pricing.tier.team.f5'),
            _ts('pricing.tier.team.f6'),
          ]}
          cta={_ts('pricing.tier.team.cta')}
          onClick={() => setContactOpen(true)}
        />
      </div>
      {contactOpen && <ContactSalesModal onClose={() => setContactOpen(false)}/>}

      <div className="price-calc">
        <div className="pc-head">
          <span className="kicker mono">{_ts('pricing.calc.kicker')}</span>
          <h3 className="pc-title display">{_ts('pricing.calc.title')}</h3>
        </div>
        <div className="pc-controls">
          <label className="pc-field">
            <span className="pc-label">{_ts('pricing.calc.model')}</span>
            <select
              className="pc-input"
              value={model.id}
              onChange={e => setModel(window.PRISM_HERO_MODELS.find(m => m.id === e.target.value))}
            >
              {window.PRISM_HERO_MODELS.map(m => <option key={m.id} value={m.id}>{m.display}</option>)}
            </select>
          </label>
          <label className="pc-field">
            <span className="pc-label">{_ts('pricing.calc.tokens')}</span>
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
              <span>{_ts('pricing.calc.prism')}</span>
              <span className="display pc-num">${cost}</span>
            </div>
            <div className="pc-result-row pc-result-secondary">
              <span>{_ts('pricing.calc.vs')}</span>
              <span className="mono">{_ts('pricing.calc.match')}</span>
            </div>
          </div>
        </div>
        <div className="pc-note">{_ts('pricing.calc.note')}</div>
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
        <span className="kicker mono">{_ts('pay.kicker')}</span>
        <h3 className="pay-title display">{_ts('pay.title')}</h3>
        <p className="pay-sub mono">{_ts('pay.sub')}</p>
      </div>

      <div className="pay-grid">
        <PayCard icon="alipay" titleKey="pay.alipay.title" descKey="pay.alipay.desc" badgeKey="pay.alipay.badge" />
        <PayCard icon="wechat" titleKey="pay.wechat.title" descKey="pay.wechat.desc" badgeKey="pay.wechat.badge" />
        <PayCard icon="bank"   titleKey="pay.bank.title"   descKey="pay.bank.desc"   badgeKey="pay.bank.badge" />

        <div className="pay-card pay-card-crypto">
          <div className="pay-card-head">
            <span className="pay-icon pay-icon-trc">T</span>
            <div>
              <div className="pay-card-title">
                USDC (TRC20)
                <span className="pay-card-pill">{_ts('pay.usdc.recommended')}</span>
              </div>
              <div className="pay-card-en mono">{_ts('pay.usdc.trc.tag')}</div>
            </div>
          </div>
          <div className="pay-addr-row">
            <code className="pay-addr mono" title={TRC_ADDR}>{TRC_ADDR}</code>
            <button className="pay-copy mono" onClick={() => copy(TRC_ADDR, 'trc')}>
              {copied === 'trc' ? _ts('pay.copied') : _ts('pay.copy')}
            </button>
          </div>
          <div className="pay-warn">⚠️ {_ts('pay.usdc.trc.warn')}</div>
        </div>

        <div className="pay-card pay-card-crypto">
          <div className="pay-card-head">
            <span className="pay-icon pay-icon-sol">◎</span>
            <div>
              <div className="pay-card-title">USDC (Solana)</div>
              <div className="pay-card-en mono">{_ts('pay.usdc.sol.tag')}</div>
            </div>
          </div>
          <div className="pay-addr-row">
            <code className="pay-addr mono" title={SOL_ADDR}>{SOL_ADDR}</code>
            <button className="pay-copy mono" onClick={() => copy(SOL_ADDR, 'sol')}>
              {copied === 'sol' ? _ts('pay.copied') : _ts('pay.copy')}
            </button>
          </div>
          <div className="pay-warn">⚠️ {_ts('pay.usdc.sol.warn')}</div>
        </div>

        <div className="pay-card pay-card-crypto">
          <div className="pay-card-head">
            <span className="pay-icon pay-icon-evm">⬢</span>
            <div>
              <div className="pay-card-title">USDC (EVM)</div>
              <div className="pay-card-en mono">{_ts('pay.usdc.evm.tag')}</div>
            </div>
          </div>
          <div className="pay-addr-row">
            <code className="pay-addr mono" title={EVM_ADDR}>{EVM_ADDR}</code>
            <button className="pay-copy mono" onClick={() => copy(EVM_ADDR, 'evm')}>
              {copied === 'evm' ? _ts('pay.copied') : _ts('pay.copy')}
            </button>
          </div>
          <div className="pay-warn">{_ts('pay.usdc.evm.warn')}</div>
        </div>
      </div>

      <div className="pay-foot mono">
        {_ts('pay.foot')}
        <a href="https://github.com/meiyaobuyao123-hash/AIzhongzhuanzhan/blob/main/docs/payment-methods.md" target="_blank" rel="noreferrer">{_ts('pay.foot.link')}</a>
      </div>
    </div>
  );
}

function PayCard({ icon, titleKey, descKey, badgeKey }) {
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
          <div className="pay-card-title">{_ts(titleKey)}</div>
        </div>
      </div>
      <div className="pay-card-desc">{_ts(descKey)}</div>
      {badgeKey && <div className="pay-badge">{_ts(badgeKey)}</div>}
    </div>
  );
}

function PriceCard({ tier, price, tagline, features, cta, ctaHref, onClick, featured }) {
  const cls = featured ? 'cta-primary' : 'cta-ghost';
  return (
    <article className={`price-card ${featured ? 'featured' : ''}`}>
      {featured && <div className="price-ribbon">{_ts('pricing.recommended')}</div>}
      <header className="price-head">
        <div className="price-tier display">{tier}</div>
        <div className="price-cost-eq mono">cost = price</div>
        <div className="price-amount display">{price}</div>
        <div className="price-tagline">{tagline}</div>
      </header>
      <ul className="price-list">
        {features.map((f, i) => <li key={i} className="price-li"><Check/>{f}</li>)}
      </ul>
      {onClick ? (
        <button type="button" className={cls} onClick={onClick}
                style={{border: 'none', cursor: 'pointer', font: 'inherit'}}>
          {cta} <Arrow2/>
        </button>
      ) : (
        <a href={ctaHref} className={cls}>{cta} <Arrow2/></a>
      )}
      {featured && <div className="price-glow" aria-hidden="true"/>}
    </article>
  );
}

/* ─── Contact Sales modal: WeChat add-friend QR ────────────────── */

function ContactSalesModal({ onClose }) {
  return (
    <div className="cs-modal-overlay" onClick={onClose}
         style={{
           position: 'fixed', inset: 0, zIndex: 1000,
           background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(6px)',
           display: 'flex', alignItems: 'center', justifyContent: 'center',
         }}>
      <div onClick={e => e.stopPropagation()}
           style={{
             background: '#FFFFFF', color: '#18181B',
             borderRadius: 14, padding: '28px 32px 24px', maxWidth: 380, width: '90%',
             boxShadow: '0 20px 50px rgba(0,0,0,0.30)',
             fontFamily: 'Inter, system-ui, sans-serif',
             textAlign: 'center',
           }}>
        <h2 style={{margin: '0 0 6px', fontSize: 20, fontWeight: 600, letterSpacing: '-0.02em'}}>
          {_ts('contact.title')}
        </h2>
        <p style={{margin: '0 0 18px', color: '#71717A', fontSize: 13}}>
          {_ts('contact.sub')}
        </p>
        <img src="/suanli/qr-wechat-contact.jpg"
             alt={_ts('contact.alt')}
             style={{width: '100%', maxWidth: 260, borderRadius: 10, display: 'block', margin: '0 auto'}}/>
        <p style={{margin: '14px 0 0', fontSize: 12, color: '#A1A1AA'}}>
          {_ts('contact.signature')}
        </p>
        <button onClick={onClose}
                style={{
                  marginTop: 18, padding: '8px 18px', borderRadius: 6,
                  background: '#F4F4F5', border: '1px solid rgba(0,0,0,0.10)',
                  color: '#18181B', fontSize: 13, cursor: 'pointer',
                  fontFamily: 'inherit',
                }}>
          {_ts('contact.close')}
        </button>
      </div>
    </div>
  );
}

/* ─── 10 · FAQ ──────────────────────────────────────────────────── */

function FAQ() {
  const [open, setOpen] = useStateS(0);
  return (
    <section className="faq" id="faq">
      <SectionHeader
        kicker={_ts('faq.kicker')}
        title={_ts('faq.title')}
        sub={_ts('faq.sub')}
      />
      <div className="faq-list">
        {FAQ_LIST.map((it, i) => (
          <div key={i} className={`faq-item ${i === open ? 'open' : ''}`}>
            <button className="faq-q" onClick={() => setOpen(o => o === i ? -1 : i)}>
              <span className="faq-q-text">{_ts(it.qKey)}</span>
              <span className="faq-q-icon" aria-hidden="true">{i === open ? '−' : '+'}</span>
            </button>
            <div className="faq-a"><p>{_ts(it.aKey)}</p></div>
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
        <div className="fcta-eyebrow mono">{_ts('fcta.eyebrow')}</div>
        <h2 className="fcta-title display">{_ts('fcta.title')}</h2>
        <p className="fcta-sub">{_ts('fcta.sub')}</p>
        <div className="fcta-row">
          <a className="cta-primary" href="/signup">{_ts('fcta.cta1')} <Arrow2/></a>
          <a className="cta-ghost" href="/quickstart">{_ts('fcta.cta2')}</a>
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
            <div className="footer-brand-tag">{_ts('footer.tag')}</div>
          </div>
        </div>
        <nav className="footer-cols">
          <FCol titleKey="footer.product" items={[
            {labelKey:'nav.pricing', href:'#pricing'},
            {labelKey:'nav.console', href:'/console'},
            {labelKey:'nav.login',   href:'/login'},
            {labelKey:'nav.signup',  href:'/signup'},
          ]}/>
          <FCol titleKey="footer.dev" items={[
            {labelKey:'console.api_docs', href:'/api-docs'},
            {labelKey:'console.quickstart', href:'/quickstart'},
            {labelKey:'clients.kicker', href:'#clients'},
          ]}/>
          <FCol titleKey="footer.company" items={[
            {labelKey:'contact.title', href:'#pricing'},
          ]}/>
        </nav>
      </div>
      <div className="footer-bottom mono">
        <span>© 2026 Prism Gateway</span>
        <span className="dot">·</span>
        <span>cost = price · always</span>
        <span className="dot">·</span>
        <span>{_ts('footer.icp')}</span>
      </div>
    </footer>
  );
}

function FCol({ titleKey, items }) {
  return (
    <div className="fcol">
      <div className="fcol-title mono">{_ts(titleKey)}</div>
      <ul>
        {items.map((it, i) => (
          <li key={i}>
            <a href={it.href}>{_ts(it.labelKey)}</a>
          </li>
        ))}
      </ul>
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
