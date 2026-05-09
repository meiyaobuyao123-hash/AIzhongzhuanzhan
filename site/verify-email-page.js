const { useState, useEffect } = React;
const t = window.t;
function VerifyEmailPage() {
  const [state, setState] = useState("loading");
  const [message, setMessage] = useState(t("verify.loading"));
  const token = new URLSearchParams(location.search).get("token") || "";
  useEffect(() => {
    if (!token) {
      setState("err");
      setMessage(t("verify.no_token"));
      return;
    }
    fetch("/suanli-api/auth/verify-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token })
    }).then(async (r) => {
      const data = await r.json().catch(() => ({}));
      if (r.ok) {
        setState("ok");
        setMessage(t("verify.success_redirect"));
        setTimeout(() => {
          location.href = "/login";
        }, 3e3);
      } else {
        setState("err");
        const code = data?.error?.code;
        if (code === "expired_verification_token") {
          setMessage(t("verify.expired"));
        } else if (code === "invalid_verification_token") {
          setMessage(t("verify.invalid"));
        } else {
          setMessage(data?.error?.message || `${t("verify.error_title")} (HTTP ${r.status})`);
        }
      }
    }).catch((e) => {
      setState("err");
      setMessage(t("verify.network_err") + (e.message || t("verify.retry_later")));
    });
  }, [token]);
  return /* @__PURE__ */ React.createElement("div", { className: "auth-shell" }, /* @__PURE__ */ React.createElement("div", { className: "auth-brand" }, /* @__PURE__ */ React.createElement("div", { className: "brand-prism", "aria-hidden": "true" }, /* @__PURE__ */ React.createElement("svg", { viewBox: "0 0 200 200", width: "180", height: "180" }, /* @__PURE__ */ React.createElement("defs", null, /* @__PURE__ */ React.createElement("linearGradient", { id: "bp", x1: "0", y1: "0", x2: "1", y2: "1" }, /* @__PURE__ */ React.createElement("stop", { offset: "0%", stopColor: "#8B5CF6" }), /* @__PURE__ */ React.createElement("stop", { offset: "50%", stopColor: "#06B6D4" }), /* @__PURE__ */ React.createElement("stop", { offset: "100%", stopColor: "#EC4899" }))), /* @__PURE__ */ React.createElement(
    "polygon",
    {
      points: "100,30 175,160 25,160",
      fill: "url(#bp)",
      opacity: "0.6",
      stroke: "rgba(255,255,255,0.7)",
      strokeWidth: "1.5",
      strokeLinejoin: "round"
    }
  ))), /* @__PURE__ */ React.createElement("div", { className: "brand-tagline" }, /* @__PURE__ */ React.createElement("h2", { className: "display" }, "Prism"), /* @__PURE__ */ React.createElement("p", null, t("verify.brand_tag")), /* @__PURE__ */ React.createElement("p", { className: "mono" }, "cost = price \xB7 always"))), /* @__PURE__ */ React.createElement("div", { className: "auth-form" }, /* @__PURE__ */ React.createElement("h1", { className: "display" }, state === "loading" && t("verify.h_loading"), state === "ok" && t("verify.h_ok"), state === "err" && t("verify.h_err")), /* @__PURE__ */ React.createElement("p", { style: {
    marginTop: "24px",
    padding: "16px",
    borderRadius: "12px",
    background: state === "ok" ? "rgba(16, 185, 129, 0.08)" : state === "err" ? "rgba(239, 68, 68, 0.08)" : "rgba(99, 102, 241, 0.08)",
    border: state === "ok" ? "1px solid rgba(16, 185, 129, 0.3)" : state === "err" ? "1px solid rgba(239, 68, 68, 0.3)" : "1px solid rgba(99, 102, 241, 0.3)",
    color: "var(--fg)",
    lineHeight: 1.6
  } }, message), /* @__PURE__ */ React.createElement("div", { style: { marginTop: "24px", display: "flex", gap: "12px", flexWrap: "wrap" } }, state === "ok" && /* @__PURE__ */ React.createElement("a", { className: "cta-primary auth-submit", href: "/login" }, t("verify.cta_login")), state === "err" && /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("a", { className: "cta-primary auth-submit", href: "/login" }, t("verify.cta_try")), /* @__PURE__ */ React.createElement("a", { className: "cta-ghost", href: "/signup" }, t("verify.cta_signup")))), /* @__PURE__ */ React.createElement("p", { className: "auth-mini", style: { marginTop: "32px" } }, /* @__PURE__ */ React.createElement("a", { href: "/suanli/" }, t("verify.back_home")))));
}
ReactDOM.createRoot(document.getElementById("root")).render(/* @__PURE__ */ React.createElement(VerifyEmailPage, null));
