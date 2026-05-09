const { useState: useStateS, useEffect: useEffectS, useMemo: useMemoS, useRef: useRefS } = React;
const _ts = window.t;
const TRUST_LIST = [
  { num: "20+", labelKey: "trust.models" },
  { num: "5", labelKey: "trust.providers" },
  { num: "1.5%", labelKey: "trust.fee" },
  { num: "0%", labelKey: "trust.markup", highlight: true }
];
const FEATURES_LIST = [
  { icon: "price", titleKey: "feature.price.title", bodyKey: "feature.price.body" },
  { icon: "channel", titleKey: "feature.channel.title", bodyKey: "feature.channel.body" },
  { icon: "shield", titleKey: "feature.shield.title", bodyKey: "feature.shield.body" },
  { icon: "plug", titleKey: "feature.plug.title", bodyKey: "feature.plug.body" },
  { icon: "failover", titleKey: "feature.failover.title", bodyKey: "feature.failover.body" },
  { icon: "observe", titleKey: "feature.observe.title", bodyKey: "feature.observe.body" }
];
const NOTDOING_LIST = [
  { titleKey: "nd.slicing.title", bodyKey: "nd.slicing.body" },
  { titleKey: "nd.downgrade.title", bodyKey: "nd.downgrade.body" },
  { titleKey: "nd.fees.title", bodyKey: "nd.fees.body" },
  { titleKey: "nd.blackbox.title", bodyKey: "nd.blackbox.body" }
];
const CATEGORIES_LIST = [
  {
    id: "coding",
    titleKey: "cat.coding.title",
    whyKey: "cat.coding.why",
    picks: [
      { model: "Claude Sonnet 4.6", provider: "anthropic", tipKey: "cat.coding.tip1", price: "$3 / $15" },
      { model: "Claude Haiku 4.5", provider: "anthropic", tipKey: "cat.coding.tip2", price: "$0.80 / $4" },
      { model: "DeepSeek V4", provider: "deepseek", tipKey: "cat.coding.tip3", price: "$0.27 / $1.10" }
    ]
  },
  {
    id: "reasoning",
    titleKey: "cat.reasoning.title",
    whyKey: "cat.reasoning.why",
    picks: [
      { model: "Claude Opus 4.7", provider: "anthropic", tipKey: "cat.reasoning.tip1", price: "$15 / $75" },
      { model: "OpenAI o3-mini", provider: "openai", tipKey: "cat.reasoning.tip2", price: "$1.10 / $4.40" },
      { model: "DeepSeek Reasoner", provider: "deepseek", tipKey: "cat.reasoning.tip3", price: "$0.55 / $2.19" }
    ]
  },
  {
    id: "cheap",
    titleKey: "cat.cheap.title",
    whyKey: "cat.cheap.why",
    picks: [
      { model: "Doubao 1.5 Lite", provider: "doubao", tipKey: "cat.cheap.tip1", price: "$0.04 / $0.08" },
      { model: "Doubao Seed 1.6 Flash", provider: "doubao", tipKey: "cat.cheap.tip2", price: "$0.02 / $0.21" },
      { model: "GPT-4o mini", provider: "openai", tipKey: "cat.cheap.tip3", price: "$0.15 / $0.60" }
    ]
  },
  {
    id: "long",
    titleKey: "cat.long.title",
    whyKey: "cat.long.why",
    picks: [
      { model: "Claude Opus 4.7", provider: "anthropic", tipKey: "cat.long.tip1", price: "$15 / $75" },
      { model: "Claude Sonnet 4.6", provider: "anthropic", tipKey: "cat.long.tip2", price: "$3 / $15" },
      { model: "MiniMax Text-01", provider: "minimax", tipKey: "cat.long.tip3", price: "$0.14 / $1.11" }
    ]
  }
];
const CHANNEL_EXAMPLES = {
  "claude-opus-4-7": {
    nameKey: "channels.ex.anthropic_official",
    providerKey: "meta.brand_zh",
    channels: [
      {
        nameKey: "channels.ex.anthropic_official",
        region: "us-east-1",
        p50: 420,
        weight: 100,
        health: "ok",
        policyKey: "channels.ex.policy_default"
      }
    ]
  },
  "gpt-5": {
    nameKey: "channels.ex.openai_official",
    providerKey: "meta.brand_zh",
    channels: [
      {
        nameKey: "channels.ex.openai_official",
        region: "us",
        p50: 410,
        weight: 100,
        health: "ok",
        policyKey: "channels.ex.policy_default"
      }
    ]
  },
  "deepseek-chat": {
    nameKey: "channels.ex.deepseek_official",
    providerKey: "meta.brand_zh",
    channels: [
      {
        nameKey: "channels.ex.deepseek_official",
        region: "cn",
        p50: 360,
        weight: 100,
        health: "ok",
        policyKey: "channels.ex.policy_default"
      }
    ]
  },
  "doubao-seed-1-6-250615": {
    nameKey: "channels.ex.volcengine",
    providerKey: "channels.ex.volcengine_provider",
    channels: [
      {
        nameKey: "channels.ex.volcengine",
        region: "cn-beijing",
        p50: 340,
        weight: 100,
        health: "ok",
        policyKey: "channels.ex.policy_default"
      }
    ]
  }
};
const FAQ_LIST = [
  { qKey: "faq.q1.q", aKey: "faq.q1.a" },
  { qKey: "faq.q2.q", aKey: "faq.q2.a" },
  { qKey: "faq.q3.q", aKey: "faq.q3.a" },
  { qKey: "faq.q4.q", aKey: "faq.q4.a" },
  { qKey: "faq.q5.q", aKey: "faq.q5.a" },
  { qKey: "faq.q6.q", aKey: "faq.q6.a" }
];
function TrustStrip() {
  return /* @__PURE__ */ React.createElement("section", { className: "trust-strip" }, /* @__PURE__ */ React.createElement("div", { className: "trust-inner" }, TRUST_LIST.map((m, i) => /* @__PURE__ */ React.createElement("div", { key: i, className: `trust-item ${m.highlight ? "highlight" : ""}` }, /* @__PURE__ */ React.createElement("div", { className: "trust-num display" }, m.num), /* @__PURE__ */ React.createElement("div", { className: "trust-label" }, /* @__PURE__ */ React.createElement("span", null, _ts(m.labelKey)))))));
}
function FeaturesGrid() {
  return /* @__PURE__ */ React.createElement("section", { className: "features", id: "features" }, /* @__PURE__ */ React.createElement(
    SectionHeader,
    {
      kicker: _ts("features.kicker"),
      title: _ts("features.title"),
      sub: _ts("features.sub")
    }
  ), /* @__PURE__ */ React.createElement("div", { className: "features-grid" }, FEATURES_LIST.map((f, i) => /* @__PURE__ */ React.createElement("article", { key: i, className: "feature-card" }, /* @__PURE__ */ React.createElement(FeatureIcon, { name: f.icon }), /* @__PURE__ */ React.createElement("h3", { className: "feature-title display" }, _ts(f.titleKey)), /* @__PURE__ */ React.createElement("p", { className: "feature-body" }, _ts(f.bodyKey)), /* @__PURE__ */ React.createElement("div", { className: "feature-glow", "aria-hidden": "true" })))));
}
function FeatureIcon({ name }) {
  const common = { width: 28, height: 28, viewBox: "0 0 28 28", fill: "none" };
  const stroke = "url(#fi-grad)";
  const grad = /* @__PURE__ */ React.createElement("defs", null, /* @__PURE__ */ React.createElement("linearGradient", { id: "fi-grad", x1: "0", y1: "0", x2: "1", y2: "1" }, /* @__PURE__ */ React.createElement("stop", { offset: "0%", stopColor: "#8B5CF6" }), /* @__PURE__ */ React.createElement("stop", { offset: "50%", stopColor: "#06B6D4" }), /* @__PURE__ */ React.createElement("stop", { offset: "100%", stopColor: "#EC4899" })));
  return /* @__PURE__ */ React.createElement("span", { className: "feature-icon" }, name === "price" && /* @__PURE__ */ React.createElement("svg", { ...common }, grad, /* @__PURE__ */ React.createElement("circle", { cx: "14", cy: "14", r: "10", stroke, strokeWidth: "1.5" }), /* @__PURE__ */ React.createElement("path", { d: "M11 17.5h6M11 13.5h6M11 9.5h6", stroke, strokeWidth: "1.4", strokeLinecap: "round" })), name === "channel" && /* @__PURE__ */ React.createElement("svg", { ...common }, grad, /* @__PURE__ */ React.createElement("path", { d: "M5 14h6m6 0h6", stroke, strokeWidth: "1.4", strokeLinecap: "round" }), /* @__PURE__ */ React.createElement("circle", { cx: "14", cy: "14", r: "3.2", stroke, strokeWidth: "1.4" }), /* @__PURE__ */ React.createElement("circle", { cx: "5", cy: "14", r: "1.5", fill: stroke }), /* @__PURE__ */ React.createElement("circle", { cx: "23", cy: "14", r: "1.5", fill: stroke })), name === "shield" && /* @__PURE__ */ React.createElement("svg", { ...common }, grad, /* @__PURE__ */ React.createElement("path", { d: "M14 4 L23 8 V14 C23 19 19 23 14 24 C9 23 5 19 5 14 V8 Z", stroke, strokeWidth: "1.5", strokeLinejoin: "round" }), /* @__PURE__ */ React.createElement("path", { d: "M10 14 L13 17 L18 11", stroke, strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" })), name === "plug" && /* @__PURE__ */ React.createElement("svg", { ...common }, grad, /* @__PURE__ */ React.createElement("rect", { x: "6", y: "9", width: "6", height: "10", rx: "2", stroke, strokeWidth: "1.4" }), /* @__PURE__ */ React.createElement("rect", { x: "16", y: "9", width: "6", height: "10", rx: "2", stroke, strokeWidth: "1.4" }), /* @__PURE__ */ React.createElement("path", { d: "M12 14h4", stroke, strokeWidth: "1.4", strokeLinecap: "round" }), /* @__PURE__ */ React.createElement("path", { d: "M9  6v3M19 6v3M9 19v3M19 19v3", stroke, strokeWidth: "1.4", strokeLinecap: "round" })), name === "failover" && /* @__PURE__ */ React.createElement("svg", { ...common }, grad, /* @__PURE__ */ React.createElement("circle", { cx: "8", cy: "14", r: "2.5", stroke, strokeWidth: "1.4" }), /* @__PURE__ */ React.createElement("circle", { cx: "20", cy: "9", r: "2.5", stroke, strokeWidth: "1.4" }), /* @__PURE__ */ React.createElement("circle", { cx: "20", cy: "19", r: "2.5", stroke, strokeWidth: "1.4" }), /* @__PURE__ */ React.createElement("path", { d: "M10.5 13l7-3M10.5 15l7 3", stroke, strokeWidth: "1.3" }), /* @__PURE__ */ React.createElement("path", { d: "M18 7l3 2-3 2", stroke, strokeWidth: "1.3", strokeLinecap: "round", strokeLinejoin: "round" })), name === "observe" && /* @__PURE__ */ React.createElement("svg", { ...common }, grad, /* @__PURE__ */ React.createElement("rect", { x: "4", y: "6", width: "20", height: "14", rx: "2", stroke, strokeWidth: "1.4" }), /* @__PURE__ */ React.createElement("path", { d: "M7 16l4-4 3 3 5-7", stroke, strokeWidth: "1.4", strokeLinecap: "round", strokeLinejoin: "round" })));
}
function LiveDemo() {
  const [lang, setLang] = useStateS("python");
  const [streamText, setStreamText] = useStateS("");
  const fullResponse = _ts("demo.term_response");
  const tickRef = useRefS(null);
  useEffectS(() => {
    let i = 0;
    setStreamText("");
    if (tickRef.current) clearInterval(tickRef.current);
    tickRef.current = setInterval(() => {
      i += 1;
      setStreamText(fullResponse.slice(0, i));
      if (i >= fullResponse.length) clearInterval(tickRef.current);
    }, 28);
    return () => clearInterval(tickRef.current);
  }, [lang]);
  const userMsg = _ts("demo.message_user");
  const codeSamples = {
    python: `from openai import OpenAI
client = OpenAI(
    base_url="https://www.ai100trading.cn/suanli-api/v1",
    api_key="sk-prism-\u2026",
)
stream = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role":"user","content":"${userMsg}"}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")`,
    node: `import OpenAI from "openai";
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
    curl: `curl https://www.ai100trading.cn/suanli-api/v1/chat/completions \\
  -H "Authorization: Bearer sk-prism-\u2026" \\
  -H "Content-Type: application/json" \\
  --no-buffer \\
  -d '{
    "model": "claude-sonnet-4-6",
    "messages": [{"role":"user","content":"${userMsg}"}],
    "stream": true
  }'`
  };
  return /* @__PURE__ */ React.createElement("section", { className: "live-demo", id: "demo" }, /* @__PURE__ */ React.createElement(
    SectionHeader,
    {
      kicker: _ts("demo.kicker"),
      title: _ts("demo.title"),
      sub: _ts("demo.sub")
    }
  ), /* @__PURE__ */ React.createElement("div", { className: "ld-grid" }, /* @__PURE__ */ React.createElement("div", { className: "ld-code" }, /* @__PURE__ */ React.createElement("div", { className: "ld-tabs" }, [["python", "Python"], ["node", "Node.js"], ["curl", "curl"]].map(([k, v]) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: k,
      className: `ld-tab mono ${lang === k ? "active" : ""}`,
      onClick: () => setLang(k)
    },
    v
  )), /* @__PURE__ */ React.createElement("button", { className: "ld-copy mono", onClick: () => navigator.clipboard?.writeText(codeSamples[lang]) }, _ts("demo.copy"))), /* @__PURE__ */ React.createElement("pre", { className: "ld-block mono" }, codeSamples[lang])), /* @__PURE__ */ React.createElement("div", { className: "ld-terminal" }, /* @__PURE__ */ React.createElement("div", { className: "ld-term-head" }, /* @__PURE__ */ React.createElement("span", { className: "cw-dot d1" }), /* @__PURE__ */ React.createElement("span", { className: "cw-dot d2" }), /* @__PURE__ */ React.createElement("span", { className: "cw-dot d3" }), /* @__PURE__ */ React.createElement("span", { className: "cw-title mono" }, "prism \xB7 streaming response"), /* @__PURE__ */ React.createElement("span", { className: "ld-streaming" }, /* @__PURE__ */ React.createElement("span", { className: "ld-streaming-dot" }), _ts("demo.streaming"))), /* @__PURE__ */ React.createElement("div", { className: "ld-term-body mono" }, /* @__PURE__ */ React.createElement("span", { className: "ld-prompt" }, "$"), " python demo.py", /* @__PURE__ */ React.createElement("div", { className: "ld-stream" }, streamText, /* @__PURE__ */ React.createElement("span", { className: "ld-caret" }))), /* @__PURE__ */ React.createElement("div", { className: "ld-term-foot mono" }, /* @__PURE__ */ React.createElement("span", null, _ts("demo.routed_to")), /* @__PURE__ */ React.createElement("em", null, _ts("demo.routed_via")), /* @__PURE__ */ React.createElement("span", { className: "dot" }, "\xB7"), /* @__PURE__ */ React.createElement("span", null, _ts("demo.foot"))))));
}
function ClientStrip() {
  return /* @__PURE__ */ React.createElement("section", { className: "clients", id: "clients" }, /* @__PURE__ */ React.createElement(
    SectionHeader,
    {
      kicker: _ts("clients.kicker"),
      title: _ts("clients.title"),
      sub: _ts("clients.sub")
    }
  ), /* @__PURE__ */ React.createElement("div", { className: "client-row" }, window.PRISM_CLIENTS.map((c, i) => /* @__PURE__ */ React.createElement(ClientTile, { key: i, client: c }))));
}
function ClientTile({ client }) {
  const [flipped, setFlipped] = useStateS(false);
  return /* @__PURE__ */ React.createElement(
    "div",
    {
      className: `client-tile ${flipped ? "flipped" : ""}`,
      onMouseEnter: () => setFlipped(true),
      onMouseLeave: () => setFlipped(false),
      onClick: () => setFlipped((f) => !f)
    },
    /* @__PURE__ */ React.createElement("div", { className: "client-front" }, /* @__PURE__ */ React.createElement(ClientGlyph, { name: client.name }), /* @__PURE__ */ React.createElement("span", { className: "client-name" }, client.name)),
    /* @__PURE__ */ React.createElement("div", { className: "client-back mono" }, client.config)
  );
}
function ClientGlyph({ name }) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = h * 31 + name.charCodeAt(i) >>> 0;
  const hue = h % 360;
  return /* @__PURE__ */ React.createElement(
    "span",
    {
      className: "client-glyph",
      style: {
        background: `linear-gradient(135deg, hsla(${hue}, 70%, 55%, 0.4), hsla(${(hue + 60) % 360}, 70%, 55%, 0.4))`,
        borderColor: `hsla(${hue}, 70%, 55%, 0.5)`
      }
    },
    name[0]
  );
}
function CategoryGrid() {
  return /* @__PURE__ */ React.createElement("section", { className: "categories", id: "models" }, /* @__PURE__ */ React.createElement(
    SectionHeader,
    {
      kicker: _ts("categories.kicker"),
      title: _ts("categories.title"),
      sub: _ts("categories.sub")
    }
  ), /* @__PURE__ */ React.createElement("div", { className: "cat-grid" }, CATEGORIES_LIST.map((cat) => /* @__PURE__ */ React.createElement(CategoryCard, { key: cat.id, cat }))), /* @__PURE__ */ React.createElement("div", { className: "cat-foot" }, /* @__PURE__ */ React.createElement("a", { href: "/api-docs#tag/models", className: "cta-ghost" }, _ts("categories.see_all"))));
}
function CategoryCard({ cat }) {
  return /* @__PURE__ */ React.createElement("article", { className: "cat-card" }, /* @__PURE__ */ React.createElement("header", { className: "cat-head" }, /* @__PURE__ */ React.createElement("h3", { className: "cat-title display" }, _ts(cat.titleKey)), /* @__PURE__ */ React.createElement("p", { className: "cat-why" }, _ts(cat.whyKey))), /* @__PURE__ */ React.createElement("ul", { className: "cat-picks" }, cat.picks.map((p, i) => /* @__PURE__ */ React.createElement("li", { key: i, className: "cat-pick" }, /* @__PURE__ */ React.createElement("span", { className: "cat-pick-glyph" }, /* @__PURE__ */ React.createElement(ClientGlyph, { name: p.provider })), /* @__PURE__ */ React.createElement("div", { className: "cat-pick-body" }, /* @__PURE__ */ React.createElement("div", { className: "cat-pick-row" }, /* @__PURE__ */ React.createElement("span", { className: "cat-pick-name" }, p.model), /* @__PURE__ */ React.createElement("span", { className: "mono cat-pick-price" }, p.price)), /* @__PURE__ */ React.createElement("div", { className: "cat-pick-tip" }, _ts(p.tipKey)))))), /* @__PURE__ */ React.createElement("div", { className: "cat-glow", "aria-hidden": "true" }));
}
function ChannelBanner() {
  const keys = Object.keys(CHANNEL_EXAMPLES);
  const [active, setActive] = useStateS(keys[0]);
  const example = CHANNEL_EXAMPLES[active];
  return /* @__PURE__ */ React.createElement("section", { className: "channels", id: "channels" }, /* @__PURE__ */ React.createElement(
    SectionHeader,
    {
      kicker: _ts("channels.kicker"),
      title: _ts("channels.title"),
      sub: _ts("channels.sub")
    }
  ), /* @__PURE__ */ React.createElement("div", { className: "ch-toggle" }, keys.map((k) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: k,
      className: `ch-tog-btn ${k === active ? "active" : ""}`,
      onClick: () => setActive(k)
    },
    _ts(CHANNEL_EXAMPLES[k].nameKey)
  ))), /* @__PURE__ */ React.createElement("div", { className: "ch-flow" }, /* @__PURE__ */ React.createElement("div", { className: "ch-node user" }, /* @__PURE__ */ React.createElement("div", { className: "ch-node-icon" }, /* @__PURE__ */ React.createElement("svg", { width: "22", height: "22", viewBox: "0 0 22 22", fill: "none" }, /* @__PURE__ */ React.createElement("circle", { cx: "11", cy: "8", r: "3.5", stroke: "currentColor", strokeWidth: "1.4" }), /* @__PURE__ */ React.createElement("path", { d: "M3 19c1.5-3.5 5-5 8-5s6.5 1.5 8 5", stroke: "currentColor", strokeWidth: "1.4", strokeLinecap: "round" }))), /* @__PURE__ */ React.createElement("div", { className: "ch-node-label" }, _ts("channels.user_request"))), /* @__PURE__ */ React.createElement("div", { className: "ch-line ch-line-1", "aria-hidden": "true" }), /* @__PURE__ */ React.createElement("div", { className: "ch-node prism" }, /* @__PURE__ */ React.createElement("div", { className: "ch-node-icon iridescent-text", style: { fontSize: 20, fontFamily: "var(--font-display)", fontWeight: 700 } }, "P"), /* @__PURE__ */ React.createElement("div", { className: "ch-node-label" }, _ts("channels.router"))), /* @__PURE__ */ React.createElement("div", { className: "ch-arc" }, example.channels.map((ch, i) => /* @__PURE__ */ React.createElement("div", { key: i, className: `ch-card arc-${i + 1}` }, /* @__PURE__ */ React.createElement("div", { className: "ch-card-head" }, /* @__PURE__ */ React.createElement("span", { className: "ch-card-name" }, _ts(ch.nameKey)), /* @__PURE__ */ React.createElement("span", { className: `ch-health h-${ch.health}` }, ch.health)), /* @__PURE__ */ React.createElement("div", { className: "ch-card-meta" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: "meta-k" }, _ts("channels.ex.region_label")), /* @__PURE__ */ React.createElement("span", { className: "meta-v mono" }, ch.region)), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: "meta-k" }, "p50"), /* @__PURE__ */ React.createElement("span", { className: "meta-v mono" }, ch.p50, "ms")), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: "meta-k" }, "weight"), /* @__PURE__ */ React.createElement("span", { className: "meta-v mono" }, ch.weight, "%"))), /* @__PURE__ */ React.createElement("div", { className: "ch-card-policy" }, _ts(ch.policyKey)), /* @__PURE__ */ React.createElement("div", { className: "ch-weight-bar" }, /* @__PURE__ */ React.createElement("div", { className: "ch-weight-fill", style: { width: `${ch.weight}%`, background: "var(--iridescent)" } })))))), /* @__PURE__ */ React.createElement("div", { className: "ch-foot" }, /* @__PURE__ */ React.createElement("span", null, _ts("channels.foot")), /* @__PURE__ */ React.createElement("a", { className: "link-arrow", href: "/quickstart" }, _ts("channels.read_quickstart"))));
}
function NotDoing() {
  return /* @__PURE__ */ React.createElement("section", { className: "not-doing", id: "not-doing" }, /* @__PURE__ */ React.createElement(
    SectionHeader,
    {
      kicker: _ts("notdoing.kicker"),
      title: _ts("notdoing.title"),
      sub: _ts("notdoing.sub")
    }
  ), /* @__PURE__ */ React.createElement("div", { className: "nd-grid" }, NOTDOING_LIST.map((it, i) => /* @__PURE__ */ React.createElement("article", { key: i, className: "nd-card" }, /* @__PURE__ */ React.createElement("div", { className: "nd-cross", "aria-hidden": "true" }, "\u2715"), /* @__PURE__ */ React.createElement("h3", { className: "nd-title display" }, _ts(it.titleKey)), /* @__PURE__ */ React.createElement("p", { className: "nd-body" }, _ts(it.bodyKey))))));
}
function PricingPreview() {
  const [model, setModel] = useStateS(window.PRISM_HERO_MODELS[1]);
  const [tokens, setTokens] = useStateS(1e5);
  const [contactOpen, setContactOpen] = useStateS(false);
  const cost = (tokens / 1e6 * (model.priceIn + model.priceOut * 3)).toFixed(4);
  return /* @__PURE__ */ React.createElement("section", { className: "pricing", id: "pricing" }, /* @__PURE__ */ React.createElement(
    SectionHeader,
    {
      kicker: _ts("pricing.kicker"),
      title: _ts("pricing.title"),
      sub: _ts("pricing.sub")
    }
  ), /* @__PURE__ */ React.createElement("div", { className: "price-grid price-grid-2" }, /* @__PURE__ */ React.createElement(
    PriceCard,
    {
      tier: _ts("pricing.tier.self.tier"),
      featured: true,
      price: _ts("pricing.tier.self.price"),
      tagline: _ts("pricing.tier.self.tagline"),
      features: [
        _ts("pricing.tier.self.f1"),
        _ts("pricing.tier.self.f2"),
        _ts("pricing.tier.self.f3"),
        _ts("pricing.tier.self.f4"),
        _ts("pricing.tier.self.f5")
      ],
      cta: _ts("pricing.tier.self.cta"),
      ctaHref: "/signup"
    }
  ), /* @__PURE__ */ React.createElement(
    PriceCard,
    {
      tier: _ts("pricing.tier.team.tier"),
      price: _ts("pricing.tier.team.price"),
      tagline: _ts("pricing.tier.team.tagline"),
      features: [
        _ts("pricing.tier.team.f1"),
        _ts("pricing.tier.team.f2"),
        _ts("pricing.tier.team.f3"),
        _ts("pricing.tier.team.f4"),
        _ts("pricing.tier.team.f5"),
        _ts("pricing.tier.team.f6")
      ],
      cta: _ts("pricing.tier.team.cta"),
      onClick: () => setContactOpen(true)
    }
  )), contactOpen && /* @__PURE__ */ React.createElement(ContactSalesModal, { onClose: () => setContactOpen(false) }), /* @__PURE__ */ React.createElement("div", { className: "price-calc" }, /* @__PURE__ */ React.createElement("div", { className: "pc-head" }, /* @__PURE__ */ React.createElement("span", { className: "kicker mono" }, _ts("pricing.calc.kicker")), /* @__PURE__ */ React.createElement("h3", { className: "pc-title display" }, _ts("pricing.calc.title"))), /* @__PURE__ */ React.createElement("div", { className: "pc-controls" }, /* @__PURE__ */ React.createElement("label", { className: "pc-field" }, /* @__PURE__ */ React.createElement("span", { className: "pc-label" }, _ts("pricing.calc.model")), /* @__PURE__ */ React.createElement(
    "select",
    {
      className: "pc-input",
      value: model.id,
      onChange: (e) => setModel(window.PRISM_HERO_MODELS.find((m) => m.id === e.target.value))
    },
    window.PRISM_HERO_MODELS.map((m) => /* @__PURE__ */ React.createElement("option", { key: m.id, value: m.id }, m.display))
  )), /* @__PURE__ */ React.createElement("label", { className: "pc-field" }, /* @__PURE__ */ React.createElement("span", { className: "pc-label" }, _ts("pricing.calc.tokens")), /* @__PURE__ */ React.createElement(
    "input",
    {
      className: "pc-input mono",
      type: "number",
      min: "1000",
      step: "10000",
      value: tokens,
      onChange: (e) => setTokens(Math.max(0, parseInt(e.target.value) || 0))
    }
  )), /* @__PURE__ */ React.createElement("div", { className: "pc-result" }, /* @__PURE__ */ React.createElement("div", { className: "pc-result-row" }, /* @__PURE__ */ React.createElement("span", null, _ts("pricing.calc.prism")), /* @__PURE__ */ React.createElement("span", { className: "display pc-num" }, "$", cost)), /* @__PURE__ */ React.createElement("div", { className: "pc-result-row pc-result-secondary" }, /* @__PURE__ */ React.createElement("span", null, _ts("pricing.calc.vs")), /* @__PURE__ */ React.createElement("span", { className: "mono" }, _ts("pricing.calc.match"))))), /* @__PURE__ */ React.createElement("div", { className: "pc-note" }, _ts("pricing.calc.note"))), /* @__PURE__ */ React.createElement(PaymentMethods, null));
}
function PaymentMethods() {
  const [copied, setCopied] = useStateS("");
  const copy = (text, label) => {
    navigator.clipboard?.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(""), 1800);
  };
  const TRC_ADDR = "TT24g41HLptouzxGycZxQKmWaTENK4K4HG";
  const SOL_ADDR = "66p5tnV6Fd7x5QmRE6X772PMVmVUVgozRzATJ4Ns9iQn";
  const EVM_ADDR = "0xC862ff9Fd79D180950E546DBB8b108d5c9c38582";
  return /* @__PURE__ */ React.createElement("div", { className: "pay-row" }, /* @__PURE__ */ React.createElement("div", { className: "pay-head" }, /* @__PURE__ */ React.createElement("span", { className: "kicker mono" }, _ts("pay.kicker")), /* @__PURE__ */ React.createElement("h3", { className: "pay-title display" }, _ts("pay.title")), /* @__PURE__ */ React.createElement("p", { className: "pay-sub mono" }, _ts("pay.sub"))), /* @__PURE__ */ React.createElement("div", { className: "pay-grid" }, /* @__PURE__ */ React.createElement(PayCard, { icon: "alipay", titleKey: "pay.alipay.title", descKey: "pay.alipay.desc", badgeKey: "pay.alipay.badge" }), /* @__PURE__ */ React.createElement(PayCard, { icon: "wechat", titleKey: "pay.wechat.title", descKey: "pay.wechat.desc", badgeKey: "pay.wechat.badge" }), /* @__PURE__ */ React.createElement(PayCard, { icon: "bank", titleKey: "pay.bank.title", descKey: "pay.bank.desc", badgeKey: "pay.bank.badge" }), /* @__PURE__ */ React.createElement("div", { className: "pay-card pay-card-crypto" }, /* @__PURE__ */ React.createElement("div", { className: "pay-card-head" }, /* @__PURE__ */ React.createElement("span", { className: "pay-icon pay-icon-trc" }, "T"), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "pay-card-title" }, "USDC (TRC20)", /* @__PURE__ */ React.createElement("span", { className: "pay-card-pill" }, _ts("pay.usdc.recommended"))), /* @__PURE__ */ React.createElement("div", { className: "pay-card-en mono" }, _ts("pay.usdc.trc.tag")))), /* @__PURE__ */ React.createElement("div", { className: "pay-addr-row" }, /* @__PURE__ */ React.createElement("code", { className: "pay-addr mono", title: TRC_ADDR }, TRC_ADDR), /* @__PURE__ */ React.createElement("button", { className: "pay-copy mono", onClick: () => copy(TRC_ADDR, "trc") }, copied === "trc" ? _ts("pay.copied") : _ts("pay.copy"))), /* @__PURE__ */ React.createElement("div", { className: "pay-warn" }, "\u26A0\uFE0F ", _ts("pay.usdc.trc.warn"))), /* @__PURE__ */ React.createElement("div", { className: "pay-card pay-card-crypto" }, /* @__PURE__ */ React.createElement("div", { className: "pay-card-head" }, /* @__PURE__ */ React.createElement("span", { className: "pay-icon pay-icon-sol" }, "\u25CE"), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "pay-card-title" }, "USDC (Solana)"), /* @__PURE__ */ React.createElement("div", { className: "pay-card-en mono" }, _ts("pay.usdc.sol.tag")))), /* @__PURE__ */ React.createElement("div", { className: "pay-addr-row" }, /* @__PURE__ */ React.createElement("code", { className: "pay-addr mono", title: SOL_ADDR }, SOL_ADDR), /* @__PURE__ */ React.createElement("button", { className: "pay-copy mono", onClick: () => copy(SOL_ADDR, "sol") }, copied === "sol" ? _ts("pay.copied") : _ts("pay.copy"))), /* @__PURE__ */ React.createElement("div", { className: "pay-warn" }, "\u26A0\uFE0F ", _ts("pay.usdc.sol.warn"))), /* @__PURE__ */ React.createElement("div", { className: "pay-card pay-card-crypto" }, /* @__PURE__ */ React.createElement("div", { className: "pay-card-head" }, /* @__PURE__ */ React.createElement("span", { className: "pay-icon pay-icon-evm" }, "\u2B22"), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "pay-card-title" }, "USDC (EVM)"), /* @__PURE__ */ React.createElement("div", { className: "pay-card-en mono" }, _ts("pay.usdc.evm.tag")))), /* @__PURE__ */ React.createElement("div", { className: "pay-addr-row" }, /* @__PURE__ */ React.createElement("code", { className: "pay-addr mono", title: EVM_ADDR }, EVM_ADDR), /* @__PURE__ */ React.createElement("button", { className: "pay-copy mono", onClick: () => copy(EVM_ADDR, "evm") }, copied === "evm" ? _ts("pay.copied") : _ts("pay.copy"))), /* @__PURE__ */ React.createElement("div", { className: "pay-warn" }, _ts("pay.usdc.evm.warn")))), /* @__PURE__ */ React.createElement("div", { className: "pay-foot mono" }, _ts("pay.foot"), /* @__PURE__ */ React.createElement("a", { href: "https://github.com/meiyaobuyao123-hash/AIzhongzhuanzhan/blob/main/docs/payment-methods.md", target: "_blank", rel: "noreferrer" }, _ts("pay.foot.link"))));
}
function PayCard({ icon, titleKey, descKey, badgeKey }) {
  return /* @__PURE__ */ React.createElement("div", { className: "pay-card" }, /* @__PURE__ */ React.createElement("div", { className: "pay-card-head" }, /* @__PURE__ */ React.createElement("span", { className: `pay-icon pay-icon-${icon}` }, icon === "alipay" && "\u652F", icon === "wechat" && "\u5FAE", icon === "bank" && "\u94F6", icon === "stripe" && "S"), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "pay-card-title" }, _ts(titleKey)))), /* @__PURE__ */ React.createElement("div", { className: "pay-card-desc" }, _ts(descKey)), badgeKey && /* @__PURE__ */ React.createElement("div", { className: "pay-badge" }, _ts(badgeKey)));
}
function PriceCard({ tier, price, tagline, features, cta, ctaHref, onClick, featured }) {
  const cls = featured ? "cta-primary" : "cta-ghost";
  return /* @__PURE__ */ React.createElement("article", { className: `price-card ${featured ? "featured" : ""}` }, featured && /* @__PURE__ */ React.createElement("div", { className: "price-ribbon" }, _ts("pricing.recommended")), /* @__PURE__ */ React.createElement("header", { className: "price-head" }, /* @__PURE__ */ React.createElement("div", { className: "price-tier display" }, tier), /* @__PURE__ */ React.createElement("div", { className: "price-cost-eq mono" }, "cost = price"), /* @__PURE__ */ React.createElement("div", { className: "price-amount display" }, price), /* @__PURE__ */ React.createElement("div", { className: "price-tagline" }, tagline)), /* @__PURE__ */ React.createElement("ul", { className: "price-list" }, features.map((f, i) => /* @__PURE__ */ React.createElement("li", { key: i, className: "price-li" }, /* @__PURE__ */ React.createElement(Check, null), f))), onClick ? /* @__PURE__ */ React.createElement(
    "button",
    {
      type: "button",
      className: cls,
      onClick,
      style: { border: "none", cursor: "pointer", font: "inherit" }
    },
    cta,
    " ",
    /* @__PURE__ */ React.createElement(Arrow2, null)
  ) : /* @__PURE__ */ React.createElement("a", { href: ctaHref, className: cls }, cta, " ", /* @__PURE__ */ React.createElement(Arrow2, null)), featured && /* @__PURE__ */ React.createElement("div", { className: "price-glow", "aria-hidden": "true" }));
}
function ContactSalesModal({ onClose }) {
  return /* @__PURE__ */ React.createElement(
    "div",
    {
      className: "cs-modal-overlay",
      onClick: onClose,
      style: {
        position: "fixed",
        inset: 0,
        zIndex: 1e3,
        background: "rgba(0,0,0,0.55)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }
    },
    /* @__PURE__ */ React.createElement(
      "div",
      {
        onClick: (e) => e.stopPropagation(),
        style: {
          background: "#FFFFFF",
          color: "#18181B",
          borderRadius: 14,
          padding: "28px 32px 24px",
          maxWidth: 380,
          width: "90%",
          boxShadow: "0 20px 50px rgba(0,0,0,0.30)",
          fontFamily: "Inter, system-ui, sans-serif",
          textAlign: "center"
        }
      },
      /* @__PURE__ */ React.createElement("h2", { style: { margin: "0 0 6px", fontSize: 20, fontWeight: 600, letterSpacing: "-0.02em" } }, _ts("contact.title")),
      /* @__PURE__ */ React.createElement("p", { style: { margin: "0 0 18px", color: "#71717A", fontSize: 13 } }, _ts("contact.sub")),
      /* @__PURE__ */ React.createElement(
        "img",
        {
          src: "/suanli/qr-wechat-contact.jpg",
          alt: _ts("contact.alt"),
          loading: "lazy",
          decoding: "async",
          style: { width: "100%", maxWidth: 260, borderRadius: 10, display: "block", margin: "0 auto" }
        }
      ),
      /* @__PURE__ */ React.createElement("p", { style: { margin: "14px 0 0", fontSize: 12, color: "#A1A1AA" } }, _ts("contact.signature")),
      /* @__PURE__ */ React.createElement(
        "button",
        {
          onClick: onClose,
          style: {
            marginTop: 18,
            padding: "8px 18px",
            borderRadius: 6,
            background: "#F4F4F5",
            border: "1px solid rgba(0,0,0,0.10)",
            color: "#18181B",
            fontSize: 13,
            cursor: "pointer",
            fontFamily: "inherit"
          }
        },
        _ts("contact.close")
      )
    )
  );
}
function FAQ() {
  const [open, setOpen] = useStateS(0);
  return /* @__PURE__ */ React.createElement("section", { className: "faq", id: "faq" }, /* @__PURE__ */ React.createElement(
    SectionHeader,
    {
      kicker: _ts("faq.kicker"),
      title: _ts("faq.title"),
      sub: _ts("faq.sub")
    }
  ), /* @__PURE__ */ React.createElement("div", { className: "faq-list" }, FAQ_LIST.map((it, i) => /* @__PURE__ */ React.createElement("div", { key: i, className: `faq-item ${i === open ? "open" : ""}` }, /* @__PURE__ */ React.createElement("button", { className: "faq-q", onClick: () => setOpen((o) => o === i ? -1 : i) }, /* @__PURE__ */ React.createElement("span", { className: "faq-q-text" }, _ts(it.qKey)), /* @__PURE__ */ React.createElement("span", { className: "faq-q-icon", "aria-hidden": "true" }, i === open ? "\u2212" : "+")), /* @__PURE__ */ React.createElement("div", { className: "faq-a" }, /* @__PURE__ */ React.createElement("p", null, _ts(it.aKey)))))));
}
function FinalCTA() {
  return /* @__PURE__ */ React.createElement("section", { className: "final-cta", id: "signup" }, /* @__PURE__ */ React.createElement("div", { className: "fcta-card" }, /* @__PURE__ */ React.createElement("div", { className: "fcta-eyebrow mono" }, _ts("fcta.eyebrow")), /* @__PURE__ */ React.createElement("h2", { className: "fcta-title display" }, _ts("fcta.title")), /* @__PURE__ */ React.createElement("p", { className: "fcta-sub" }, _ts("fcta.sub")), /* @__PURE__ */ React.createElement("div", { className: "fcta-row" }, /* @__PURE__ */ React.createElement("a", { className: "cta-primary", href: "/signup" }, _ts("fcta.cta1"), " ", /* @__PURE__ */ React.createElement(Arrow2, null)), /* @__PURE__ */ React.createElement("a", { className: "cta-ghost", href: "/quickstart" }, _ts("fcta.cta2"))), /* @__PURE__ */ React.createElement("div", { className: "fcta-glow", "aria-hidden": "true" })));
}
function Footer() {
  return /* @__PURE__ */ React.createElement("footer", { className: "footer" }, /* @__PURE__ */ React.createElement("div", { className: "footer-inner" }, /* @__PURE__ */ React.createElement("div", { className: "footer-brand" }, /* @__PURE__ */ React.createElement(Logo, null), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "footer-brand-name display" }, "Prism"), /* @__PURE__ */ React.createElement("div", { className: "footer-brand-tag" }, _ts("footer.tag")))), /* @__PURE__ */ React.createElement("nav", { className: "footer-cols" }, /* @__PURE__ */ React.createElement(FCol, { titleKey: "footer.product", items: [
    { labelKey: "nav.pricing", href: "#pricing" },
    { labelKey: "nav.console", href: "/console" },
    { labelKey: "nav.login", href: "/login" },
    { labelKey: "nav.signup", href: "/signup" }
  ] }), /* @__PURE__ */ React.createElement(FCol, { titleKey: "footer.dev", items: [
    { labelKey: "console.api_docs", href: "/api-docs" },
    { labelKey: "console.quickstart", href: "/quickstart" },
    { labelKey: "clients.kicker", href: "#clients" }
  ] }), /* @__PURE__ */ React.createElement(FCol, { titleKey: "footer.company", items: [
    { labelKey: "contact.title", href: "#pricing" }
  ] }))), /* @__PURE__ */ React.createElement("div", { className: "footer-bottom mono" }, /* @__PURE__ */ React.createElement("span", null, "\xA9 2026 Prism Gateway"), /* @__PURE__ */ React.createElement("span", { className: "dot" }, "\xB7"), /* @__PURE__ */ React.createElement("span", null, "cost = price \xB7 always"), /* @__PURE__ */ React.createElement("span", { className: "dot" }, "\xB7"), /* @__PURE__ */ React.createElement("span", null, _ts("footer.icp"))));
}
function FCol({ titleKey, items }) {
  return /* @__PURE__ */ React.createElement("div", { className: "fcol" }, /* @__PURE__ */ React.createElement("div", { className: "fcol-title mono" }, _ts(titleKey)), /* @__PURE__ */ React.createElement("ul", null, items.map((it, i) => /* @__PURE__ */ React.createElement("li", { key: i }, /* @__PURE__ */ React.createElement("a", { href: it.href }, _ts(it.labelKey))))));
}
function SectionHeader({ kicker, title, sub }) {
  return /* @__PURE__ */ React.createElement("header", { className: "sec-head" }, kicker && /* @__PURE__ */ React.createElement("div", { className: "kicker mono" }, kicker), /* @__PURE__ */ React.createElement("h2", { className: "sec-title display" }, title), sub && /* @__PURE__ */ React.createElement("p", { className: "sec-sub mono" }, sub));
}
function Logo({ size = 28 }) {
  return /* @__PURE__ */ React.createElement("svg", { width: size, height: size, viewBox: "0 0 32 32", style: { display: "block" } }, /* @__PURE__ */ React.createElement("defs", null, /* @__PURE__ */ React.createElement("linearGradient", { id: "lg-grad", x1: "0", y1: "0", x2: "1", y2: "1" }, /* @__PURE__ */ React.createElement("stop", { offset: "0%", stopColor: "#8B5CF6" }), /* @__PURE__ */ React.createElement("stop", { offset: "35%", stopColor: "#06B6D4" }), /* @__PURE__ */ React.createElement("stop", { offset: "70%", stopColor: "#EC4899" }), /* @__PURE__ */ React.createElement("stop", { offset: "100%", stopColor: "#F59E0B" }))), /* @__PURE__ */ React.createElement("path", { d: "M 16 4 L 28 26 L 4 26 Z", stroke: "url(#lg-grad)", strokeWidth: "1.5", fill: "none", strokeLinejoin: "round" }), /* @__PURE__ */ React.createElement("path", { d: "M 1 16 L 11 16", stroke: "rgba(255,255,255,0.6)", strokeWidth: "1", strokeLinecap: "round" }), /* @__PURE__ */ React.createElement("path", { d: "M 22 18 L 31 14", stroke: "#8B5CF6", strokeWidth: "1", strokeLinecap: "round" }), /* @__PURE__ */ React.createElement("path", { d: "M 22 19 L 31 18", stroke: "#06B6D4", strokeWidth: "1", strokeLinecap: "round" }), /* @__PURE__ */ React.createElement("path", { d: "M 22 20 L 31 22", stroke: "#EC4899", strokeWidth: "1", strokeLinecap: "round" }), /* @__PURE__ */ React.createElement("path", { d: "M 22 21 L 31 26", stroke: "#F59E0B", strokeWidth: "1", strokeLinecap: "round" }));
}
function Check() {
  return /* @__PURE__ */ React.createElement("svg", { width: "14", height: "14", viewBox: "0 0 14 14", fill: "none", "aria-hidden": "true" }, /* @__PURE__ */ React.createElement("path", { d: "M3 7.5l3 3 5-7", stroke: "url(#fi-grad)", strokeWidth: "1.6", strokeLinecap: "round", strokeLinejoin: "round" }));
}
function Arrow2() {
  return /* @__PURE__ */ React.createElement("svg", { width: "14", height: "14", viewBox: "0 0 14 14", fill: "none", "aria-hidden": "true" }, /* @__PURE__ */ React.createElement("path", { d: "M2 7h8m-3-3 3 3-3 3", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }));
}
