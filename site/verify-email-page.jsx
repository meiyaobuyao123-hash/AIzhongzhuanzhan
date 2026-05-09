/* /verify-email page React app — extracted from verify-email.html for esbuild precompile. */

const { useState, useEffect } = React;
const t = window.t;

function VerifyEmailPage() {
  const [state, setState] = useState('loading'); // 'loading' | 'ok' | 'err'
  const [message, setMessage] = useState(t('verify.loading'));
  const token = new URLSearchParams(location.search).get('token') || '';

  useEffect(() => {
    if (!token) {
      setState('err');
      setMessage(t('verify.no_token'));
      return;
    }
    fetch('/suanli-api/auth/verify-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    })
      .then(async (r) => {
        const data = await r.json().catch(() => ({}));
        if (r.ok) {
          setState('ok');
          setMessage(t('verify.success_redirect'));
          setTimeout(() => { location.href = '/login'; }, 3000);
        } else {
          setState('err');
          const code = data?.error?.code;
          if (code === 'expired_verification_token') {
            setMessage(t('verify.expired'));
          } else if (code === 'invalid_verification_token') {
            setMessage(t('verify.invalid'));
          } else {
            setMessage(data?.error?.message || `${t('verify.error_title')} (HTTP ${r.status})`);
          }
        }
      })
      .catch((e) => {
        setState('err');
        setMessage(t('verify.network_err') + (e.message || t('verify.retry_later')));
      });
  }, [token]);

  return (
    <div className="auth-shell">
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
          <p>{t('verify.brand_tag')}</p>
          <p className="mono">cost = price · always</p>
        </div>
      </div>

      <div className="auth-form">
        <h1 className="display">
          {state === 'loading' && t('verify.h_loading')}
          {state === 'ok' && t('verify.h_ok')}
          {state === 'err' && t('verify.h_err')}
        </h1>

        <p style={{
          marginTop: '24px',
          padding: '16px',
          borderRadius: '12px',
          background: state === 'ok' ? 'rgba(16, 185, 129, 0.08)'
                    : state === 'err' ? 'rgba(239, 68, 68, 0.08)'
                    : 'rgba(99, 102, 241, 0.08)',
          border: state === 'ok' ? '1px solid rgba(16, 185, 129, 0.3)'
                : state === 'err' ? '1px solid rgba(239, 68, 68, 0.3)'
                : '1px solid rgba(99, 102, 241, 0.3)',
          color: 'var(--fg)',
          lineHeight: 1.6,
        }}>
          {message}
        </p>

        <div style={{ marginTop: '24px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {state === 'ok' && (
            <a className="cta-primary auth-submit" href="/login">{t('verify.cta_login')}</a>
          )}
          {state === 'err' && (
            <>
              <a className="cta-primary auth-submit" href="/login">{t('verify.cta_try')}</a>
              <a className="cta-ghost" href="/signup">{t('verify.cta_signup')}</a>
            </>
          )}
        </div>

        <p className="auth-mini" style={{ marginTop: '32px' }}>
          <a href="/suanli/">{t('verify.back_home')}</a>
        </p>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<VerifyEmailPage/>);
