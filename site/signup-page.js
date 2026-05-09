const { useState } = React;
const t = window.t;
function AuthLangPicker() {
  const supported = window.PRISM_I18N_SUPPORTED;
  const current = window.LANG;
  return /* @__PURE__ */ React.createElement("div", { className: "auth-lang-row" }, /* @__PURE__ */ React.createElement(
    "select",
    {
      className: "lang-picker mono",
      value: current,
      onChange: (e) => window.setLang(e.target.value),
      title: t("nav.lang_label")
    },
    supported.map((c) => /* @__PURE__ */ React.createElement("option", { key: c, value: c }, t("lang." + c)))
  ));
}
function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(null);
  const [error, setError] = useState("");
  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError(t("auth.error.password_mismatch"));
      return;
    }
    if (password.length < 10) {
      setError(t("auth.error.password_short"));
      return;
    }
    setLoading(true);
    try {
      const data = await PrismAPI.post("/auth/register", { email, password }, { requireAuth: false });
      if (data.token) {
        PrismAPI.setToken(data.token, data.expires_at);
        location.href = "/console";
        return;
      }
      setSubmitted(data);
    } catch (err) {
      setError(err.message || t("auth.error.signup_failed"));
    } finally {
      setLoading(false);
    }
  }
  if (submitted) {
    return /* @__PURE__ */ React.createElement("div", { className: "auth-shell" }, /* @__PURE__ */ React.createElement(BrandSide, null), /* @__PURE__ */ React.createElement("div", { className: "auth-form" }, /* @__PURE__ */ React.createElement(AuthLangPicker, null), /* @__PURE__ */ React.createElement("h1", { className: "display" }, t("auth.signup.success_title")), /* @__PURE__ */ React.createElement("p", { className: "auth-sub", dangerouslySetInnerHTML: {
      __html: t("auth.signup.success_body", { email: submitted.email })
    } }), /* @__PURE__ */ React.createElement("p", { className: "auth-mini mono" }, t("auth.signup.success_mini")), /* @__PURE__ */ React.createElement("a", { href: "/login", className: "cta-ghost auth-back" }, t("auth.signup.success_back"))));
  }
  return /* @__PURE__ */ React.createElement("div", { className: "auth-shell" }, /* @__PURE__ */ React.createElement(BrandSide, null), /* @__PURE__ */ React.createElement("form", { className: "auth-form", onSubmit }, /* @__PURE__ */ React.createElement(AuthLangPicker, null), /* @__PURE__ */ React.createElement("h1", { className: "display" }, t("auth.signup.title")), /* @__PURE__ */ React.createElement("p", { className: "auth-sub" }, t("auth.signup.sub")), /* @__PURE__ */ React.createElement("label", { className: "auth-label" }, t("auth.email_label")), /* @__PURE__ */ React.createElement(
    "input",
    {
      className: "auth-input",
      type: "email",
      required: true,
      value: email,
      onChange: (e) => setEmail(e.target.value),
      placeholder: "dev@example.com"
    }
  ), /* @__PURE__ */ React.createElement("label", { className: "auth-label" }, t("auth.password_label")), /* @__PURE__ */ React.createElement(
    "input",
    {
      className: "auth-input",
      type: "password",
      required: true,
      minLength: 10,
      value: password,
      onChange: (e) => setPassword(e.target.value),
      placeholder: t("auth.password_hint")
    }
  ), /* @__PURE__ */ React.createElement("label", { className: "auth-label" }, t("auth.confirm_label")), /* @__PURE__ */ React.createElement(
    "input",
    {
      className: "auth-input",
      type: "password",
      required: true,
      value: confirm,
      onChange: (e) => setConfirm(e.target.value)
    }
  ), error && /* @__PURE__ */ React.createElement("div", { className: "auth-error" }, error), /* @__PURE__ */ React.createElement("button", { className: "cta-primary auth-submit", type: "submit", disabled: loading }, loading ? t("auth.signup.submitting") : t("auth.signup.submit")), /* @__PURE__ */ React.createElement(OAuthButtons, null), /* @__PURE__ */ React.createElement("p", { className: "auth-mini" }, t("auth.signup.have_account"), /* @__PURE__ */ React.createElement("a", { href: "/login" }, t("auth.login.title")), "\xB7", /* @__PURE__ */ React.createElement("a", { href: "/suanli/" }, t("auth.back_home")))));
}
function OAuthButtons() {
  const [providers, setProviders] = useState([]);
  React.useEffect(() => {
    fetch("/suanli-api/auth/oauth/providers").then((r) => r.json()).then((d) => {
      setProviders((d.data || []).filter((p) => p.configured));
    }).catch(() => {
    });
  }, []);
  if (!providers.length) return null;
  return /* @__PURE__ */ React.createElement("div", { className: "auth-oauth" }, /* @__PURE__ */ React.createElement("div", { className: "auth-divider" }, /* @__PURE__ */ React.createElement("span", null, t("auth.oauth.or"))), providers.map((p) => /* @__PURE__ */ React.createElement(
    "a",
    {
      key: p.name,
      className: "cta-ghost auth-oauth-btn",
      href: `/suanli-api/auth/oauth/${p.name}/authorize`
    },
    p.name === "github" ? t("auth.oauth.github") : t("auth.oauth.google")
  )));
}
function BrandSide() {
  return /* @__PURE__ */ React.createElement("div", { className: "auth-brand" }, /* @__PURE__ */ React.createElement("div", { className: "brand-prism", "aria-hidden": "true" }, /* @__PURE__ */ React.createElement("svg", { viewBox: "0 0 200 200", width: "180", height: "180" }, /* @__PURE__ */ React.createElement("defs", null, /* @__PURE__ */ React.createElement("linearGradient", { id: "bp", x1: "0", y1: "0", x2: "1", y2: "1" }, /* @__PURE__ */ React.createElement("stop", { offset: "0%", stopColor: "#8B5CF6" }), /* @__PURE__ */ React.createElement("stop", { offset: "50%", stopColor: "#06B6D4" }), /* @__PURE__ */ React.createElement("stop", { offset: "100%", stopColor: "#EC4899" }))), /* @__PURE__ */ React.createElement(
    "polygon",
    {
      points: "100,30 175,160 25,160",
      fill: "url(#bp)",
      opacity: "0.6",
      stroke: "rgba(255,255,255,0.7)",
      strokeWidth: "1.5",
      strokeLinejoin: "round"
    }
  ))), /* @__PURE__ */ React.createElement("div", { className: "brand-tagline" }, /* @__PURE__ */ React.createElement("h2", { className: "display" }, "Prism"), /* @__PURE__ */ React.createElement("p", null, t("auth.brand.signup_tag")), /* @__PURE__ */ React.createElement("p", { className: "mono" }, "cost = price \xB7 always")));
}
ReactDOM.createRoot(document.getElementById("root")).render(/* @__PURE__ */ React.createElement(SignupPage, null));
