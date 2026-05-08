/* Composition root for Prism homepage. */

const { useState: useStateApp, useEffect: useEffectApp } = React;

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
    // If we know the expiry and it's already past, treat as logged out.
    if (exp && new Date(exp).getTime() < Date.now()) return;
    setLoggedIn(true);
    // Best-effort fetch /account/me for the email display (non-blocking).
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
            <span className="nav-brand-zh">棱镜</span>
          </div>
        </a>

        <div className="nav-links">
          <a className="nav-link active" href="#">
            <span className="zh">首页</span>
            <span className="en mono">home</span>
          </a>
          <a className="nav-link" href="#models">
            <span className="zh">模型</span>
            <span className="en mono">models</span>
          </a>
          <a className="nav-link" href="#pricing">
            <span className="zh">定价</span>
            <span className="en mono">pricing</span>
          </a>
          <a className="nav-link" href="/api-docs">
            <span className="zh">文档</span>
            <span className="en mono">docs</span>
          </a>
          <a className="nav-link" href="/console">
            <span className="zh">控制台</span>
            <span className="en mono">console</span>
          </a>
        </div>

        <div className="nav-right">
          {loggedIn ? (
            <>
              {userEmail && (
                <span className="nav-user mono" title={userEmail}>
                  {userEmail.length > 22 ? userEmail.slice(0, 20) + '…' : userEmail}
                </span>
              )}
              <a className="cta-primary nav-cta" href="/console">
                进入控制台
                <Arrow2/>
              </a>
            </>
          ) : (
            <>
              <a className="nav-login" href="/login">登录</a>
              <a className="cta-primary nav-cta" href="/signup">
                立即开始
                <Arrow2/>
              </a>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

/* Mount */
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
