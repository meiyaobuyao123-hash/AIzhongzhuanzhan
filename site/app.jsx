/* Composition root for Prism homepage. */

const { useState: useStateApp, useEffect: useEffectApp } = React;
const t = window.t;

function App() {
  return (
    <>
      {/* Background ambience (defined in styles.css) */}
      <div className="bg-ambience" aria-hidden="true">
        <div className="nebula-1"/>
        <div className="nebula-2"/>
        <div className="nebula-3"/>
        <div className="stars"/>
      </div>

      <div className="page">
        <TopNav />
        <HeroSection />
        <TrustStrip />
        <FeaturesGrid />
        <LiveDemo />
        <ClientStrip />
        <CategoryGrid />
        <ChannelBanner />
        <NotDoing />
        <PricingPreview />
        <FAQ />
        <FinalCTA />
        <Footer />
      </div>
    </>
  );
}

/* ─── Top nav ───────────────────────────────────────────────────── */

function TopNav() {
  const [scrolled, setScrolled] = useStateApp(false);
  const [loggedIn, setLoggedIn] = useStateApp(false);
  const [userEmail, setUserEmail] = useStateApp('');

  useEffectApp(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Detect existing login by checking the same JWT key the console uses.
  useEffectApp(() => {
    const token = localStorage.getItem('prism_token');
    const exp = localStorage.getItem('prism_token_expires');
    if (!token) return;
    if (exp && new Date(exp).getTime() < Date.now()) return;
    setLoggedIn(true);
    fetch('/suanli-api/account/me', {
      headers: { 'Authorization': 'Bearer ' + token },
    })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d && d.email) setUserEmail(d.email); })
      .catch(() => {});
  }, []);

  return (
    <nav className={`nav ${scrolled ? 'scrolled' : ''}`}>
      <div className="nav-inner">
        <a href="#" className="nav-brand">
          <Logo size={28}/>
          <div>
            <span className="nav-brand-name display">Prism</span>
            <span className="nav-brand-zh">{t('meta.brand_zh')}</span>
          </div>
        </a>

        <div className="nav-links">
          <a className="nav-link active" href="#">
            <span className="zh">{t('nav.home')}</span>
            <span className="en mono">home</span>
          </a>
          <a className="nav-link" href="#models">
            <span className="zh">{t('nav.models')}</span>
            <span className="en mono">models</span>
          </a>
          <a className="nav-link" href="#pricing">
            <span className="zh">{t('nav.pricing')}</span>
            <span className="en mono">pricing</span>
          </a>
          <a className="nav-link" href="/api-docs">
            <span className="zh">{t('nav.docs')}</span>
            <span className="en mono">docs</span>
          </a>
          <a className="nav-link" href="/console">
            <span className="zh">{t('nav.console')}</span>
            <span className="en mono">console</span>
          </a>
        </div>

        <div className="nav-right">
          <LangPicker/>
          {loggedIn ? (
            <>
              {userEmail && (
                <span className="nav-user mono" title={userEmail}>
                  {userEmail.length > 22 ? userEmail.slice(0, 20) + '…' : userEmail}
                </span>
              )}
              <a className="cta-primary nav-cta" href="/console">
                {t('nav.go_console')}
                <Arrow2/>
              </a>
            </>
          ) : (
            <>
              <a className="nav-login" href="/login">{t('nav.login')}</a>
              <a className="cta-primary nav-cta" href="/signup">
                {t('nav.signup')}
                <Arrow2/>
              </a>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

/* ─── Language picker (shared across pages — also reused by signup/login/console via window.PrismLangPicker) ─── */

function LangPicker() {
  const supported = window.PRISM_I18N_SUPPORTED || ['en', 'zh', 'ja', 'ko', 'fr'];
  const current = window.LANG || 'en';
  return (
    <select
      className="lang-picker mono"
      value={current}
      onChange={e => window.setLang(e.target.value)}
      title={t('nav.lang_label')}
      aria-label={t('nav.lang_label')}
    >
      {supported.map(code => (
        <option key={code} value={code}>{t('lang.' + code)}</option>
      ))}
    </select>
  );
}
// Expose so other pages (signup/login/console) can use it without re-defining.
window.PrismLangPicker = LangPicker;

/* Mount */
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
