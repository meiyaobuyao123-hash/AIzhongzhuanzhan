/* Hero section: 3D prism + live model swap demo
   - Pure CSS/SVG prism (no Three.js — keeps the page light)
   - Click any model pill → code "model=" string animates in, price/p50 ticker updates
*/

const { useState: useStateHero, useEffect: useEffectHero, useMemo: useMemoHero } = React;

function HeroSection() {
  const models = window.PRISM_HERO_MODELS;
  const [selected, setSelected] = useStateHero(models[0]);
  const [animKey, setAnimKey] = useStateHero(0);

  function pickModel(m) {
    if (m.id === selected.id) return;
    setSelected(m);
    setAnimKey(k => k + 1);
  }

  return (
    <section className="hero">
      <div className="hero-inner">
        <div className="hero-copy">
          <h1 className="hero-title">
            <span>成本透明，</span>
            <span className="accent">0 加价</span>
            <span>。</span>
          </h1>
          <p className="hero-sub">
            200+ 模型，一个 OpenAI 兼容 API。价目表写在你看得见的地方。
          </p>
          <p className="hero-sub-en mono">cost = price. always.</p>

          <div className="hero-cta-row">
            <a href="#signup" className="cta-primary">
              <span>立即开始</span>
              <span className="cta-aside">充 1 万到账 9995</span>
              <Arrow />
            </a>
            <a href="#models" className="cta-ghost">查看模型与价格</a>
          </div>

          <div className="hero-trust-mini">
            <span>0% 加价 · 万 5 手续费</span>
            <span className="dot">·</span>
            <span>支付宝 / 微信 / 对公</span>
            <span className="dot">·</span>
            <span>OpenAI 协议直接兼容</span>
          </div>
        </div>

        <div className="hero-stage">
          <PrismVisual />
          <div className="model-swap-card">
            <div className="msc-pills">
              {models.map(m => (
                <button
                  key={m.id}
                  className={`msc-pill ${m.id === selected.id ? 'active' : ''}`}
                  onClick={() => pickModel(m)}
                  title={m.id}
                >
                  {m.display}
                </button>
              ))}
            </div>

            <CodeWindow model={selected} animKey={animKey} />

            <div className="msc-stats" key={animKey}>
              <Stat label="输入价" en="input"  value={`$${selected.priceIn}`}  unit=" / 1M tokens" />
              <Stat label="输出价" en="output" value={`$${selected.priceOut}`} unit=" / 1M tokens" />
              <Stat label="p50"    en="latency" value={`${selected.p50}ms`} />
              <Stat label="上下文" en="context" value={selected.ctx} />
            </div>

            <p className="msc-caption">
              <span className="msc-arrow">↑</span>
              <span>点击任一模型，代码里的 <code>model</code> 字段会变；其他什么都不用动。</span>
            </p>
          </div>
        </div>
      </div>

      <ProviderMarquee />
    </section>
  );
}

/* ─── 3D-ish CSS prism + dispersed spectrum ─────────────────────── */

function PrismVisual() {
  return (
    <div className="prism-stage" aria-hidden="true">
      <div className="prism-orbit">
        <div className="prism-glass">
          <svg viewBox="0 0 200 200" className="prism-svg">
            <defs>
              <linearGradient id="pg-face" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%"  stopColor="rgba(139,92,246,0.55)"/>
                <stop offset="50%" stopColor="rgba(6,182,212,0.45)"/>
                <stop offset="100%" stopColor="rgba(236,72,153,0.55)"/>
              </linearGradient>
              <linearGradient id="pg-edge" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%"  stopColor="#a78bfa"/>
                <stop offset="50%" stopColor="#67e8f9"/>
                <stop offset="100%" stopColor="#f472b6"/>
              </linearGradient>
            </defs>
            <polygon
              points="100,30 175,160 25,160"
              fill="url(#pg-face)"
              stroke="url(#pg-edge)"
              strokeWidth="1.5"
              strokeLinejoin="round"
            />
            <polygon
              points="100,30 175,160 25,160"
              fill="none"
              stroke="rgba(255,255,255,0.5)"
              strokeWidth="0.8"
              strokeLinejoin="round"
              opacity="0.6"
            />
          </svg>
        </div>

        {/* incoming ray */}
        <div className="prism-incoming" />

        {/* dispersed rays */}
        <div className="prism-ray r1" />
        <div className="prism-ray r2" />
        <div className="prism-ray r3" />
        <div className="prism-ray r4" />
        <div className="prism-ray r5" />
        <div className="prism-ray r6" />
        <div className="prism-ray r7" />
      </div>

      <div className="prism-glow" />
    </div>
  );
}

/* ─── Code block window with animated model= line ───────────────── */

function CodeWindow({ model, animKey }) {
  return (
    <div className="code-window">
      <div className="cw-chrome">
        <span className="cw-dot d1" />
        <span className="cw-dot d2" />
        <span className="cw-dot d3" />
        <span className="cw-title mono">openai-python · streaming</span>
      </div>
      <pre className="code-body mono">
{`from openai import OpenAI

client = OpenAI(
    base_url="https://api.prism.ai/v1",
    api_key="sk-prism-…",
)

resp = client.chat.completions.create(
    model=`}<span className="cw-highlight" key={animKey}>"{model.id}"</span>{`,
    messages=[{"role":"user","content":"Hello"}],
    stream=True,
)`}
      </pre>
    </div>
  );
}

/* ─── Stat tile in the demo widget ──────────────────────────────── */

function Stat({ label, en, value, unit }) {
  return (
    <div className="stat-tile">
      <div className="stat-k">
        <span>{label}</span>
        <span className="mono stat-en">{en}</span>
      </div>
      <div className="stat-v">
        <span>{value}</span>
        {unit && <span className="stat-unit">{unit}</span>}
      </div>
    </div>
  );
}

/* ─── Provider marquee ──────────────────────────────────────────── */

function ProviderMarquee() {
  const items = [...window.PRISM_PROVIDERS_MARQUEE, ...window.PRISM_PROVIDERS_MARQUEE];
  return (
    <div className="provider-marquee" aria-hidden="true">
      <div className="pm-track">
        {items.map((name, i) => (
          <span key={i} className="pm-chip">
            <ProviderGlyph name={name} />
            <span>{name}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function ProviderGlyph({ name }) {
  const initial = name[0];
  // Hash the name to a hue so each provider has a stable color tint
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  const hue = h % 360;
  return (
    <span
      className="pm-glyph"
      style={{
        background: `linear-gradient(135deg, hsla(${hue}, 70%, 60%, 0.5), hsla(${(hue + 60) % 360}, 70%, 60%, 0.5))`,
        borderColor: `hsla(${hue}, 70%, 60%, 0.4)`,
      }}
    >
      {initial}
    </span>
  );
}

function Arrow() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
      <path d="M2 6h7m-3-3 3 3-3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
