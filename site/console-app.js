const { useState, useEffect, useCallback } = React;
const t = window.t;
function ConsoleLangPicker() {
  const supported = window.PRISM_I18N_SUPPORTED;
  const current = window.LANG;
  return /* @__PURE__ */ React.createElement(
    "select",
    {
      className: "lang-picker mono",
      value: current,
      onChange: (e) => window.setLang(e.target.value),
      title: t("nav.lang_label"),
      "aria-label": t("nav.lang_label"),
      style: { marginRight: 12 }
    },
    supported.map((c) => /* @__PURE__ */ React.createElement("option", { key: c, value: c }, t("lang." + c)))
  );
}
const ICON_PATHS = {
  // Nav icons
  home: '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
  key: '<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>',
  chart: '<path d="M3 3v18h18"/><path d="M7 16l4-4 4 4 5-5"/>',
  wallet: '<path d="M21 12V7a2 2 0 0 0-2-2H5a2 2 0 0 0 0 4h16v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><circle cx="17" cy="14" r="1.5"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
  // Metric icons
  zap: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
  arrowDown: '<line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>',
  arrowUp: '<line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>',
  dollar: '<line x1="12" y1="2" x2="12" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
  // Misc
  book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
  copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  x: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  check: '<polyline points="20 6 9 17 4 12"/>',
  chevronDown: '<polyline points="6 9 12 15 18 9"/>',
  chevronRight: '<polyline points="9 18 15 12 9 6"/>',
  // Pay icons (for USDC cards — geometric shapes)
  diamond: '<rect x="3" y="11" width="18" height="11" rx="2"/><circle cx="12" cy="16" r="1"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  hexagon: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>',
  circle: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/>'
};
function Icon({ name, size = 16, className = "", color }) {
  const path = ICON_PATHS[name];
  if (!path) return null;
  return /* @__PURE__ */ React.createElement(
    "svg",
    {
      className: `cs-icon ${className}`,
      width: size,
      height: size,
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: color || "currentColor",
      strokeWidth: "1.75",
      strokeLinecap: "round",
      strokeLinejoin: "round",
      dangerouslySetInnerHTML: { __html: path }
    }
  );
}
const TABS = [
  { id: "overview", labelKey: "console.tab.overview", icon: "home" },
  { id: "keys", labelKey: "console.tab.keys", icon: "key" },
  { id: "usage", labelKey: "console.tab.usage", icon: "chart" },
  { id: "billing", labelKey: "console.tab.billing", icon: "wallet" },
  { id: "settings", labelKey: "console.tab.settings", icon: "settings" }
];
function getTabFromHash() {
  const h = (location.hash || "").replace(/^#/, "");
  return TABS.find((t2) => t2.id === h)?.id || "overview";
}
function fmtUSD(n) {
  if (typeof n !== "number") return "-";
  return "$" + n.toFixed(4);
}
function fmtCompact(n) {
  if (n === void 0 || n === null) return "-";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return String(n);
}
function ConsoleApp() {
  const [tab, setTab] = useState(getTabFromHash());
  const [me, setMe] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const onHash = () => setTab(getTabFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  useEffect(() => {
    if (!PrismAPI.isLoggedIn()) {
      location.href = "/login?next=" + encodeURIComponent("/console");
      return;
    }
    PrismAPI.get("/account/me").then(setMe).catch((err) => setError(err.message));
  }, []);
  async function logout() {
    try {
      await PrismAPI.post("/auth/logout", {});
    } catch {
    }
    PrismAPI.clearToken();
    location.href = "/login";
  }
  if (error) return /* @__PURE__ */ React.createElement("div", { className: "cs-main" }, /* @__PURE__ */ React.createElement("div", { className: "auth-error" }, error));
  if (!me) return /* @__PURE__ */ React.createElement("div", { className: "cs-main" }, /* @__PURE__ */ React.createElement("div", { className: "cs-empty" }, t("console.loading")));
  return /* @__PURE__ */ React.createElement("div", { className: "cs-shell" }, /* @__PURE__ */ React.createElement("aside", { className: "cs-sidebar" }, /* @__PURE__ */ React.createElement("a", { href: "/suanli/", className: "cs-brand cs-brand-link", title: t("console.brand_back") }, /* @__PURE__ */ React.createElement("span", { className: "cs-brand-mark" }, "P"), /* @__PURE__ */ React.createElement("span", { className: "cs-brand-name" }, "Prism")), TABS.map((tt) => /* @__PURE__ */ React.createElement(
    "a",
    {
      key: tt.id,
      href: `#${tt.id}`,
      className: `cs-nav-link ${tab === tt.id ? "active" : ""}`
    },
    /* @__PURE__ */ React.createElement(Icon, { name: tt.icon }),
    /* @__PURE__ */ React.createElement("span", null, t(tt.labelKey))
  )), /* @__PURE__ */ React.createElement("div", { style: { height: 12 } }), /* @__PURE__ */ React.createElement(
    "a",
    {
      href: "/api-docs",
      target: "_blank",
      rel: "noreferrer",
      className: "cs-nav-link cs-nav-external",
      title: t("console.api_docs_tip")
    },
    /* @__PURE__ */ React.createElement(Icon, { name: "book" }),
    /* @__PURE__ */ React.createElement("span", null, t("console.api_docs")),
    /* @__PURE__ */ React.createElement(Icon, { name: "arrowUp", size: 11, className: "cs-icon-ext" })
  ), /* @__PURE__ */ React.createElement(
    "a",
    {
      href: "/quickstart",
      target: "_blank",
      rel: "noreferrer",
      className: "cs-nav-link cs-nav-external",
      title: t("console.quickstart_tip")
    },
    /* @__PURE__ */ React.createElement(Icon, { name: "zap" }),
    /* @__PURE__ */ React.createElement("span", null, t("console.quickstart")),
    /* @__PURE__ */ React.createElement(Icon, { name: "arrowUp", size: 11, className: "cs-icon-ext" })
  ), /* @__PURE__ */ React.createElement("div", { className: "cs-nav-foot" }, me.email, /* @__PURE__ */ React.createElement("br", null), /* @__PURE__ */ React.createElement("span", { className: "mono", style: { fontSize: 11, color: "var(--text-muted)" } }, t("console.tier"), ": ", me.tier), /* @__PURE__ */ React.createElement("button", { className: "cs-logout", onClick: logout }, t("console.logout")))), /* @__PURE__ */ React.createElement("main", { className: "cs-main" }, /* @__PURE__ */ React.createElement("div", { className: "cs-page-header" }, /* @__PURE__ */ React.createElement("h1", null, t(TABS.find((tt) => tt.id === tab).labelKey)), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "center", flexWrap: "wrap" } }, /* @__PURE__ */ React.createElement(ConsoleLangPicker, null), /* @__PURE__ */ React.createElement("div", { className: "cs-balance-pill" }, /* @__PURE__ */ React.createElement("span", { style: { display: "inline-flex", gap: 12, alignItems: "center" } }, /* @__PURE__ */ React.createElement("span", { title: t("console.bal.usd_tip") }, /* @__PURE__ */ React.createElement("span", { style: { color: "var(--text-muted)", fontSize: 11, marginRight: 4 } }, "USD"), /* @__PURE__ */ React.createElement("strong", null, fmtUSD(me.balance_usd))), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--text-faint)", fontSize: 11 } }, "\xB7"), /* @__PURE__ */ React.createElement("span", { title: t("console.bal.cny_tip") }, /* @__PURE__ */ React.createElement("span", { style: { color: "var(--text-muted)", fontSize: 11, marginRight: 4 } }, "CNY"), /* @__PURE__ */ React.createElement("strong", null, "\xA5", (me.balance_cny ?? 0).toFixed(2)))), /* @__PURE__ */ React.createElement("a", { href: "#billing", className: "cs-btn cs-btn-primary", style: { padding: "4px 12px" } }, t("console.topup_btn"))))), tab === "overview" && /* @__PURE__ */ React.createElement(Overview, { me }), tab === "keys" && /* @__PURE__ */ React.createElement(Keys, { me }), tab === "usage" && /* @__PURE__ */ React.createElement(Usage, { me }), tab === "billing" && /* @__PURE__ */ React.createElement(Billing, { me }), tab === "settings" && /* @__PURE__ */ React.createElement(Settings, { me, setMe })), /* @__PURE__ */ React.createElement(MobileBottomTabBar, { tab }));
}
function MobileBottomTabBar({ tab }) {
  return /* @__PURE__ */ React.createElement("nav", { className: "cs-bottom-nav", "aria-label": "Primary" }, /* @__PURE__ */ React.createElement("div", { className: "cs-bottom-nav-inner" }, TABS.map((tt) => /* @__PURE__ */ React.createElement(
    "a",
    {
      key: tt.id,
      href: `#${tt.id}`,
      className: `cs-bottom-tab ${tab === tt.id ? "active" : ""}`
    },
    /* @__PURE__ */ React.createElement(Icon, { name: tt.icon, size: 20 }),
    /* @__PURE__ */ React.createElement("span", null, t(tt.labelKey))
  ))));
}
function Overview({ me }) {
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);
  useEffect(() => {
    PrismAPI.get("/usage/stats?group_by=day").then(setStats).catch(() => {
    });
    PrismAPI.get("/usage/requests?size=10").then((d) => setRecent(d.data || [])).catch(() => {
    });
  }, []);
  const totalCost = stats?.summary?.total_cost_usd ?? 0;
  const totalRequests = stats?.summary?.total_requests ?? 0;
  return /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", { className: "cs-metrics" }, /* @__PURE__ */ React.createElement(
    Metric,
    {
      label: t("console.metric.usd_wallet"),
      value: fmtUSD(me.balance_usd),
      meta: t("console.metric.usd_meta", { usd: fmtUSD(me.total_topped_up_usd) }),
      icon: "dollar",
      accent: "green"
    }
  ), /* @__PURE__ */ React.createElement(
    Metric,
    {
      label: t("console.metric.cny_wallet"),
      value: `\xA5${(me.balance_cny ?? 0).toFixed(2)}`,
      meta: t("console.metric.cny_meta", { cny: `\xA5${(me.total_topped_up_cny ?? 0).toFixed(2)}` }),
      icon: "zap",
      accent: "magenta"
    }
  ), /* @__PURE__ */ React.createElement(Metric, { label: t("console.metric.month_calls"), value: fmtCompact(totalRequests), meta: t("console.metric.month_calls_meta") }), /* @__PURE__ */ React.createElement(Metric, { label: t("console.metric.month_cost"), value: fmtUSD(totalCost), meta: t("console.metric.month_cost_meta") })), /* @__PURE__ */ React.createElement("section", { className: "cs-section" }, /* @__PURE__ */ React.createElement("h2", null, t("console.recent.title")), recent.length === 0 ? /* @__PURE__ */ React.createElement("div", { className: "cs-empty" }, t("console.recent.empty")) : /* @__PURE__ */ React.createElement("table", { className: "cs-table" }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", null, t("console.col.time")), /* @__PURE__ */ React.createElement("th", null, t("console.col.model")), /* @__PURE__ */ React.createElement("th", null, t("console.col.status")), /* @__PURE__ */ React.createElement("th", null, t("console.col.tokens")), /* @__PURE__ */ React.createElement("th", null, t("console.col.cost")), /* @__PURE__ */ React.createElement("th", null, t("console.col.latency")), /* @__PURE__ */ React.createElement("th", null, t("console.col.detail")))), /* @__PURE__ */ React.createElement("tbody", null, recent.map((r) => /* @__PURE__ */ React.createElement("tr", { key: r.request_id }, /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("console.col.time") }, r.created_at?.slice(11, 19)), /* @__PURE__ */ React.createElement("td", { "data-label": t("console.col.model") }, r.model_id), /* @__PURE__ */ React.createElement("td", { "data-label": t("console.col.status") }, /* @__PURE__ */ React.createElement(StatusPill, { status: r.status })), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("console.col.tokens") }, r.tokens.prompt, " / ", r.tokens.completion), /* @__PURE__ */ React.createElement("td", { "data-label": t("console.col.cost") }, fmtUSD(r.cost_usd)), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("console.col.latency") }, r.latency_ms, "ms"), /* @__PURE__ */ React.createElement("td", { "data-label": t("console.col.detail") }, /* @__PURE__ */ React.createElement("a", { href: `#usage/${r.request_id}`, className: "cs-btn", style: { padding: "4px 10px" } }, t("console.view")))))))));
}
function Metric({ label, value, meta, icon, accent }) {
  const accentClass = accent ? `cs-metric-${accent}` : "";
  return /* @__PURE__ */ React.createElement("div", { className: `cs-metric ${accentClass}` }, /* @__PURE__ */ React.createElement("div", { className: "cs-metric-head" }, icon && /* @__PURE__ */ React.createElement("span", { className: "cs-metric-icon" }, typeof icon === "string" ? /* @__PURE__ */ React.createElement(Icon, { name: icon, size: 15 }) : icon), /* @__PURE__ */ React.createElement("div", { className: "cs-metric-label" }, label)), /* @__PURE__ */ React.createElement("div", { className: "cs-metric-value" }, value), meta && /* @__PURE__ */ React.createElement("div", { className: "cs-metric-meta" }, meta));
}
function StatusPill({ status }) {
  const cls = status === "ok" ? "cs-pill-ok" : status === "partial" ? "cs-pill-warn" : "cs-pill-err";
  return /* @__PURE__ */ React.createElement("span", { className: `cs-pill ${cls}` }, status);
}
function modelFamily(modelId) {
  const m = (modelId || "").toLowerCase();
  if (m.startsWith("claude")) return "anthropic";
  if (m.startsWith("gpt-") || m.startsWith("o1") || m.startsWith("o3") || m.startsWith("o4") || m.startsWith("o5")) return "openai";
  if (m.startsWith("doubao")) return "doubao";
  if (m.startsWith("deepseek")) return "deepseek";
  if (m.startsWith("minimax") || m.startsWith("abab")) return "minimax";
  if (m.startsWith("gemini")) return "google";
  if (m.startsWith("glm")) return "glm";
  if (m.startsWith("qwen")) return "qwen";
  if (m.startsWith("kimi")) return "kimi";
  return "other";
}
function ProviderBadge({ modelId }) {
  const fam = modelFamily(modelId);
  const labels = {
    anthropic: "Claude",
    openai: "OpenAI",
    doubao: "Doubao",
    deepseek: "DeepSeek",
    minimax: "MiniMax",
    google: "Gemini",
    glm: "GLM",
    qwen: "Qwen",
    kimi: "Kimi",
    other: "\xB7"
  };
  return /* @__PURE__ */ React.createElement("span", { className: `cs-fam cs-fam-${fam}`, title: modelId }, labels[fam]);
}
function ModelCell({ modelId }) {
  return /* @__PURE__ */ React.createElement("span", { className: "cs-model-cell" }, /* @__PURE__ */ React.createElement(ProviderBadge, { modelId }), /* @__PURE__ */ React.createElement("span", { className: "mono cs-model-id" }, modelId));
}
function Keys() {
  const [keys, setKeys] = useState(null);
  const [creating, setCreating] = useState(false);
  const [createdKey, setCreatedKey] = useState(null);
  const refresh = useCallback(() => {
    PrismAPI.get("/account/api-keys").then((d) => setKeys(d.data || [])).catch(() => {
    });
  }, []);
  useEffect(refresh, [refresh]);
  async function createKey(name, rpm) {
    const data = await PrismAPI.post("/account/api-keys", { name, rate_limit_rpm: rpm });
    setCreatedKey(data);
    setCreating(false);
    refresh();
  }
  async function revoke(id) {
    if (!confirm(t("console.keys.confirm_revoke"))) return;
    await PrismAPI.delete(`/account/api-keys/${id}`);
    refresh();
  }
  return /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", { className: "cs-row-between", style: { marginBottom: 16 } }, /* @__PURE__ */ React.createElement("p", { style: { color: "var(--text-muted)", fontSize: 13, margin: 0 } }, t("console.keys.intro")), /* @__PURE__ */ React.createElement("button", { className: "cs-btn cs-btn-primary", onClick: () => setCreating(true) }, t("keys.create_btn"))), keys && keys.length === 0 ? /* @__PURE__ */ React.createElement("div", { className: "cs-empty" }, t("console.keys.empty")) : keys && /* @__PURE__ */ React.createElement("table", { className: "cs-table" }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", null, t("console.col.name")), /* @__PURE__ */ React.createElement("th", null, t("console.keys.col.prefix")), /* @__PURE__ */ React.createElement("th", null, t("console.keys.col.rpm")), /* @__PURE__ */ React.createElement("th", null, t("console.col.status")), /* @__PURE__ */ React.createElement("th", null, t("console.keys.col.last_used")), /* @__PURE__ */ React.createElement("th", null, t("console.col.actions")))), /* @__PURE__ */ React.createElement("tbody", null, keys.map((k) => /* @__PURE__ */ React.createElement("tr", { key: k.id }, /* @__PURE__ */ React.createElement("td", { "data-label": t("console.col.name") }, k.name || "-"), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("console.keys.col.prefix") }, k.prefix, "\u2026", k.last4), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("console.keys.col.rpm") }, k.rate_limit_rpm || t("console.keys.rpm_default")), /* @__PURE__ */ React.createElement("td", { "data-label": t("console.col.status") }, k.enabled ? /* @__PURE__ */ React.createElement("span", { className: "cs-pill cs-pill-ok" }, "enabled") : /* @__PURE__ */ React.createElement("span", { className: "cs-pill cs-pill-err" }, "revoked")), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("console.keys.col.last_used"), style: { fontSize: 11, color: "var(--text-muted)" } }, k.last_used_at?.slice(0, 19) || t("console.keys.never_used")), /* @__PURE__ */ React.createElement("td", { "data-label": t("console.col.actions") }, k.enabled && /* @__PURE__ */ React.createElement("button", { className: "cs-btn cs-btn-danger", onClick: () => revoke(k.id) }, t("keys.revoke"))))))), creating && /* @__PURE__ */ React.createElement(CreateKeyModal, { onClose: () => setCreating(false), onCreate: createKey }), createdKey && /* @__PURE__ */ React.createElement(CreatedKeyModal, { data: createdKey, onClose: () => setCreatedKey(null) }));
}
function CreateKeyModal({ onClose, onCreate }) {
  const [name, setName] = useState("");
  const [rpm, setRpm] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit() {
    setBusy(true);
    try {
      await onCreate(name || null, rpm ? parseInt(rpm) : null);
    } finally {
      setBusy(false);
    }
  }
  return /* @__PURE__ */ React.createElement("div", { className: "cs-modal-overlay", onClick: onClose }, /* @__PURE__ */ React.createElement("div", { className: "cs-modal", onClick: (e) => e.stopPropagation() }, /* @__PURE__ */ React.createElement("h3", null, t("keys.modal_title")), /* @__PURE__ */ React.createElement("div", { style: { marginBottom: 12 } }, /* @__PURE__ */ React.createElement("label", { className: "auth-label" }, t("keys.name_label")), /* @__PURE__ */ React.createElement(
    "input",
    {
      className: "auth-input",
      value: name,
      onChange: (e) => setName(e.target.value),
      placeholder: t("console.keys.modal.name_ph"),
      style: { width: "100%", boxSizing: "border-box" }
    }
  )), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "auth-label" }, t("console.keys.modal.rpm_label")), /* @__PURE__ */ React.createElement(
    "input",
    {
      className: "auth-input",
      type: "number",
      min: 1,
      value: rpm,
      onChange: (e) => setRpm(e.target.value),
      placeholder: "600",
      style: { width: "100%", boxSizing: "border-box" }
    }
  )), /* @__PURE__ */ React.createElement("div", { className: "cs-modal-actions" }, /* @__PURE__ */ React.createElement("button", { className: "cs-btn", onClick: onClose, disabled: busy }, t("keys.cancel")), /* @__PURE__ */ React.createElement("button", { className: "cs-btn cs-btn-primary", onClick: submit, disabled: busy }, busy ? t("console.keys.modal.creating") : t("keys.create")))));
}
function CreatedKeyModal({ data, onClose }) {
  const [copied, setCopied] = useState(false);
  function copy() {
    navigator.clipboard?.writeText(data.key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2e3);
  }
  return /* @__PURE__ */ React.createElement("div", { className: "cs-modal-overlay" }, /* @__PURE__ */ React.createElement("div", { className: "cs-modal" }, /* @__PURE__ */ React.createElement("h3", null, t("console.keys.created.title")), /* @__PURE__ */ React.createElement(
    "p",
    {
      style: { color: "var(--text-muted)", fontSize: 13 },
      dangerouslySetInnerHTML: { __html: t("console.keys.created.body") }
    }
  ), /* @__PURE__ */ React.createElement("div", { className: "cs-key-display" }, /* @__PURE__ */ React.createElement("span", { style: { flex: 1 } }, data.key), /* @__PURE__ */ React.createElement("button", { className: "cs-btn", onClick: copy }, copied ? t("console.keys.created.copied") : t("keys.copy"))), /* @__PURE__ */ React.createElement("p", { style: { color: "var(--text-muted)", fontSize: 12, fontFamily: "var(--font-mono)" } }, "# Claude Code:", /* @__PURE__ */ React.createElement("br", null), "export ANTHROPIC_BASE_URL=https://www.ai100trading.cn/suanli-api", /* @__PURE__ */ React.createElement("br", null), "export ANTHROPIC_AUTH_TOKEN=", data.key.slice(0, 14), "\u2026", /* @__PURE__ */ React.createElement("br", null), /* @__PURE__ */ React.createElement("br", null), "# OpenAI SDK / Cursor:", /* @__PURE__ */ React.createElement("br", null), "base_url=https://www.ai100trading.cn/suanli-api/v1", /* @__PURE__ */ React.createElement("br", null), "api_key=", data.key.slice(0, 14), "\u2026"), /* @__PURE__ */ React.createElement("div", { className: "cs-modal-actions" }, /* @__PURE__ */ React.createElement("button", { className: "cs-btn cs-btn-primary", onClick: onClose }, t("console.keys.created.saved")))));
}
function Usage() {
  const today = /* @__PURE__ */ new Date();
  const todayStr = today.toISOString().slice(0, 10);
  const weekAgo = new Date(today.getTime() - 7 * 864e5).toISOString().slice(0, 10);
  const [filters, setFilters] = useState({
    since: weekAgo,
    until: todayStr,
    model: "",
    status: ""
  });
  const [groupBy, setGroupBy] = useState("model");
  const [expanded, setExpanded] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [stats, setStats] = useState(null);
  const [requests, setRequests] = useState({ data: [], total: 0, pages: 0 });
  const [models, setModels] = useState([]);
  const [detail, setDetail] = useState(null);
  const [loadingPage, setLoadingPage] = useState(false);
  const buildParams = (extra = {}) => {
    const p = new URLSearchParams();
    if (filters.since) p.set("since", (/* @__PURE__ */ new Date(filters.since + "T00:00:00Z")).toISOString());
    if (filters.until) p.set("until", (/* @__PURE__ */ new Date(filters.until + "T23:59:59Z")).toISOString());
    if (filters.model) p.set("model", filters.model);
    if (filters.status) p.set("status", filters.status);
    Object.entries(extra).forEach(([k, v]) => p.set(k, v));
    return p.toString();
  };
  useEffect(() => {
    PrismAPI.get(`/usage/stats?${buildParams({ group_by: groupBy })}`).then(setStats).catch(() => {
    });
  }, [groupBy, filters.since, filters.until, filters.model, filters.status]);
  useEffect(() => {
    setLoadingPage(true);
    PrismAPI.get(`/usage/requests?${buildParams({ page, size: pageSize })}`).then(setRequests).catch(() => setRequests({ data: [], total: 0, pages: 0 })).finally(() => setLoadingPage(false));
  }, [page, pageSize, filters.since, filters.until, filters.model, filters.status]);
  useEffect(() => {
    PrismAPI.get("/usage/models").then((d) => setModels(d.data || [])).catch(() => {
    });
  }, []);
  useEffect(() => {
    setPage(1);
  }, [filters.since, filters.until, filters.model, filters.status]);
  useEffect(() => {
    const handler = () => {
      const m = location.hash.match(/^#usage\/([\w-]+)$/);
      if (m) PrismAPI.get(`/usage/requests/${m[1]}`).then(setDetail);
      else setDetail(null);
    };
    handler();
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);
  const summary = stats?.summary || {};
  const aggData = stats?.data || [];
  const total = requests.total || 0;
  const pages = requests.pages || 0;
  const fromN = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const toN = Math.min(page * pageSize, total);
  return /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", { className: "cs-filter-bar" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "cs-filter-label" }, t("usage.filter.since")), /* @__PURE__ */ React.createElement(
    "input",
    {
      className: "cs-input cs-input-date",
      type: "date",
      value: filters.since,
      onChange: (e) => setFilters({ ...filters, since: e.target.value })
    }
  )), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "cs-filter-label" }, t("usage.filter.until")), /* @__PURE__ */ React.createElement(
    "input",
    {
      className: "cs-input cs-input-date",
      type: "date",
      value: filters.until,
      onChange: (e) => setFilters({ ...filters, until: e.target.value })
    }
  )), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "cs-filter-label" }, t("usage.filter.model")), /* @__PURE__ */ React.createElement(
    "select",
    {
      className: "cs-input",
      value: filters.model,
      onChange: (e) => setFilters({ ...filters, model: e.target.value })
    },
    /* @__PURE__ */ React.createElement("option", { value: "" }, t("usage.filter.all_models")),
    models.map((m) => /* @__PURE__ */ React.createElement("option", { key: m.model_id, value: m.model_id }, m.model_id, " (", m.requests, ")"))
  )), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("label", { className: "cs-filter-label" }, t("usage.filter.status")), /* @__PURE__ */ React.createElement(
    "select",
    {
      className: "cs-input",
      value: filters.status,
      onChange: (e) => setFilters({ ...filters, status: e.target.value })
    },
    /* @__PURE__ */ React.createElement("option", { value: "" }, t("usage.filter.all_status")),
    /* @__PURE__ */ React.createElement("option", { value: "ok" }, "ok"),
    /* @__PURE__ */ React.createElement("option", { value: "error" }, "error"),
    /* @__PURE__ */ React.createElement("option", { value: "partial" }, "partial"),
    /* @__PURE__ */ React.createElement("option", { value: "cancelled" }, "cancelled")
  )), /* @__PURE__ */ React.createElement("div", { style: { alignSelf: "flex-end" } }, /* @__PURE__ */ React.createElement(
    "button",
    {
      className: "cs-btn",
      onClick: () => setFilters({ since: weekAgo, until: todayStr, model: "", status: "" })
    },
    t("usage.filter.reset")
  ))), /* @__PURE__ */ React.createElement("div", { className: "cs-summary-cards" }, /* @__PURE__ */ React.createElement(
    Metric,
    {
      label: t("usage.summary.requests"),
      value: fmtCompact(summary.total_requests || 0),
      meta: t("usage.summary.range"),
      icon: "zap",
      accent: "cyan"
    }
  ), /* @__PURE__ */ React.createElement(
    Metric,
    {
      label: t("usage.summary.input"),
      value: fmtCompact(summary.total_input_tokens || 0),
      icon: "arrowDown",
      accent: "purple"
    }
  ), /* @__PURE__ */ React.createElement(
    Metric,
    {
      label: t("usage.summary.output"),
      value: fmtCompact(summary.total_output_tokens || 0),
      icon: "arrowUp",
      accent: "magenta"
    }
  ), /* @__PURE__ */ React.createElement(
    Metric,
    {
      label: t("usage.summary.cost"),
      value: fmtUSD(summary.total_cost_usd || 0),
      meta: t("usage.summary.zeromarkup"),
      icon: "dollar",
      accent: "green"
    }
  )), /* @__PURE__ */ React.createElement("section", { className: "cs-section" }, /* @__PURE__ */ React.createElement("div", { className: "cs-section-head" }, /* @__PURE__ */ React.createElement("h2", null, t("usage.agg.title")), /* @__PURE__ */ React.createElement("div", { className: "cs-row", style: { gap: 6 } }, /* @__PURE__ */ React.createElement("span", { style: { fontSize: 12, color: "var(--text-muted)", marginRight: 6 } }, t("usage.agg.group_label")), [
    { id: "model", labelKey: "usage.agg.by_model" },
    { id: "channel", labelKey: "usage.agg.by_channel" },
    { id: "day", labelKey: "usage.agg.by_day" },
    { id: "key", labelKey: "usage.agg.by_key" }
  ].map((g) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: g.id,
      className: `cs-btn ${groupBy === g.id ? "cs-btn-primary" : ""}`,
      onClick: () => {
        setGroupBy(g.id);
        setExpanded(null);
      },
      style: { fontSize: 12, padding: "6px 12px" }
    },
    t(g.labelKey)
  )))), aggData.length === 0 ? /* @__PURE__ */ React.createElement("div", { className: "cs-empty" }, t("usage.agg.empty")) : /* @__PURE__ */ React.createElement("table", { className: "cs-table" }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", null, groupByLabel(groupBy)), /* @__PURE__ */ React.createElement("th", null, t("usage.agg.col.requests")), /* @__PURE__ */ React.createElement("th", null, t("usage.agg.col.input")), /* @__PURE__ */ React.createElement("th", null, t("usage.agg.col.output")), /* @__PURE__ */ React.createElement("th", null, t("usage.agg.col.cost")), /* @__PURE__ */ React.createElement("th", null, t("usage.agg.col.avg_lat")))), /* @__PURE__ */ React.createElement("tbody", null, aggData.map((r, i) => {
    const isChannel = groupBy === "channel";
    const childKey = parseInt(r.bucket || "0", 10);
    const isOpen = isChannel && expanded === childKey;
    const expandable = isChannel && (r.models || []).length > 0;
    const display = isChannel ? r.channel_name ? `${r.channel_name} (#${r.bucket})` : t("usage.agg.unrouted") : r.bucket || "-";
    return /* @__PURE__ */ React.createElement(React.Fragment, { key: i }, /* @__PURE__ */ React.createElement(
      "tr",
      {
        className: expandable ? "cs-row-expandable" : "",
        onClick: expandable ? () => setExpanded(isOpen ? null : childKey) : void 0,
        style: expandable ? { cursor: "pointer" } : void 0
      },
      /* @__PURE__ */ React.createElement("td", { "data-label": groupByLabel(groupBy) }, expandable && /* @__PURE__ */ React.createElement("span", { style: { display: "inline-block", width: 14, color: "var(--text-muted)" } }, isOpen ? "\u25BE" : "\u25B8"), groupBy === "model" ? /* @__PURE__ */ React.createElement(ModelCell, { modelId: display }) : /* @__PURE__ */ React.createElement("span", { className: "mono" }, display)),
      /* @__PURE__ */ React.createElement("td", { "data-label": t("usage.agg.col.requests") }, fmtCompact(r.requests)),
      /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("usage.agg.col.input") }, fmtCompact(r.input_tokens)),
      /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("usage.agg.col.output") }, fmtCompact(r.output_tokens)),
      /* @__PURE__ */ React.createElement("td", { "data-label": t("usage.agg.col.cost") }, fmtUSD(r.cost_usd)),
      /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("usage.agg.col.avg_lat") }, r.avg_latency_ms ? r.avg_latency_ms + "ms" : "-")
    ), isOpen && (r.models || []).map((m) => /* @__PURE__ */ React.createElement("tr", { key: `${i}:${m.model_id}`, className: "cs-row-child" }, /* @__PURE__ */ React.createElement("td", { "data-label": groupByLabel(groupBy), style: { paddingLeft: 36 } }, /* @__PURE__ */ React.createElement("span", { style: { color: "var(--text-muted)", marginRight: 6 } }, "\u21B3"), /* @__PURE__ */ React.createElement(ModelCell, { modelId: m.model_id })), /* @__PURE__ */ React.createElement("td", { "data-label": t("usage.agg.col.requests") }, fmtCompact(m.requests)), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("usage.agg.col.input") }, fmtCompact(m.input_tokens)), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("usage.agg.col.output") }, fmtCompact(m.output_tokens)), /* @__PURE__ */ React.createElement("td", { "data-label": t("usage.agg.col.cost") }, fmtUSD(m.cost_usd)), /* @__PURE__ */ React.createElement("td", { "data-label": t("usage.agg.col.avg_lat") }, "\u2014"))));
  })))), /* @__PURE__ */ React.createElement("section", { className: "cs-section" }, /* @__PURE__ */ React.createElement("div", { className: "cs-section-head" }, /* @__PURE__ */ React.createElement("h2", null, t("usage.detail.title")), /* @__PURE__ */ React.createElement("div", { className: "cs-page-ctrl" }, /* @__PURE__ */ React.createElement("span", { className: "mono cs-page-info" }, total === 0 ? t("usage.detail.zero") : t("usage.detail.range", { from: fromN, to: toN, total })), /* @__PURE__ */ React.createElement(
    "select",
    {
      className: "cs-input",
      value: pageSize,
      onChange: (e) => {
        setPageSize(Number(e.target.value));
        setPage(1);
      },
      style: { width: 110 }
    },
    /* @__PURE__ */ React.createElement("option", { value: 25 }, t("usage.detail.per_page", { n: 25 })),
    /* @__PURE__ */ React.createElement("option", { value: 50 }, t("usage.detail.per_page", { n: 50 })),
    /* @__PURE__ */ React.createElement("option", { value: 100 }, t("usage.detail.per_page", { n: 100 }))
  ), /* @__PURE__ */ React.createElement(
    "button",
    {
      className: "cs-btn",
      disabled: page <= 1 || loadingPage,
      onClick: () => setPage((p) => Math.max(1, p - 1))
    },
    t("usage.detail.prev")
  ), /* @__PURE__ */ React.createElement("span", { className: "mono cs-page-info" }, pages > 0 ? `${page} / ${pages}` : "-"), /* @__PURE__ */ React.createElement(
    "button",
    {
      className: "cs-btn",
      disabled: page >= pages || loadingPage,
      onClick: () => setPage((p) => Math.min(pages, p + 1))
    },
    t("usage.detail.next")
  ))), requests.data.length === 0 ? /* @__PURE__ */ React.createElement("div", { className: "cs-empty" }, t("usage.detail.empty")) : /* @__PURE__ */ React.createElement("table", { className: "cs-table" }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", null, t("console.col.time")), /* @__PURE__ */ React.createElement("th", null, t("console.col.model")), /* @__PURE__ */ React.createElement("th", null, t("console.col.status")), /* @__PURE__ */ React.createElement("th", null, t("usage.detail.col.input")), /* @__PURE__ */ React.createElement("th", null, t("usage.detail.col.output")), /* @__PURE__ */ React.createElement("th", null, t("console.col.latency")), /* @__PURE__ */ React.createElement("th", null, t("console.col.cost")), /* @__PURE__ */ React.createElement("th", null, t("console.col.detail")))), /* @__PURE__ */ React.createElement("tbody", null, requests.data.map((r) => /* @__PURE__ */ React.createElement("tr", { key: r.request_id }, /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("console.col.time"), style: { fontSize: 11 } }, r.created_at?.slice(0, 19).replace("T", " ")), /* @__PURE__ */ React.createElement("td", { "data-label": t("console.col.model") }, /* @__PURE__ */ React.createElement(ModelCell, { modelId: r.model_id })), /* @__PURE__ */ React.createElement("td", { "data-label": t("console.col.status") }, /* @__PURE__ */ React.createElement(StatusPill, { status: r.status })), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("usage.detail.col.input") }, fmtCompact(r.tokens.prompt)), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("usage.detail.col.output") }, fmtCompact(r.tokens.completion)), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("console.col.latency") }, r.latency_ms ? r.latency_ms + "ms" : "-"), /* @__PURE__ */ React.createElement("td", { "data-label": t("console.col.cost") }, fmtUSD(r.cost_usd)), /* @__PURE__ */ React.createElement("td", { "data-label": t("console.col.detail") }, /* @__PURE__ */ React.createElement("a", { href: `#usage/${r.request_id}`, className: "cs-btn", style: { padding: "4px 10px" } }, t("console.view")))))))), detail && /* @__PURE__ */ React.createElement(RequestDetailModal, { d: detail, onClose: () => location.hash = "#usage" }));
}
function groupByLabel(g) {
  return {
    model: t("usage.agg.label.model"),
    channel: t("usage.agg.label.channel"),
    day: t("usage.agg.label.day"),
    key: t("usage.agg.label.key")
  }[g] || g;
}
function RequestDetailModal({ d, onClose }) {
  const ch = d.routing?.served_by_channel;
  return /* @__PURE__ */ React.createElement("div", { className: "cs-modal-overlay", onClick: onClose }, /* @__PURE__ */ React.createElement("div", { className: "cs-modal", onClick: (e) => e.stopPropagation(), style: { minWidth: 600 } }, /* @__PURE__ */ React.createElement("h3", null, t("usage.modal.title")), /* @__PURE__ */ React.createElement("div", { style: { display: "grid", gridTemplateColumns: "auto 1fr", gap: "8px 14px", fontSize: 13 } }, /* @__PURE__ */ React.createElement("span", { style: { color: "var(--text-muted)" } }, t("usage.modal.req_id")), /* @__PURE__ */ React.createElement("span", { className: "mono" }, d.request_id), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--text-muted)" } }, t("console.col.model")), /* @__PURE__ */ React.createElement("span", null, d.model_id), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--text-muted)" } }, t("console.col.status")), /* @__PURE__ */ React.createElement("span", null, /* @__PURE__ */ React.createElement(StatusPill, { status: d.status })), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--text-muted)" } }, t("console.col.time")), /* @__PURE__ */ React.createElement("span", { className: "mono" }, d.created_at), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--text-muted)" } }, t("usage.modal.streaming")), /* @__PURE__ */ React.createElement("span", null, d.is_streaming ? t("usage.modal.yes") : t("usage.modal.no"))), /* @__PURE__ */ React.createElement("h4", { style: { margin: "20px 0 10px", fontFamily: "var(--font-display)" } }, t("usage.modal.channel_section")), ch ? /* @__PURE__ */ React.createElement("div", { className: "cs-channel-card" }, /* @__PURE__ */ React.createElement("div", { className: "cs-channel-name" }, ch.name), /* @__PURE__ */ React.createElement("div", { className: "cs-channel-meta" }, /* @__PURE__ */ React.createElement("span", null, "provider: ", /* @__PURE__ */ React.createElement("strong", null, ch.provider)), ch.region && /* @__PURE__ */ React.createElement("span", null, "region: ", /* @__PURE__ */ React.createElement("strong", null, ch.region))), /* @__PURE__ */ React.createElement("div", { className: "cs-channel-meta" }, /* @__PURE__ */ React.createElement("span", null, ch.policy.no_training ? t("usage.modal.no_training") : t("usage.modal.may_train")), /* @__PURE__ */ React.createElement("span", null, t("usage.modal.log_retention", { days: ch.policy.log_retention_days || "?" })))) : /* @__PURE__ */ React.createElement("div", { className: "cs-empty", style: { padding: 20 } }, t("usage.modal.no_upstream")), d.routing?.tried_channels?.length > 1 && /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("h4", { style: { margin: "20px 0 10px", fontFamily: "var(--font-display)" } }, t("usage.modal.retry_history")), /* @__PURE__ */ React.createElement("table", { className: "cs-table" }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", null, t("usage.modal.col.order")), /* @__PURE__ */ React.createElement("th", null, "Channel ID"), /* @__PURE__ */ React.createElement("th", null, t("usage.modal.col.http")), /* @__PURE__ */ React.createElement("th", null, t("usage.modal.col.result")))), /* @__PURE__ */ React.createElement("tbody", null, d.routing.tried_channels.map((tc, i) => /* @__PURE__ */ React.createElement("tr", { key: i }, /* @__PURE__ */ React.createElement("td", { "data-label": t("usage.modal.col.order") }, i + 1), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": "Channel ID" }, tc.channel_id), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("usage.modal.col.http") }, tc.status || "-"), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("usage.modal.col.result"), style: { fontSize: 11 } }, tc.error?.slice(0, 80) || "ok")))))), /* @__PURE__ */ React.createElement("h4", { style: { margin: "20px 0 10px", fontFamily: "var(--font-display)" } }, t("usage.modal.tok_section")), /* @__PURE__ */ React.createElement("table", { className: "cs-table cs-table-kv" }, /* @__PURE__ */ React.createElement("tbody", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", null, "Input (prompt)"), /* @__PURE__ */ React.createElement("td", { className: "mono" }, d.tokens.prompt.toLocaleString())), /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", null, "Output (completion)"), /* @__PURE__ */ React.createElement("td", { className: "mono" }, d.tokens.completion.toLocaleString())), d.tokens.cache_read > 0 && /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", null, "Cache read"), /* @__PURE__ */ React.createElement("td", { className: "mono" }, d.tokens.cache_read.toLocaleString())), d.tokens.cache_write > 0 && /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", null, "Cache write"), /* @__PURE__ */ React.createElement("td", { className: "mono" }, d.tokens.cache_write.toLocaleString())), d.tokens.reasoning > 0 && /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", null, "Reasoning"), /* @__PURE__ */ React.createElement("td", { className: "mono" }, d.tokens.reasoning.toLocaleString())), /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", null, /* @__PURE__ */ React.createElement("strong", null, t("usage.modal.cost_label"))), /* @__PURE__ */ React.createElement("td", { className: "mono" }, /* @__PURE__ */ React.createElement("strong", null, fmtUSD(d.cost_usd)))))), d.error_message && /* @__PURE__ */ React.createElement("div", { className: "auth-error", style: { marginTop: 16 } }, d.error_message), /* @__PURE__ */ React.createElement("div", { className: "cs-modal-actions" }, /* @__PURE__ */ React.createElement("button", { className: "cs-btn", onClick: onClose }, t("usage.modal.close")))));
}
const USDT_CHANNELS = [
  {
    key: "usdt-trc20",
    title: "USDC (TRC20)",
    enKey: "pay.usdc.trc.tag",
    noteKey: "pay.usdc.trc.warn",
    icon: "diamond",
    accent: "#2775CA"
  },
  {
    key: "usdt-sol",
    title: "USDC (Solana)",
    enKey: "pay.usdc.sol.tag",
    noteKey: "pay.usdc.sol.warn",
    icon: "circle",
    accent: "#2775CA"
  },
  {
    key: "usdt-evm",
    title: "USDC (EVM)",
    enKey: "pay.usdc.evm.tag",
    noteKey: "pay.usdc.evm.warn",
    icon: "hexagon",
    accent: "#2775CA"
  }
];
function Billing({ me }) {
  const [topups, setTopups] = useState([]);
  const [activeIntent, setActiveIntent] = useState(null);
  const [loadingChannel, setLoadingChannel] = useState(null);
  const refresh = useCallback(() => {
    PrismAPI.get("/account/topups").then((d) => setTopups(d.data || [])).catch(() => {
    });
  }, []);
  useEffect(() => {
    refresh();
  }, [refresh]);
  async function startUSDT(channel, amount_usd) {
    setLoadingChannel(channel);
    try {
      const data = await PrismAPI.post("/account/topup-intent", { channel, amount_usd });
      setActiveIntent(data);
      refresh();
    } catch (err) {
      alert(t("billing.usdt.create_failed") + (err.message || ""));
    } finally {
      setLoadingChannel(null);
    }
  }
  return /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", { className: "cs-metrics" }, /* @__PURE__ */ React.createElement(
    Metric,
    {
      label: t("console.metric.usd_wallet"),
      value: fmtUSD(me.balance_usd),
      meta: t("console.metric.usd_meta", { usd: fmtUSD(me.total_topped_up_usd) }).split(" \xB7 ")[0],
      icon: "dollar",
      accent: "green"
    }
  ), /* @__PURE__ */ React.createElement(
    Metric,
    {
      label: t("console.metric.cny_wallet"),
      value: `\xA5${(me.balance_cny ?? 0).toFixed(2)}`,
      meta: t("console.metric.cny_meta", { cny: `\xA5${(me.total_topped_up_cny ?? 0).toFixed(2)}` }).split(" \xB7 ")[0],
      icon: "zap",
      accent: "magenta"
    }
  ), /* @__PURE__ */ React.createElement(Metric, { label: t("billing.metric.fee"), value: "1.5%", meta: "cost = price" }), /* @__PURE__ */ React.createElement(
    Metric,
    {
      label: t("billing.metric.fx"),
      value: "6.5 / 7.0",
      meta: t("billing.metric.fx_meta")
    }
  )), /* @__PURE__ */ React.createElement("section", { className: "cs-section" }, /* @__PURE__ */ React.createElement("h2", null, t("billing.usd.title")), /* @__PURE__ */ React.createElement("p", { style: { color: "var(--text-muted)", fontSize: 13, marginBottom: 16 } }, t("billing.usd.intro")), /* @__PURE__ */ React.createElement("div", { className: "cs-pay-grid" }, USDT_CHANNELS.map((ch) => /* @__PURE__ */ React.createElement(
    UsdtCard,
    {
      key: ch.key,
      channel: ch,
      onStart: (amt) => startUSDT(ch.key, amt),
      loading: loadingChannel === ch.key
    }
  )))), /* @__PURE__ */ React.createElement("section", { className: "cs-section" }, /* @__PURE__ */ React.createElement("h2", null, t("billing.cny.title")), /* @__PURE__ */ React.createElement("p", { style: { color: "var(--text-muted)", fontSize: 13, marginBottom: 16 } }, t("billing.cny.intro", { email: me.email, ops: "ops@ai100trading.cn" })), /* @__PURE__ */ React.createElement("div", { className: "cs-pay-grid" }, /* @__PURE__ */ React.createElement(
    DomesticPayCard,
    {
      titleKey: "pay.alipay.title",
      en: t("billing.alipay.label"),
      qrUrl: "/suanli/qr-alipay.jpg",
      tone: "alipay"
    }
  ), /* @__PURE__ */ React.createElement(
    DomesticPayCard,
    {
      titleKey: "pay.wechat.title",
      en: t("billing.wechat.label"),
      qrUrl: "/suanli/qr-wechat.jpg",
      tone: "wechat"
    }
  ))), /* @__PURE__ */ React.createElement("section", { className: "cs-section" }, /* @__PURE__ */ React.createElement("h2", null, t("billing.history.title")), topups.length === 0 ? /* @__PURE__ */ React.createElement("div", { className: "cs-empty" }, t("billing.history.empty")) : /* @__PURE__ */ React.createElement("table", { className: "cs-table" }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", null, t("console.col.time")), /* @__PURE__ */ React.createElement("th", null, t("billing.history.col.channel")), /* @__PURE__ */ React.createElement("th", null, t("billing.history.col.amount")), /* @__PURE__ */ React.createElement("th", null, t("billing.history.col.fee")), /* @__PURE__ */ React.createElement("th", null, t("billing.history.col.credited")), /* @__PURE__ */ React.createElement("th", null, t("console.col.status")), /* @__PURE__ */ React.createElement("th", null, "memo"), /* @__PURE__ */ React.createElement("th", null, t("billing.history.col.tx")))), /* @__PURE__ */ React.createElement("tbody", null, topups.map((tu) => /* @__PURE__ */ React.createElement("tr", { key: tu.id }, /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("console.col.time"), style: { fontSize: 11 } }, tu.created_at?.slice(0, 19)), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("billing.history.col.channel") }, tu.channel), /* @__PURE__ */ React.createElement("td", { "data-label": t("billing.history.col.amount") }, fmtUSD(tu.amount_usd)), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("billing.history.col.fee") }, fmtUSD(tu.fee_usd)), /* @__PURE__ */ React.createElement("td", { "data-label": t("billing.history.col.credited") }, fmtUSD(tu.credited_usd)), /* @__PURE__ */ React.createElement("td", { "data-label": t("console.col.status") }, /* @__PURE__ */ React.createElement(StatusPill, { status: tu.status === "paid" ? "ok" : tu.status })), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": "memo", style: { fontSize: 11 } }, tu.memo || "-"), /* @__PURE__ */ React.createElement("td", { className: "mono", "data-label": t("billing.history.col.tx"), style: { fontSize: 11 } }, tu.external_ref?.slice(0, 14) || "-")))))), activeIntent && /* @__PURE__ */ React.createElement(
    UsdtIntentModal,
    {
      intent: activeIntent,
      onClose: () => {
        setActiveIntent(null);
        refresh();
      },
      onPaid: () => {
        setActiveIntent(null);
        refresh();
      }
    }
  ));
}
function UsdtCard({ channel, onStart, loading }) {
  const [amount, setAmount] = useState(50);
  const fee = (amount * 0.015).toFixed(2);
  const credited = (amount - amount * 0.015).toFixed(2);
  return /* @__PURE__ */ React.createElement("div", { className: "cs-pay-card", style: { borderColor: channel.accent + "40" } }, /* @__PURE__ */ React.createElement("div", { className: "cs-pay-card-head" }, /* @__PURE__ */ React.createElement("span", { className: "cs-pay-icon", style: {
    background: channel.accent + "14",
    color: channel.accent,
    borderColor: channel.accent + "33"
  } }, /* @__PURE__ */ React.createElement(Icon, { name: channel.icon, size: 20 })), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "cs-pay-card-title" }, channel.title), /* @__PURE__ */ React.createElement("div", { className: "cs-pay-card-en mono" }, t(channel.enKey)))), /* @__PURE__ */ React.createElement("div", { className: "cs-pay-card-note mono" }, t(channel.noteKey)), /* @__PURE__ */ React.createElement("label", { className: "cs-label", style: { marginTop: 12 } }, t("billing.usdt.amount_label")), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap: 8 } }, /* @__PURE__ */ React.createElement(
    "input",
    {
      className: "cs-input",
      type: "number",
      min: 5,
      max: 1e5,
      step: 1,
      value: amount,
      onChange: (e) => setAmount(Number(e.target.value))
    }
  ), /* @__PURE__ */ React.createElement(
    "button",
    {
      className: "cs-btn cs-btn-primary",
      disabled: loading || amount < 5,
      onClick: () => onStart(amount)
    },
    loading ? t("billing.usdt.generating") : t("billing.usdt.go")
  )), /* @__PURE__ */ React.createElement("div", { className: "cs-pay-card-foot mono" }, t("billing.usdt.foot", { fee, credited })));
}
function UsdtIntentModal({ intent, onClose, onPaid }) {
  const [now, setNow] = useState(Date.now());
  const [status, setStatus] = useState(intent.status || "pending");
  useEffect(() => {
    const t2 = setInterval(() => setNow(Date.now()), 1e3);
    return () => clearInterval(t2);
  }, []);
  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const d = await PrismAPI.get("/account/topups");
        const mine = (d.data || []).find((t2) => t2.id === intent.id);
        if (mine && mine.status === "paid") {
          setStatus("paid");
          clearInterval(poll);
          setTimeout(() => onPaid(), 2e3);
        }
      } catch {
      }
    }, 8e3);
    return () => clearInterval(poll);
  }, [intent.id, onPaid]);
  const expiresAt = intent.expires_at ? new Date(intent.expires_at).getTime() : 0;
  const remainSec = Math.max(0, Math.floor((expiresAt - now) / 1e3));
  const mins = Math.floor(remainSec / 60);
  const secs = String(remainSec % 60).padStart(2, "0");
  const copyAddr = () => navigator.clipboard?.writeText(intent.address);
  const copyAmt = () => navigator.clipboard?.writeText(String(intent.expected_amount_usd));
  return /* @__PURE__ */ React.createElement("div", { className: "cs-modal-overlay", onClick: onClose }, /* @__PURE__ */ React.createElement(
    "div",
    {
      className: "cs-modal",
      onClick: (e) => e.stopPropagation(),
      style: { maxWidth: 560 }
    },
    /* @__PURE__ */ React.createElement("h2", { style: { marginTop: 0 } }, status === "paid" ? t("billing.intent.paid_title") : t("billing.intent.title", { ch: intent.channel.toUpperCase() })),
    status !== "paid" && /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement(
      "div",
      {
        className: "cs-pay-banner mono",
        dangerouslySetInnerHTML: { __html: t("billing.intent.banner", {
          amt: intent.expected_amount_usd,
          min: mins,
          sec: secs,
          net: intent.network ? t("billing.intent.network", { net: intent.network.toUpperCase() }) : ""
        }) }
      }
    ), /* @__PURE__ */ React.createElement("label", { className: "cs-label" }, t("billing.intent.addr")), /* @__PURE__ */ React.createElement("div", { className: "cs-pay-row" }, /* @__PURE__ */ React.createElement("code", { className: "cs-pay-addr mono" }, intent.address), /* @__PURE__ */ React.createElement("button", { className: "cs-btn", onClick: copyAddr }, t("billing.intent.copy_addr"))), /* @__PURE__ */ React.createElement("label", { className: "cs-label", style: { marginTop: 12 } }, t("billing.intent.amt")), /* @__PURE__ */ React.createElement("div", { className: "cs-pay-row" }, /* @__PURE__ */ React.createElement("code", { className: "cs-pay-addr mono", style: { fontSize: 18, color: "var(--accent-amber)" } }, "$", intent.expected_amount_usd, " USDC"), /* @__PURE__ */ React.createElement("button", { className: "cs-btn", onClick: copyAmt }, t("billing.intent.copy_amt"))), /* @__PURE__ */ React.createElement(
      "div",
      {
        className: "cs-pay-warn mono",
        dangerouslySetInnerHTML: { __html: t("billing.intent.warn", { memo: intent.memo }) }
      }
    ), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 16, fontSize: 13, color: "var(--text-muted)" } }, t("billing.intent.tail"))),
    status === "paid" && /* @__PURE__ */ React.createElement("div", { className: "cs-pay-success" }, /* @__PURE__ */ React.createElement("p", { dangerouslySetInnerHTML: { __html: t("billing.intent.success_amt", { amt: intent.credited_usd }) } }), /* @__PURE__ */ React.createElement("p", null, t("billing.intent.refresh"))),
    /* @__PURE__ */ React.createElement("div", { className: "cs-modal-actions" }, /* @__PURE__ */ React.createElement("button", { className: "cs-btn", onClick: onClose }, t("usage.modal.close")))
  ));
}
function DomesticPayCard({ titleKey, en, qrUrl, tone }) {
  const [imgError, setImgError] = useState(false);
  const title = t(titleKey);
  return /* @__PURE__ */ React.createElement("div", { className: `cs-pay-card cs-pay-card-${tone}` }, /* @__PURE__ */ React.createElement("div", { className: "cs-pay-card-head" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "cs-pay-card-title" }, title), /* @__PURE__ */ React.createElement("div", { className: "cs-pay-card-en mono" }, en))), /* @__PURE__ */ React.createElement("div", { className: "cs-qr-box" }, imgError ? /* @__PURE__ */ React.createElement("div", { className: "cs-qr-placeholder mono" }, t("billing.qr.placeholder", { file: qrUrl.split("/").pop() })) : /* @__PURE__ */ React.createElement(
    "img",
    {
      src: qrUrl,
      alt: title,
      className: "cs-qr-img",
      loading: "lazy",
      decoding: "async",
      onError: () => setImgError(true)
    }
  )), /* @__PURE__ */ React.createElement("div", { className: "cs-pay-card-foot mono" }, t("billing.qr.foot")));
}
function Settings({ me, setMe }) {
  const [name, setName] = useState(me.display_name || "");
  const [oldPwd, setOldPwd] = useState("");
  const [newPwd, setNewPwd] = useState("");
  const [msg, setMsg] = useState("");
  async function saveProfile(e) {
    e.preventDefault();
    setMsg("");
    try {
      const updated = await PrismAPI.patch("/account/me", { display_name: name });
      setMe(updated);
      setMsg(t("settings.saved_ok"));
    } catch (err) {
      setMsg("\u2717 " + err.message);
    }
  }
  async function changePwd(e) {
    e.preventDefault();
    setMsg("");
    try {
      await PrismAPI.post("/auth/change-password", { old_password: oldPwd, new_password: newPwd });
      setMsg(t("settings.pwd_changed"));
      setOldPwd("");
      setNewPwd("");
    } catch (err) {
      setMsg("\u2717 " + err.message);
    }
  }
  return /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("section", { className: "cs-section" }, /* @__PURE__ */ React.createElement("h2", null, t("settings.profile.title")), /* @__PURE__ */ React.createElement("form", { onSubmit: saveProfile, style: { maxWidth: 480 } }, /* @__PURE__ */ React.createElement("label", { className: "auth-label" }, t("settings.display_name")), /* @__PURE__ */ React.createElement(
    "input",
    {
      className: "auth-input",
      value: name,
      onChange: (e) => setName(e.target.value),
      style: { width: "100%", boxSizing: "border-box" }
    }
  ), /* @__PURE__ */ React.createElement("button", { className: "cs-btn cs-btn-primary", type: "submit" }, t("settings.save")))), /* @__PURE__ */ React.createElement("section", { className: "cs-section" }, /* @__PURE__ */ React.createElement("h2", null, t("settings.changepwd.title")), /* @__PURE__ */ React.createElement("form", { onSubmit: changePwd, style: { maxWidth: 480 } }, /* @__PURE__ */ React.createElement("label", { className: "auth-label" }, t("settings.current_pwd")), /* @__PURE__ */ React.createElement(
    "input",
    {
      className: "auth-input",
      type: "password",
      required: true,
      value: oldPwd,
      onChange: (e) => setOldPwd(e.target.value),
      style: { width: "100%", boxSizing: "border-box" }
    }
  ), /* @__PURE__ */ React.createElement("label", { className: "auth-label" }, t("settings.new_pwd")), /* @__PURE__ */ React.createElement(
    "input",
    {
      className: "auth-input",
      type: "password",
      required: true,
      minLength: 10,
      value: newPwd,
      onChange: (e) => setNewPwd(e.target.value),
      style: { width: "100%", boxSizing: "border-box" }
    }
  ), /* @__PURE__ */ React.createElement("button", { className: "cs-btn cs-btn-primary", type: "submit" }, t("settings.changepwd_btn")))), msg && /* @__PURE__ */ React.createElement("div", { className: "auth-error", style: {
    background: msg.startsWith("\u2713") ? "rgba(16,185,129,0.10)" : "rgba(236,72,153,0.10)",
    borderColor: msg.startsWith("\u2713") ? "rgba(16,185,129,0.3)" : "rgba(236,72,153,0.3)",
    color: msg.startsWith("\u2713") ? "var(--accent-green)" : "#f9a8d4"
  } }, msg));
}
ReactDOM.createRoot(document.getElementById("root")).render(/* @__PURE__ */ React.createElement(ConsoleApp, null));
