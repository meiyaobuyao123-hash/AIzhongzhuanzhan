/* /signup page React app — extracted from signup.html for esbuild precompile. */

const { useState } = React;
const t = window.t;

function AuthLangPicker() {
  const supported = window.PRISM_I18N_SUPPORTED;
  const current = window.LANG;
  return (
    <div className="auth-lang-row">
      <select
        className="lang-picker mono"
        value={current}
        onChange={e => window.setLang(e.target.value)}
        title={t('nav.lang_label')}
      >
        {supported.map(c => <option key={c} value={c}>{t('lang.' + c)}</option>)}
      </select>
    </div>
  );
}

function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(null); // {email} after success
  const [error, setError] = useState('');

  async function onSubmit(e) {
    e.preventDefault();
    setError('');
    if (password !== confirm) { setError(t('auth.error.password_mismatch')); return; }
    if (password.length < 10) { setError(t('auth.error.password_short')); return; }
    setLoading(true);
    try {
      const data = await PrismAPI.post('/auth/register', { email, password }, { requireAuth: false });
      if (data.token) {
        PrismAPI.setToken(data.token, data.expires_at);
        location.href = '/console';
        return;
      }
      setSubmitted(data);
    } catch (err) {
      setError(err.message || t('auth.error.signup_failed'));
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <div className="auth-shell">
        <BrandSide/>
        <div className="auth-form">
          <AuthLangPicker/>
          <h1 className="display">{t('auth.signup.success_title')}</h1>
          <p className="auth-sub" dangerouslySetInnerHTML={{
            __html: t('auth.signup.success_body', { email: submitted.email })
          }}/>
          <p className="auth-mini mono">{t('auth.signup.success_mini')}</p>
          <a href="/login" className="cta-ghost auth-back">{t('auth.signup.success_back')}</a>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <BrandSide/>
      <form className="auth-form" onSubmit={onSubmit}>
        <AuthLangPicker/>
        <h1 className="display">{t('auth.signup.title')}</h1>
        <p className="auth-sub">{t('auth.signup.sub')}</p>

        <label className="auth-label">{t('auth.email_label')}</label>
        <input className="auth-input" type="email" required value={email}
          onChange={e => setEmail(e.target.value)} placeholder="dev@example.com"/>

        <label className="auth-label">{t('auth.password_label')}</label>
        <input className="auth-input" type="password" required minLength={10} value={password}
          onChange={e => setPassword(e.target.value)} placeholder={t('auth.password_hint')}/>

        <label className="auth-label">{t('auth.confirm_label')}</label>
        <input className="auth-input" type="password" required value={confirm}
          onChange={e => setConfirm(e.target.value)}/>

        {error && <div className="auth-error">{error}</div>}

        <button className="cta-primary auth-submit" type="submit" disabled={loading}>
          {loading ? t('auth.signup.submitting') : t('auth.signup.submit')}
        </button>

        <OAuthButtons/>

        <p className="auth-mini">
          {t('auth.signup.have_account')}<a href="/login">{t('auth.login.title')}</a>
          ·
          <a href="/suanli/">{t('auth.back_home')}</a>
        </p>
      </form>
    </div>
  );
}

function OAuthButtons() {
  const [providers, setProviders] = useState([]);
  React.useEffect(() => {
    fetch('/suanli-api/auth/oauth/providers').then(r => r.json()).then(d => {
      setProviders((d.data || []).filter(p => p.configured));
    }).catch(() => {});
  }, []);

  if (!providers.length) return null;
  return (
    <div className="auth-oauth">
      <div className="auth-divider"><span>{t('auth.oauth.or')}</span></div>
      {providers.map(p => (
        <a key={p.name} className="cta-ghost auth-oauth-btn"
           href={`/suanli-api/auth/oauth/${p.name}/authorize`}>
          {p.name === 'github' ? t('auth.oauth.github') : t('auth.oauth.google')}
        </a>
      ))}
    </div>
  );
}

function BrandSide() {
  return (
    <div className="auth-brand">
      <div className="brand-prism" aria-hidden="true">
        <svg viewBox="0 0 200 200" width="180" height="180">
          <defs>
            <linearGradient id="bp" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#8B5CF6"/>
              <stop offset="50%" stopColor="#06B6D4"/>
              <stop offset="100%" stopColor="#EC4899"/>
            </linearGradient>
          </defs>
          <polygon points="100,30 175,160 25,160" fill="url(#bp)" opacity="0.6"
            stroke="rgba(255,255,255,0.7)" strokeWidth="1.5" strokeLinejoin="round"/>
        </svg>
      </div>
      <div className="brand-tagline">
        <h2 className="display">Prism</h2>
        <p>{t('auth.brand.signup_tag')}</p>
        <p className="mono">cost = price · always</p>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<SignupPage/>);
