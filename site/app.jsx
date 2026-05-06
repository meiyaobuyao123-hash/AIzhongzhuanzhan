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
  useEffectApp(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
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
          <a className="nav-link" href="#docs">
            <span className="zh">文档</span>
            <span className="en mono">docs</span>
          </a>
          <a className="nav-link" href="#console">
            <span className="zh">控制台</span>
            <span className="en mono">console</span>
          </a>
        </div>

        <div className="nav-right">
          <a className="nav-login" href="#login">登录</a>
          <a className="cta-primary nav-cta" href="#signup">
            立即开始
            <Arrow2/>
          </a>
        </div>
      </div>
    </nav>
  );
}

/* Mount */
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
