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
  const [drawerOpen, setDrawerOpen] = useStateApp(false);

  useEffectApp(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Lock body scroll while drawer open
  useEffectApp(() => {
    document.body.style.overflow = drawerOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [drawerOpen]);

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
    <>
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

          <button
            className="nav-burger"
            aria-label="Menu"
            aria-expanded={drawerOpen}
            onClick={() => setDrawerOpen(true)}
          >
            <span/><span/><span/>
          </button>
        </div>
      </nav>

      {drawerOpen && (
        <MobileDrawer
          loggedIn={loggedIn}
          userEmail={userEmail}
          onClose={() => setDrawerOpen(false)}
        />
      )}
    </>
  );
}

/* ─── Mobile drawer (full-screen overlay) ─────────────────────── */

function MobileDrawer({ loggedIn, userEmail, onClose }) {
  return (
    <div className="mobile-drawer" role="dialog" aria-modal="true">
      <div className="mobile-drawer-head">
        <a href="#" className="nav-brand" onClick={onClose}>
          <Logo size={28}/>
          <span className="nav-brand-name display">Prism</span>
        </a>
        <button className="mobile-drawer-close" aria-label="Close" onClick={onClose}>
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <path d="M5 5l12 12M17 5L5 17" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
          </svg>
        </button>
      </div>

      <nav className="mobile-drawer-links">
        <a href="#" onClick={onClose}>{t('nav.home')}</a>
        <a href="#models" onClick={onClose}>{t('nav.models')}</a>
        <a href="#pricing" onClick={onClose}>{t('nav.pricing')}</a>
        <a href="/api-docs">{t('nav.docs')}</a>
        <a href="/console">{t('nav.console')}</a>
      </nav>

      <div className="mobile-drawer-lang">
        <LangPicker/>
      </div>

      <div className="mobile-drawer-cta">
        {loggedIn ? (
          <>
            {userEmail && (
              <div className="mobile-drawer-user mono">{userEmail}</div>
            )}
            <a className="cta-primary" href="/console">
              {t('nav.go_console')}<Arrow2/>
            </a>
          </>
        ) : (
          <>
            <a className="cta-ghost" href="/login">{t('nav.login')}</a>
            <a className="cta-primary" href="/signup">
              {t('nav.signup')}<Arrow2/>
            </a>
          </>
        )}
      </div>
    </div>
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
