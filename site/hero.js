const { useState: useStateHero, useEffect: useEffectHero, useMemo: useMemoHero } = React;
const _t = window.t;
function HeroSection() {
  const models = window.PRISM_HERO_MODELS;
  const [selected, setSelected] = useStateHero(models[0]);
  const [animKey, setAnimKey] = useStateHero(0);
  function pickModel(m) {
    if (m.id === selected.id) return;
    setSelected(m);
    setAnimKey((k) => k + 1);
  }
  return /* @__PURE__ */ React.createElement("section", { className: "hero" }, /* @__PURE__ */ React.createElement("div", { className: "hero-inner" }, /* @__PURE__ */ React.createElement("div", { className: "hero-copy" }, /* @__PURE__ */ React.createElement("h1", { className: "hero-title" }, /* @__PURE__ */ React.createElement("span", null, _t("hero.title.1")), /* @__PURE__ */ React.createElement("span", { className: "accent" }, _t("hero.title.accent")), /* @__PURE__ */ React.createElement("span", null, _t("hero.title.2"))), /* @__PURE__ */ React.createElement("p", { className: "hero-sub" }, _t("hero.sub")), /* @__PURE__ */ React.createElement("p", { className: "hero-sub-en mono" }, "cost = price. always."), /* @__PURE__ */ React.createElement("div", { className: "hero-cta-row" }, /* @__PURE__ */ React.createElement("a", { href: "/signup", className: "cta-primary" }, /* @__PURE__ */ React.createElement("span", null, _t("hero.cta_primary")), /* @__PURE__ */ React.createElement("span", { className: "cta-aside" }, _t("hero.cta_aside")), /* @__PURE__ */ React.createElement(Arrow, null)), /* @__PURE__ */ React.createElement("a", { href: "/quickstart", className: "cta-ghost" }, _t("hero.cta_ghost"))), /* @__PURE__ */ React.createElement("div", { className: "hero-trust-mini" }, /* @__PURE__ */ React.createElement("span", null, _t("hero.trust.1")), /* @__PURE__ */ React.createElement("span", { className: "dot" }, "\xB7"), /* @__PURE__ */ React.createElement("span", null, _t("hero.trust.2")), /* @__PURE__ */ React.createElement("span", { className: "dot" }, "\xB7"), /* @__PURE__ */ React.createElement("span", null, _t("hero.trust.3")))), /* @__PURE__ */ React.createElement("div", { className: "hero-stage" }, /* @__PURE__ */ React.createElement(PrismVisual, null), /* @__PURE__ */ React.createElement("div", { className: "model-swap-card" }, /* @__PURE__ */ React.createElement("div", { className: "msc-pills" }, models.map((m) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: m.id,
      className: `msc-pill ${m.id === selected.id ? "active" : ""}`,
      onClick: () => pickModel(m),
      title: m.id
    },
    m.display
  ))), /* @__PURE__ */ React.createElement(CodeWindow, { model: selected, animKey }), /* @__PURE__ */ React.createElement("div", { className: "msc-stats", key: animKey }, /* @__PURE__ */ React.createElement(Stat, { labelKey: "hero.stat.input", value: `$${selected.priceIn}`, unit: _t("hero.unit_per_million") }), /* @__PURE__ */ React.createElement(Stat, { labelKey: "hero.stat.output", value: `$${selected.priceOut}`, unit: _t("hero.unit_per_million") }), /* @__PURE__ */ React.createElement(Stat, { labelKey: "hero.stat.latency", value: `${selected.p50}ms` }), /* @__PURE__ */ React.createElement(Stat, { labelKey: "hero.stat.context", value: selected.ctx })), /* @__PURE__ */ React.createElement("p", { className: "msc-caption" }, /* @__PURE__ */ React.createElement("span", { className: "msc-arrow" }, "\u2191"), /* @__PURE__ */ React.createElement("span", null, _t("hero.caption")))))), /* @__PURE__ */ React.createElement(ProviderMarquee, null));
}
function PrismVisual() {
  return /* @__PURE__ */ React.createElement("div", { className: "prism-stage", "aria-hidden": "true" }, /* @__PURE__ */ React.createElement("div", { className: "prism-orbit" }, /* @__PURE__ */ React.createElement("div", { className: "prism-glass" }, /* @__PURE__ */ React.createElement("svg", { viewBox: "0 0 200 200", className: "prism-svg" }, /* @__PURE__ */ React.createElement("defs", null, /* @__PURE__ */ React.createElement("linearGradient", { id: "pg-face", x1: "0", y1: "0", x2: "1", y2: "1" }, /* @__PURE__ */ React.createElement("stop", { offset: "0%", stopColor: "rgba(139,92,246,0.55)" }), /* @__PURE__ */ React.createElement("stop", { offset: "50%", stopColor: "rgba(6,182,212,0.45)" }), /* @__PURE__ */ React.createElement("stop", { offset: "100%", stopColor: "rgba(236,72,153,0.55)" })), /* @__PURE__ */ React.createElement("linearGradient", { id: "pg-edge", x1: "0", y1: "0", x2: "1", y2: "0" }, /* @__PURE__ */ React.createElement("stop", { offset: "0%", stopColor: "#a78bfa" }), /* @__PURE__ */ React.createElement("stop", { offset: "50%", stopColor: "#67e8f9" }), /* @__PURE__ */ React.createElement("stop", { offset: "100%", stopColor: "#f472b6" }))), /* @__PURE__ */ React.createElement(
    "polygon",
    {
      points: "100,30 175,160 25,160",
      fill: "url(#pg-face)",
      stroke: "url(#pg-edge)",
      strokeWidth: "1.5",
      strokeLinejoin: "round"
    }
  ), /* @__PURE__ */ React.createElement(
    "polygon",
    {
      points: "100,30 175,160 25,160",
      fill: "none",
      stroke: "rgba(255,255,255,0.5)",
      strokeWidth: "0.8",
      strokeLinejoin: "round",
      opacity: "0.6"
    }
  ))), /* @__PURE__ */ React.createElement("div", { className: "prism-incoming" }), /* @__PURE__ */ React.createElement("div", { className: "prism-ray r1" }), /* @__PURE__ */ React.createElement("div", { className: "prism-ray r2" }), /* @__PURE__ */ React.createElement("div", { className: "prism-ray r3" }), /* @__PURE__ */ React.createElement("div", { className: "prism-ray r4" }), /* @__PURE__ */ React.createElement("div", { className: "prism-ray r5" }), /* @__PURE__ */ React.createElement("div", { className: "prism-ray r6" }), /* @__PURE__ */ React.createElement("div", { className: "prism-ray r7" })), /* @__PURE__ */ React.createElement("div", { className: "prism-glow" }));
}
function CodeWindow({ model, animKey }) {
  return /* @__PURE__ */ React.createElement("div", { className: "code-window" }, /* @__PURE__ */ React.createElement("div", { className: "cw-chrome" }, /* @__PURE__ */ React.createElement("span", { className: "cw-dot d1" }), /* @__PURE__ */ React.createElement("span", { className: "cw-dot d2" }), /* @__PURE__ */ React.createElement("span", { className: "cw-dot d3" }), /* @__PURE__ */ React.createElement("span", { className: "cw-title mono" }, "openai-python \xB7 streaming")), /* @__PURE__ */ React.createElement("pre", { className: "code-body mono" }, `from openai import OpenAI

client = OpenAI(
    base_url="https://www.ai100trading.cn/suanli-api/v1",
    api_key="sk-prism-\u2026",
)

resp = client.chat.completions.create(
    model=`, /* @__PURE__ */ React.createElement("span", { className: "cw-highlight", key: animKey }, '"', model.id, '"'), `,
    messages=[{"role":"user","content":"Hello"}],
    stream=True,
)`));
}
function Stat({ labelKey, value, unit }) {
  return /* @__PURE__ */ React.createElement("div", { className: "stat-tile" }, /* @__PURE__ */ React.createElement("div", { className: "stat-k" }, /* @__PURE__ */ React.createElement("span", null, _t(labelKey))), /* @__PURE__ */ React.createElement("div", { className: "stat-v" }, /* @__PURE__ */ React.createElement("span", null, value), unit && /* @__PURE__ */ React.createElement("span", { className: "stat-unit" }, unit)));
}
function ProviderMarquee() {
  const items = [...window.PRISM_PROVIDERS_MARQUEE, ...window.PRISM_PROVIDERS_MARQUEE];
  return /* @__PURE__ */ React.createElement("div", { className: "provider-marquee", "aria-hidden": "true" }, /* @__PURE__ */ React.createElement("div", { className: "pm-track" }, items.map((name, i) => /* @__PURE__ */ React.createElement("span", { key: i, className: "pm-chip" }, /* @__PURE__ */ React.createElement(ProviderGlyph, { name }), /* @__PURE__ */ React.createElement("span", null, name)))));
}
function ProviderGlyph({ name }) {
  const initial = name[0];
  let h = 0;
  for (let i = 0; i < name.length; i++) h = h * 31 + name.charCodeAt(i) >>> 0;
  const hue = h % 360;
  return /* @__PURE__ */ React.createElement(
    "span",
    {
      className: "pm-glyph",
      style: {
        background: `linear-gradient(135deg, hsla(${hue}, 70%, 60%, 0.5), hsla(${(hue + 60) % 360}, 70%, 60%, 0.5))`,
        borderColor: `hsla(${hue}, 70%, 60%, 0.4)`
      }
    },
    initial
  );
}
function Arrow() {
  return /* @__PURE__ */ React.createElement("svg", { width: "12", height: "12", viewBox: "0 0 12 12", fill: "none", "aria-hidden": "true" }, /* @__PURE__ */ React.createElement("path", { d: "M2 6h7m-3-3 3 3-3 3", stroke: "currentColor", strokeWidth: "1.4", strokeLinecap: "round", strokeLinejoin: "round" }));
}
