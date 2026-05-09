const { useState: useStateApp, useEffect: useEffectApp } = React;
const t = window.t;
function App() {
  return /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", { className: "bg-ambience", "aria-hidden": "true" }, /* @__PURE__ */ React.createElement("div", { className: "nebula-1" }), /* @__PURE__ */ React.createElement("div", { className: "nebula-2" }), /* @__PURE__ */ React.createElement("div", { className: "nebula-3" }), /* @__PURE__ */ React.createElement("div", { className: "stars" })), /* @__PURE__ */ React.createElement("div", { className: "page" }, /* @__PURE__ */ React.createElement(TopNav, null), /* @__PURE__ */ React.createElement(HeroSection, null), /* @__PURE__ */ React.createElement(TrustStrip, null), /* @__PURE__ */ React.createElement(FeaturesGrid, null), /* @__PURE__ */ React.createElement(LiveDemo, null), /* @__PURE__ */ React.createElement(ClientStrip, null), /* @__PURE__ */ React.createElement(CategoryGrid, null), /* @__PURE__ */ React.createElement(ChannelBanner, null), /* @__PURE__ */ React.createElement(NotDoing, null), /* @__PURE__ */ React.createElement(PricingPreview, null), /* @__PURE__ */ React.createElement(FAQ, null), /* @__PURE__ */ React.createElement(FinalCTA, null), /* @__PURE__ */ React.createElement(Footer, null)));
}
function TopNav() {
  const [scrolled, setScrolled] = useStateApp(false);
  const [loggedIn, setLoggedIn] = useStateApp(false);
  const [userEmail, setUserEmail] = useStateApp("");
  const [drawerOpen, setDrawerOpen] = useStateApp(false);
  useEffectApp(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  useEffectApp(() => {
    document.body.style.overflow = drawerOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [drawerOpen]);
  useEffectApp(() => {
    const token = localStorage.getItem("prism_token");
    const exp = localStorage.getItem("prism_token_expires");
    if (!token) return;
    if (exp && new Date(exp).getTime() < Date.now()) return;
    setLoggedIn(true);
    fetch("/suanli-api/account/me", {
      headers: { "Authorization": "Bearer " + token }
    }).then((r) => r.ok ? r.json() : null).then((d) => {
      if (d && d.email) setUserEmail(d.email);
    }).catch(() => {
    });
  }, []);
  return /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("nav", { className: `nav ${scrolled ? "scrolled" : ""}` }, /* @__PURE__ */ React.createElement("div", { className: "nav-inner" }, /* @__PURE__ */ React.createElement("a", { href: "#", className: "nav-brand" }, /* @__PURE__ */ React.createElement(Logo, { size: 28 }), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: "nav-brand-name display" }, "Prism"), /* @__PURE__ */ React.createElement("span", { className: "nav-brand-zh" }, t("meta.brand_zh")))), /* @__PURE__ */ React.createElement("div", { className: "nav-links" }, /* @__PURE__ */ React.createElement("a", { className: "nav-link active", href: "#" }, /* @__PURE__ */ React.createElement("span", { className: "zh" }, t("nav.home")), /* @__PURE__ */ React.createElement("span", { className: "en mono" }, "home")), /* @__PURE__ */ React.createElement("a", { className: "nav-link", href: "#models" }, /* @__PURE__ */ React.createElement("span", { className: "zh" }, t("nav.models")), /* @__PURE__ */ React.createElement("span", { className: "en mono" }, "models")), /* @__PURE__ */ React.createElement("a", { className: "nav-link", href: "#pricing" }, /* @__PURE__ */ React.createElement("span", { className: "zh" }, t("nav.pricing")), /* @__PURE__ */ React.createElement("span", { className: "en mono" }, "pricing")), /* @__PURE__ */ React.createElement("a", { className: "nav-link", href: "/api-docs" }, /* @__PURE__ */ React.createElement("span", { className: "zh" }, t("nav.docs")), /* @__PURE__ */ React.createElement("span", { className: "en mono" }, "docs")), /* @__PURE__ */ React.createElement("a", { className: "nav-link", href: "/console" }, /* @__PURE__ */ React.createElement("span", { className: "zh" }, t("nav.console")), /* @__PURE__ */ React.createElement("span", { className: "en mono" }, "console"))), /* @__PURE__ */ React.createElement("div", { className: "nav-right" }, /* @__PURE__ */ React.createElement(LangPicker, null), loggedIn ? /* @__PURE__ */ React.createElement(React.Fragment, null, userEmail && /* @__PURE__ */ React.createElement("span", { className: "nav-user mono", title: userEmail }, userEmail.length > 22 ? userEmail.slice(0, 20) + "\u2026" : userEmail), /* @__PURE__ */ React.createElement("a", { className: "cta-primary nav-cta", href: "/console" }, t("nav.go_console"), /* @__PURE__ */ React.createElement(Arrow2, null))) : /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("a", { className: "nav-login", href: "/login" }, t("nav.login")), /* @__PURE__ */ React.createElement("a", { className: "cta-primary nav-cta", href: "/signup" }, t("nav.signup"), /* @__PURE__ */ React.createElement(Arrow2, null)))), /* @__PURE__ */ React.createElement(
    "button",
    {
      className: "nav-burger",
      "aria-label": "Menu",
      "aria-expanded": drawerOpen,
      onClick: () => setDrawerOpen(true)
    },
    /* @__PURE__ */ React.createElement("span", null),
    /* @__PURE__ */ React.createElement("span", null),
    /* @__PURE__ */ React.createElement("span", null)
  ))), drawerOpen && /* @__PURE__ */ React.createElement(
    MobileDrawer,
    {
      loggedIn,
      userEmail,
      onClose: () => setDrawerOpen(false)
    }
  ));
}
function MobileDrawer({ loggedIn, userEmail, onClose }) {
  return /* @__PURE__ */ React.createElement("div", { className: "mobile-drawer", role: "dialog", "aria-modal": "true" }, /* @__PURE__ */ React.createElement("div", { className: "mobile-drawer-head" }, /* @__PURE__ */ React.createElement("a", { href: "#", className: "nav-brand", onClick: onClose }, /* @__PURE__ */ React.createElement(Logo, { size: 28 }), /* @__PURE__ */ React.createElement("span", { className: "nav-brand-name display" }, "Prism")), /* @__PURE__ */ React.createElement("button", { className: "mobile-drawer-close", "aria-label": "Close", onClick: onClose }, /* @__PURE__ */ React.createElement("svg", { width: "22", height: "22", viewBox: "0 0 22 22", fill: "none" }, /* @__PURE__ */ React.createElement("path", { d: "M5 5l12 12M17 5L5 17", stroke: "currentColor", strokeWidth: "1.6", strokeLinecap: "round" })))), /* @__PURE__ */ React.createElement("nav", { className: "mobile-drawer-links" }, /* @__PURE__ */ React.createElement("a", { href: "#", onClick: onClose }, t("nav.home")), /* @__PURE__ */ React.createElement("a", { href: "#models", onClick: onClose }, t("nav.models")), /* @__PURE__ */ React.createElement("a", { href: "#pricing", onClick: onClose }, t("nav.pricing")), /* @__PURE__ */ React.createElement("a", { href: "/api-docs" }, t("nav.docs")), /* @__PURE__ */ React.createElement("a", { href: "/console" }, t("nav.console"))), /* @__PURE__ */ React.createElement("div", { className: "mobile-drawer-lang" }, /* @__PURE__ */ React.createElement(LangPicker, null)), /* @__PURE__ */ React.createElement("div", { className: "mobile-drawer-cta" }, loggedIn ? /* @__PURE__ */ React.createElement(React.Fragment, null, userEmail && /* @__PURE__ */ React.createElement("div", { className: "mobile-drawer-user mono" }, userEmail), /* @__PURE__ */ React.createElement("a", { className: "cta-primary", href: "/console" }, t("nav.go_console"), /* @__PURE__ */ React.createElement(Arrow2, null))) : /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("a", { className: "cta-ghost", href: "/login" }, t("nav.login")), /* @__PURE__ */ React.createElement("a", { className: "cta-primary", href: "/signup" }, t("nav.signup"), /* @__PURE__ */ React.createElement(Arrow2, null)))));
}
function LangPicker() {
  const supported = window.PRISM_I18N_SUPPORTED || ["en", "zh", "ja", "ko", "fr"];
  const current = window.LANG || "en";
  return /* @__PURE__ */ React.createElement(
    "select",
    {
      className: "lang-picker mono",
      value: current,
      onChange: (e) => window.setLang(e.target.value),
      title: t("nav.lang_label"),
      "aria-label": t("nav.lang_label")
    },
    supported.map((code) => /* @__PURE__ */ React.createElement("option", { key: code, value: code }, t("lang." + code)))
  );
}
window.PrismLangPicker = LangPicker;
ReactDOM.createRoot(document.getElementById("root")).render(/* @__PURE__ */ React.createElement(App, null));
