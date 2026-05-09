/* Prism Console SPA — single hash-routed app with 5 tabs. */

const { useState, useEffect, useCallback } = React;
const t = window.t;

function ConsoleLangPicker() {
  const supported = window.PRISM_I18N_SUPPORTED;
  const current = window.LANG;
  return (
    <select
      className="lang-picker mono"
      value={current}
      onChange={e => window.setLang(e.target.value)}
      title={t('nav.lang_label')}
      aria-label={t('nav.lang_label')}
      style={{marginRight: 12}}
    >
      {supported.map(c => <option key={c} value={c}>{t('lang.' + c)}</option>)}
    </select>
  );
}

/* ── Icon system: Lucide-style inline SVGs (no third-party deps) ──────── */

const ICON_PATHS = {
  // Nav icons
  home:      '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
  key:       '<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>',
  chart:     '<path d="M3 3v18h18"/><path d="M7 16l4-4 4 4 5-5"/>',
  wallet:    '<path d="M21 12V7a2 2 0 0 0-2-2H5a2 2 0 0 0 0 4h16v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><circle cx="17" cy="14" r="1.5"/>',
  settings:  '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
  // Metric icons
  zap:       '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
  arrowDown: '<line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>',
  arrowUp:   '<line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>',
  dollar:    '<line x1="12" y1="2" x2="12" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
  // Misc
  book:      '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
  copy:      '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  x:         '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  check:     '<polyline points="20 6 9 17 4 12"/>',
  chevronDown:  '<polyline points="6 9 12 15 18 9"/>',
  chevronRight: '<polyline points="9 18 15 12 9 6"/>',
  // Pay icons (for USDC cards — geometric shapes)
  diamond:   '<rect x="3" y="11" width="18" height="11" rx="2"/><circle cx="12" cy="16" r="1"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  hexagon:   '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>',
  circle:    '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/>',
};

function Icon({ name, size = 16, className = '', color }) {
  const path = ICON_PATHS[name];
  if (!path) return null;
  return (
    <svg className={`cs-icon ${className}`} width={size} height={size} viewBox="0 0 24 24"
         fill="none" stroke={color || 'currentColor'} strokeWidth="1.75"
         strokeLinecap="round" strokeLinejoin="round"
         dangerouslySetInnerHTML={{ __html: path }}/>
  );
}

const TABS = [
  { id: 'overview', labelKey: 'console.tab.overview', icon: 'home' },
  { id: 'keys',     labelKey: 'console.tab.keys',     icon: 'key' },
  { id: 'usage',    labelKey: 'console.tab.usage',    icon: 'chart' },
  { id: 'billing',  labelKey: 'console.tab.billing',  icon: 'wallet' },
  { id: 'settings', labelKey: 'console.tab.settings', icon: 'settings' },
];

function getTabFromHash() {
  const h = (location.hash || '').replace(/^#/, '');
  return TABS.find(t => t.id === h)?.id || 'overview';
}

function fmtUSD(n) {
  if (typeof n !== 'number') return '-';
  return '$' + n.toFixed(4);
}

function fmtCompact(n) {
  if (n === undefined || n === null) return '-';
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return String(n);
}

function ConsoleApp() {
  const [tab, setTab] = useState(getTabFromHash());
  const [me, setMe] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const onHash = () => setTab(getTabFromHash());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  useEffect(() => {
    if (!PrismAPI.isLoggedIn()) {
      location.href = '/login?next=' + encodeURIComponent('/console');
      return;
    }
    PrismAPI.get('/account/me')
      .then(setMe)
      .catch(err => setError(err.message));
  }, []);

  async function logout() {
    try { await PrismAPI.post('/auth/logout', {}); } catch {}
    PrismAPI.clearToken();
    location.href = '/login';
  }

  if (error) return <div className="cs-main"><div className="auth-error">{error}</div></div>;
  if (!me) return <div className="cs-main"><div className="cs-empty">{t('console.loading')}</div></div>;

  return (
    <div className="cs-shell">
      <aside className="cs-sidebar">
        <a href="/suanli/" className="cs-brand cs-brand-link" title={t('console.brand_back')}>
          <span className="cs-brand-mark">P</span>
          <span className="cs-brand-name">Prism</span>
        </a>
        {TABS.map(tt => (
          <a key={tt.id} href={`#${tt.id}`}
             className={`cs-nav-link ${tab === tt.id ? 'active' : ''}`}>
            <Icon name={tt.icon}/>
            <span>{t(tt.labelKey)}</span>
          </a>
        ))}
        <div style={{height: 12}}/>
        <a href="/api-docs" target="_blank" rel="noreferrer"
           className="cs-nav-link cs-nav-external" title={t('console.api_docs_tip')}>
          <Icon name="book"/>
          <span>{t('console.api_docs')}</span>
          <Icon name="arrowUp" size={11} className="cs-icon-ext"/>
        </a>
        <a href="/quickstart" target="_blank" rel="noreferrer"
           className="cs-nav-link cs-nav-external" title={t('console.quickstart_tip')}>
          <Icon name="zap"/>
          <span>{t('console.quickstart')}</span>
          <Icon name="arrowUp" size={11} className="cs-icon-ext"/>
        </a>
        <div className="cs-nav-foot">
          {me.email}
          <br/>
          <span className="mono" style={{fontSize: 11, color: 'var(--text-muted)'}}>{t('console.tier')}: {me.tier}</span>
          <button className="cs-logout" onClick={logout}>{t('console.logout')}</button>
        </div>
      </aside>

      <main className="cs-main">
        <div className="cs-page-header">
          <h1>{t(TABS.find(tt => tt.id === tab).labelKey)}</h1>
          <div style={{display: 'flex', alignItems: 'center'}}>
            <ConsoleLangPicker/>
            <div className="cs-balance-pill">
              <span style={{display: 'inline-flex', gap: 12, alignItems: 'center'}}>
                <span title={t('console.bal.usd_tip')}>
                  <span style={{color: 'var(--text-muted)', fontSize: 11, marginRight: 4}}>USD</span>
                  <strong>{fmtUSD(me.balance_usd)}</strong>
                </span>
                <span style={{color: 'var(--text-faint)', fontSize: 11}}>·</span>
                <span title={t('console.bal.cny_tip')}>
                  <span style={{color: 'var(--text-muted)', fontSize: 11, marginRight: 4}}>CNY</span>
                  <strong>¥{(me.balance_cny ?? 0).toFixed(2)}</strong>
                </span>
              </span>
              <a href="#billing" className="cs-btn cs-btn-primary" style={{padding: '4px 12px'}}>{t('console.topup_btn')}</a>
            </div>
          </div>
        </div>

        {tab === 'overview' && <Overview me={me}/>}
        {tab === 'keys'     && <Keys me={me}/>}
        {tab === 'usage'    && <Usage me={me}/>}
        {tab === 'billing'  && <Billing me={me}/>}
        {tab === 'settings' && <Settings me={me} setMe={setMe}/>}
      </main>
    </div>
  );
}

/* ─── Overview ───────────────────────────────────────────────────────────── */

function Overview({ me }) {
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    PrismAPI.get('/usage/stats?group_by=day').then(setStats).catch(() => {});
    PrismAPI.get('/usage/requests?size=10').then(d => setRecent(d.data || [])).catch(() => {});
  }, []);

  const totalCost = stats?.summary?.total_cost_usd ?? 0;
  const totalRequests = stats?.summary?.total_requests ?? 0;

  return (
    <>
      <div className="cs-metrics">
        <Metric label={t('console.metric.usd_wallet')} value={fmtUSD(me.balance_usd)}
          meta={t('console.metric.usd_meta', { usd: fmtUSD(me.total_topped_up_usd) })}
          icon="dollar" accent="green"/>
        <Metric label={t('console.metric.cny_wallet')} value={`¥${(me.balance_cny ?? 0).toFixed(2)}`}
          meta={t('console.metric.cny_meta', { cny: `¥${(me.total_topped_up_cny ?? 0).toFixed(2)}` })}
          icon="zap" accent="magenta"/>
        <Metric label={t('console.metric.month_calls')} value={fmtCompact(totalRequests)} meta={t('console.metric.month_calls_meta')}/>
        <Metric label={t('console.metric.month_cost')} value={fmtUSD(totalCost)} meta={t('console.metric.month_cost_meta')}/>
      </div>

      <section className="cs-section">
        <h2>{t('console.recent.title')}</h2>
        {recent.length === 0 ? (
          <div className="cs-empty">{t('console.recent.empty')}</div>
        ) : (
          <table className="cs-table">
            <thead>
              <tr>
                <th>{t('console.col.time')}</th>
                <th>{t('console.col.model')}</th>
                <th>{t('console.col.status')}</th>
                <th>{t('console.col.tokens')}</th>
                <th>{t('console.col.cost')}</th>
                <th>{t('console.col.latency')}</th>
                <th>{t('console.col.detail')}</th>
              </tr>
            </thead>
            <tbody>
              {recent.map(r => (
                <tr key={r.request_id}>
                  <td className="mono">{r.created_at?.slice(11, 19)}</td>
                  <td>{r.model_id}</td>
                  <td><StatusPill status={r.status}/></td>
                  <td className="mono">{r.tokens.prompt} / {r.tokens.completion}</td>
                  <td>{fmtUSD(r.cost_usd)}</td>
                  <td className="mono">{r.latency_ms}ms</td>
                  <td>
                    <a href={`#usage/${r.request_id}`} className="cs-btn" style={{padding: '4px 10px'}}>{t('console.view')}</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  );
}

function Metric({ label, value, meta, icon, accent }) {
  const accentClass = accent ? `cs-metric-${accent}` : '';
  return (
    <div className={`cs-metric ${accentClass}`}>
      <div className="cs-metric-head">
        {icon && (
          <span className="cs-metric-icon">
            {typeof icon === 'string' ? <Icon name={icon} size={15}/> : icon}
          </span>
        )}
        <div className="cs-metric-label">{label}</div>
      </div>
      <div className="cs-metric-value">{value}</div>
      {meta && <div className="cs-metric-meta">{meta}</div>}
    </div>
  );
}

function StatusPill({ status }) {
  const cls = status === 'ok' ? 'cs-pill-ok'
            : status === 'partial' ? 'cs-pill-warn'
            : 'cs-pill-err';
  return <span className={`cs-pill ${cls}`}>{status}</span>;
}

/* Provider/family color coding for model_id badges. Returns a CSS modifier. */
function modelFamily(modelId) {
  const m = (modelId || '').toLowerCase();
  if (m.startsWith('claude'))  return 'anthropic';
  if (m.startsWith('gpt-') || m.startsWith('o1') || m.startsWith('o3') || m.startsWith('o4') || m.startsWith('o5')) return 'openai';
  if (m.startsWith('doubao'))  return 'doubao';
  if (m.startsWith('deepseek'))return 'deepseek';
  if (m.startsWith('minimax') || m.startsWith('abab')) return 'minimax';
  if (m.startsWith('gemini'))  return 'google';
  if (m.startsWith('glm'))     return 'glm';
  if (m.startsWith('qwen'))    return 'qwen';
  if (m.startsWith('kimi'))    return 'kimi';
  return 'other';
}

function ProviderBadge({ modelId }) {
  const fam = modelFamily(modelId);
  const labels = {
    anthropic: 'Claude', openai: 'OpenAI', doubao: 'Doubao',
    deepseek: 'DeepSeek', minimax: 'MiniMax', google: 'Gemini',
    glm: 'GLM', qwen: 'Qwen', kimi: 'Kimi', other: '·',
  };
  return (
    <span className={`cs-fam cs-fam-${fam}`} title={modelId}>
      {labels[fam]}
    </span>
  );
}

function ModelCell({ modelId }) {
  return (
    <span className="cs-model-cell">
      <ProviderBadge modelId={modelId}/>
      <span className="mono cs-model-id">{modelId}</span>
    </span>
  );
}

/* ─── Keys ───────────────────────────────────────────────────────────────── */

function Keys() {
  const [keys, setKeys] = useState(null);
  const [creating, setCreating] = useState(false);
  const [createdKey, setCreatedKey] = useState(null);

  const refresh = useCallback(() => {
    PrismAPI.get('/account/api-keys').then(d => setKeys(d.data || [])).catch(() => {});
  }, []);
  useEffect(refresh, [refresh]);

  async function createKey(name, rpm) {
    const data = await PrismAPI.post('/account/api-keys', { name, rate_limit_rpm: rpm });
    setCreatedKey(data);
    setCreating(false);
    refresh();
  }

  async function revoke(id) {
    if (!confirm(t('console.keys.confirm_revoke'))) return;
    await PrismAPI.delete(`/account/api-keys/${id}`);
    refresh();
  }

  return (
    <>
      <div className="cs-row-between" style={{marginBottom: 16}}>
        <p style={{color: 'var(--text-muted)', fontSize: 13, margin: 0}}>
          {t('console.keys.intro')}
        </p>
        <button className="cs-btn cs-btn-primary" onClick={() => setCreating(true)}>{t('keys.create_btn')}</button>
      </div>

      {keys && keys.length === 0 ? (
        <div className="cs-empty">{t('console.keys.empty')}</div>
      ) : keys && (
        <table className="cs-table">
          <thead>
            <tr>
              <th>{t('console.col.name')}</th>
              <th>{t('console.keys.col.prefix')}</th>
              <th>{t('console.keys.col.rpm')}</th>
              <th>{t('console.col.status')}</th>
              <th>{t('console.keys.col.last_used')}</th>
              <th>{t('console.col.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {keys.map(k => (
              <tr key={k.id}>
                <td>{k.name || '-'}</td>
                <td className="mono">{k.prefix}…{k.last4}</td>
                <td className="mono">{k.rate_limit_rpm || t('console.keys.rpm_default')}</td>
                <td>
                  {k.enabled
                    ? <span className="cs-pill cs-pill-ok">enabled</span>
                    : <span className="cs-pill cs-pill-err">revoked</span>}
                </td>
                <td className="mono" style={{fontSize: 11, color: 'var(--text-muted)'}}>
                  {k.last_used_at?.slice(0, 19) || t('console.keys.never_used')}
                </td>
                <td>
                  {k.enabled && (
                    <button className="cs-btn cs-btn-danger" onClick={() => revoke(k.id)}>{t('keys.revoke')}</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {creating && <CreateKeyModal onClose={() => setCreating(false)} onCreate={createKey}/>}
      {createdKey && <CreatedKeyModal data={createdKey} onClose={() => setCreatedKey(null)}/>}
    </>
  );
}

function CreateKeyModal({ onClose, onCreate }) {
  const [name, setName] = useState('');
  const [rpm, setRpm] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    try {
      await onCreate(name || null, rpm ? parseInt(rpm) : null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="cs-modal-overlay" onClick={onClose}>
      <div className="cs-modal" onClick={e => e.stopPropagation()}>
        <h3>{t('keys.modal_title')}</h3>
        <div style={{marginBottom: 12}}>
          <label className="auth-label">{t('keys.name_label')}</label>
          <input className="auth-input" value={name} onChange={e => setName(e.target.value)}
            placeholder={t('console.keys.modal.name_ph')} style={{width: '100%', boxSizing: 'border-box'}}/>
        </div>
        <div>
          <label className="auth-label">{t('console.keys.modal.rpm_label')}</label>
          <input className="auth-input" type="number" min={1} value={rpm}
            onChange={e => setRpm(e.target.value)} placeholder="600"
            style={{width: '100%', boxSizing: 'border-box'}}/>
        </div>
        <div className="cs-modal-actions">
          <button className="cs-btn" onClick={onClose} disabled={busy}>{t('keys.cancel')}</button>
          <button className="cs-btn cs-btn-primary" onClick={submit} disabled={busy}>
            {busy ? t('console.keys.modal.creating') : t('keys.create')}
          </button>
        </div>
      </div>
    </div>
  );
}

function CreatedKeyModal({ data, onClose }) {
  const [copied, setCopied] = useState(false);
  function copy() {
    navigator.clipboard?.writeText(data.key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }
  return (
    <div className="cs-modal-overlay">
      <div className="cs-modal">
        <h3>{t('console.keys.created.title')}</h3>
        <p style={{color: 'var(--text-muted)', fontSize: 13}}
           dangerouslySetInnerHTML={{ __html: t('console.keys.created.body') }}/>
        <div className="cs-key-display">
          <span style={{flex: 1}}>{data.key}</span>
          <button className="cs-btn" onClick={copy}>{copied ? t('console.keys.created.copied') : t('keys.copy')}</button>
        </div>
        <p style={{color: 'var(--text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)'}}>
          # Claude Code:<br/>
          export ANTHROPIC_BASE_URL=https://www.ai100trading.cn/suanli-api<br/>
          export ANTHROPIC_AUTH_TOKEN={data.key.slice(0, 14)}…<br/>
          <br/>
          # OpenAI SDK / Cursor:<br/>
          base_url=https://www.ai100trading.cn/suanli-api/v1<br/>
          api_key={data.key.slice(0, 14)}…
        </p>
        <div className="cs-modal-actions">
          <button className="cs-btn cs-btn-primary" onClick={onClose}>{t('console.keys.created.saved')}</button>
        </div>
      </div>
    </div>
  );
}

/* ─── Usage ──────────────────────────────────────────────────────────────── */

function Usage() {
  // ── Filter state ──────────────────────────────────────────────────────────
  // Defaults: last 7 days, all models, all statuses
  const today = new Date();
  const todayStr = today.toISOString().slice(0, 10);
  const weekAgo = new Date(today.getTime() - 7 * 86400000).toISOString().slice(0, 10);

  const [filters, setFilters] = useState({
    since: weekAgo,
    until: todayStr,
    model: '',
    status: '',
  });

  // ── Aggregate group-by tab ────────────────────────────────────────────────
  const [groupBy, setGroupBy] = useState('model');
  const [expanded, setExpanded] = useState(null);  // channel id whose row is open

  // ── Pagination state for the detail log ───────────────────────────────────
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  // ── Data ──────────────────────────────────────────────────────────────────
  const [stats, setStats] = useState(null);
  const [requests, setRequests] = useState({ data: [], total: 0, pages: 0 });
  const [models, setModels] = useState([]);          // for the dropdown
  const [detail, setDetail] = useState(null);
  const [loadingPage, setLoadingPage] = useState(false);

  // Build query string from current filters
  const buildParams = (extra = {}) => {
    const p = new URLSearchParams();
    if (filters.since) p.set('since', new Date(filters.since + 'T00:00:00Z').toISOString());
    if (filters.until) p.set('until', new Date(filters.until + 'T23:59:59Z').toISOString());
    if (filters.model) p.set('model', filters.model);
    if (filters.status) p.set('status', filters.status);
    Object.entries(extra).forEach(([k, v]) => p.set(k, v));
    return p.toString();
  };

  // ── Fetch effects ─────────────────────────────────────────────────────────
  useEffect(() => {
    PrismAPI.get(`/usage/stats?${buildParams({ group_by: groupBy })}`)
      .then(setStats).catch(() => {});
  }, [groupBy, filters.since, filters.until, filters.model, filters.status]);

  useEffect(() => {
    setLoadingPage(true);
    PrismAPI.get(`/usage/requests?${buildParams({ page, size: pageSize })}`)
      .then(setRequests)
      .catch(() => setRequests({ data: [], total: 0, pages: 0 }))
      .finally(() => setLoadingPage(false));
  }, [page, pageSize, filters.since, filters.until, filters.model, filters.status]);

  useEffect(() => {
    PrismAPI.get('/usage/models').then(d => setModels(d.data || [])).catch(() => {});
  }, []);

  // Reset to page 1 when filters change
  useEffect(() => { setPage(1); }, [filters.since, filters.until, filters.model, filters.status]);

  // Hash deep link: /console#usage/{request_id}
  useEffect(() => {
    const handler = () => {
      const m = location.hash.match(/^#usage\/([\w-]+)$/);
      if (m) PrismAPI.get(`/usage/requests/${m[1]}`).then(setDetail);
      else setDetail(null);
    };
    handler();
    window.addEventListener('hashchange', handler);
    return () => window.removeEventListener('hashchange', handler);
  }, []);

  // ── Derived ───────────────────────────────────────────────────────────────
  const summary = stats?.summary || {};
  const aggData = stats?.data || [];
  const total = requests.total || 0;
  const pages = requests.pages || 0;
  const fromN = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const toN   = Math.min(page * pageSize, total);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <>
      {/* Filter bar */}
      <div className="cs-filter-bar">
        <div>
          <label className="cs-filter-label">{t('usage.filter.since')}</label>
          <input className="cs-input cs-input-date" type="date"
            value={filters.since}
            onChange={e => setFilters({...filters, since: e.target.value})}/>
        </div>
        <div>
          <label className="cs-filter-label">{t('usage.filter.until')}</label>
          <input className="cs-input cs-input-date" type="date"
            value={filters.until}
            onChange={e => setFilters({...filters, until: e.target.value})}/>
        </div>
        <div>
          <label className="cs-filter-label">{t('usage.filter.model')}</label>
          <select className="cs-input"
            value={filters.model}
            onChange={e => setFilters({...filters, model: e.target.value})}>
            <option value="">{t('usage.filter.all_models')}</option>
            {models.map(m => (
              <option key={m.model_id} value={m.model_id}>
                {m.model_id} ({m.requests})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="cs-filter-label">{t('usage.filter.status')}</label>
          <select className="cs-input"
            value={filters.status}
            onChange={e => setFilters({...filters, status: e.target.value})}>
            <option value="">{t('usage.filter.all_status')}</option>
            <option value="ok">ok</option>
            <option value="error">error</option>
            <option value="partial">partial</option>
            <option value="cancelled">cancelled</option>
          </select>
        </div>
        <div style={{alignSelf: 'flex-end'}}>
          <button className="cs-btn"
            onClick={() => setFilters({since: weekAgo, until: todayStr, model: '', status: ''})}>
            {t('usage.filter.reset')}
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="cs-summary-cards">
        <Metric label={t('usage.summary.requests')} value={fmtCompact(summary.total_requests || 0)}
                meta={t('usage.summary.range')} icon="zap" accent="cyan"/>
        <Metric label={t('usage.summary.input')} value={fmtCompact(summary.total_input_tokens || 0)}
                icon="arrowDown" accent="purple"/>
        <Metric label={t('usage.summary.output')} value={fmtCompact(summary.total_output_tokens || 0)}
                icon="arrowUp" accent="magenta"/>
        <Metric label={t('usage.summary.cost')} value={fmtUSD(summary.total_cost_usd || 0)}
                meta={t('usage.summary.zeromarkup')} icon="dollar" accent="green"/>
      </div>

      {/* Aggregate section */}
      <section className="cs-section">
        <div className="cs-section-head">
          <h2>{t('usage.agg.title')}</h2>
          <div className="cs-row" style={{gap: 6}}>
            <span style={{fontSize: 12, color: 'var(--text-muted)', marginRight: 6}}>{t('usage.agg.group_label')}</span>
            {[
              {id: 'model',   labelKey: 'usage.agg.by_model'},
              {id: 'channel', labelKey: 'usage.agg.by_channel'},
              {id: 'day',     labelKey: 'usage.agg.by_day'},
              {id: 'key',     labelKey: 'usage.agg.by_key'},
            ].map(g => (
              <button key={g.id}
                className={`cs-btn ${groupBy === g.id ? 'cs-btn-primary' : ''}`}
                onClick={() => { setGroupBy(g.id); setExpanded(null); }}
                style={{fontSize: 12, padding: '6px 12px'}}>
                {t(g.labelKey)}
              </button>
            ))}
          </div>
        </div>

        {aggData.length === 0 ? (
          <div className="cs-empty">{t('usage.agg.empty')}</div>
        ) : (
          <table className="cs-table">
            <thead>
              <tr>
                <th>{groupByLabel(groupBy)}</th>
                <th>{t('usage.agg.col.requests')}</th>
                <th>{t('usage.agg.col.input')}</th>
                <th>{t('usage.agg.col.output')}</th>
                <th>{t('usage.agg.col.cost')}</th>
                <th>{t('usage.agg.col.avg_lat')}</th>
              </tr>
            </thead>
            <tbody>
              {aggData.map((r, i) => {
                const isChannel = groupBy === 'channel';
                const childKey = parseInt(r.bucket || '0', 10);
                const isOpen = isChannel && expanded === childKey;
                const expandable = isChannel && (r.models || []).length > 0;
                const display = isChannel
                  ? (r.channel_name ? `${r.channel_name} (#${r.bucket})` : t('usage.agg.unrouted'))
                  : (r.bucket || '-');
                return (
                  <React.Fragment key={i}>
                    <tr
                      className={expandable ? 'cs-row-expandable' : ''}
                      onClick={expandable ? () => setExpanded(isOpen ? null : childKey) : undefined}
                      style={expandable ? {cursor: 'pointer'} : undefined}
                    >
                      <td>
                        {expandable && (
                          <span style={{display: 'inline-block', width: 14, color: 'var(--text-muted)'}}>
                            {isOpen ? '▾' : '▸'}
                          </span>
                        )}
                        {groupBy === 'model'
                          ? <ModelCell modelId={display}/>
                          : <span className="mono">{display}</span>}
                      </td>
                      <td>{fmtCompact(r.requests)}</td>
                      <td className="mono">{fmtCompact(r.input_tokens)}</td>
                      <td className="mono">{fmtCompact(r.output_tokens)}</td>
                      <td>{fmtUSD(r.cost_usd)}</td>
                      <td className="mono">{r.avg_latency_ms ? r.avg_latency_ms + 'ms' : '-'}</td>
                    </tr>
                    {isOpen && (r.models || []).map(m => (
                      <tr key={`${i}:${m.model_id}`} className="cs-row-child">
                        <td style={{paddingLeft: 36}}>
                          <span style={{color: 'var(--text-muted)', marginRight: 6}}>↳</span>
                          <ModelCell modelId={m.model_id}/>
                        </td>
                        <td>{fmtCompact(m.requests)}</td>
                        <td className="mono">{fmtCompact(m.input_tokens)}</td>
                        <td className="mono">{fmtCompact(m.output_tokens)}</td>
                        <td>{fmtUSD(m.cost_usd)}</td>
                        <td>—</td>
                      </tr>
                    ))}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </section>

      {/* Detail log section */}
      <section className="cs-section">
        <div className="cs-section-head">
          <h2>{t('usage.detail.title')}</h2>
          <div className="cs-page-ctrl">
            <span className="mono cs-page-info">
              {total === 0 ? t('usage.detail.zero') : t('usage.detail.range', { from: fromN, to: toN, total })}
            </span>
            <select className="cs-input"
              value={pageSize}
              onChange={e => { setPageSize(Number(e.target.value)); setPage(1); }}
              style={{width: 110}}>
              <option value={25}>{t('usage.detail.per_page', { n: 25 })}</option>
              <option value={50}>{t('usage.detail.per_page', { n: 50 })}</option>
              <option value={100}>{t('usage.detail.per_page', { n: 100 })}</option>
            </select>
            <button className="cs-btn" disabled={page <= 1 || loadingPage}
              onClick={() => setPage(p => Math.max(1, p - 1))}>{t('usage.detail.prev')}</button>
            <span className="mono cs-page-info">
              {pages > 0 ? `${page} / ${pages}` : '-'}
            </span>
            <button className="cs-btn" disabled={page >= pages || loadingPage}
              onClick={() => setPage(p => Math.min(pages, p + 1))}>{t('usage.detail.next')}</button>
          </div>
        </div>

        {requests.data.length === 0 ? (
          <div className="cs-empty">{t('usage.detail.empty')}</div>
        ) : (
          <table className="cs-table">
            <thead>
              <tr>
                <th>{t('console.col.time')}</th>
                <th>{t('console.col.model')}</th>
                <th>{t('console.col.status')}</th>
                <th>{t('usage.detail.col.input')}</th>
                <th>{t('usage.detail.col.output')}</th>
                <th>{t('console.col.latency')}</th>
                <th>{t('console.col.cost')}</th>
                <th>{t('console.col.detail')}</th>
              </tr>
            </thead>
            <tbody>
              {requests.data.map(r => (
                <tr key={r.request_id}>
                  <td className="mono" style={{fontSize: 11}}>{r.created_at?.slice(0, 19).replace('T', ' ')}</td>
                  <td><ModelCell modelId={r.model_id}/></td>
                  <td><StatusPill status={r.status}/></td>
                  <td className="mono">{fmtCompact(r.tokens.prompt)}</td>
                  <td className="mono">{fmtCompact(r.tokens.completion)}</td>
                  <td className="mono">{r.latency_ms ? r.latency_ms + 'ms' : '-'}</td>
                  <td>{fmtUSD(r.cost_usd)}</td>
                  <td><a href={`#usage/${r.request_id}`} className="cs-btn" style={{padding: '4px 10px'}}>{t('console.view')}</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {detail && <RequestDetailModal d={detail} onClose={() => location.hash = '#usage'}/>}
    </>
  );
}

function groupByLabel(g) {
  return ({
    model:   t('usage.agg.label.model'),
    channel: t('usage.agg.label.channel'),
    day:     t('usage.agg.label.day'),
    key:     t('usage.agg.label.key'),
  })[g] || g;
}

function RequestDetailModal({ d, onClose }) {
  const ch = d.routing?.served_by_channel;
  return (
    <div className="cs-modal-overlay" onClick={onClose}>
      <div className="cs-modal" onClick={e => e.stopPropagation()} style={{minWidth: 600}}>
        <h3>{t('usage.modal.title')}</h3>
        <div style={{display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 14px', fontSize: 13}}>
          <span style={{color: 'var(--text-muted)'}}>{t('usage.modal.req_id')}</span>
          <span className="mono">{d.request_id}</span>
          <span style={{color: 'var(--text-muted)'}}>{t('console.col.model')}</span>
          <span>{d.model_id}</span>
          <span style={{color: 'var(--text-muted)'}}>{t('console.col.status')}</span>
          <span><StatusPill status={d.status}/></span>
          <span style={{color: 'var(--text-muted)'}}>{t('console.col.time')}</span>
          <span className="mono">{d.created_at}</span>
          <span style={{color: 'var(--text-muted)'}}>{t('usage.modal.streaming')}</span>
          <span>{d.is_streaming ? t('usage.modal.yes') : t('usage.modal.no')}</span>
        </div>

        <h4 style={{margin: '20px 0 10px', fontFamily: 'var(--font-display)'}}>
          {t('usage.modal.channel_section')}
        </h4>
        {ch ? (
          <div className="cs-channel-card">
            <div className="cs-channel-name">{ch.name}</div>
            <div className="cs-channel-meta">
              <span>provider: <strong>{ch.provider}</strong></span>
              {ch.region && <span>region: <strong>{ch.region}</strong></span>}
            </div>
            <div className="cs-channel-meta">
              <span>{ch.policy.no_training ? t('usage.modal.no_training') : t('usage.modal.may_train')}</span>
              <span>{t('usage.modal.log_retention', { days: ch.policy.log_retention_days || '?' })}</span>
            </div>
          </div>
        ) : (
          <div className="cs-empty" style={{padding: 20}}>{t('usage.modal.no_upstream')}</div>
        )}

        {d.routing?.tried_channels?.length > 1 && (
          <>
            <h4 style={{margin: '20px 0 10px', fontFamily: 'var(--font-display)'}}>{t('usage.modal.retry_history')}</h4>
            <table className="cs-table">
              <thead>
                <tr><th>{t('usage.modal.col.order')}</th><th>Channel ID</th><th>{t('usage.modal.col.http')}</th><th>{t('usage.modal.col.result')}</th></tr>
              </thead>
              <tbody>
                {d.routing.tried_channels.map((tc, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td className="mono">{tc.channel_id}</td>
                    <td className="mono">{tc.status || '-'}</td>
                    <td className="mono" style={{fontSize: 11}}>{tc.error?.slice(0, 80) || 'ok'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        <h4 style={{margin: '20px 0 10px', fontFamily: 'var(--font-display)'}}>{t('usage.modal.tok_section')}</h4>
        <table className="cs-table">
          <tbody>
            <tr><td>Input (prompt)</td><td className="mono">{d.tokens.prompt.toLocaleString()}</td></tr>
            <tr><td>Output (completion)</td><td className="mono">{d.tokens.completion.toLocaleString()}</td></tr>
            {d.tokens.cache_read > 0 && <tr><td>Cache read</td><td className="mono">{d.tokens.cache_read.toLocaleString()}</td></tr>}
            {d.tokens.cache_write > 0 && <tr><td>Cache write</td><td className="mono">{d.tokens.cache_write.toLocaleString()}</td></tr>}
            {d.tokens.reasoning > 0 && <tr><td>Reasoning</td><td className="mono">{d.tokens.reasoning.toLocaleString()}</td></tr>}
            <tr><td><strong>{t('usage.modal.cost_label')}</strong></td><td className="mono"><strong>{fmtUSD(d.cost_usd)}</strong></td></tr>
          </tbody>
        </table>

        {d.error_message && (
          <div className="auth-error" style={{marginTop: 16}}>{d.error_message}</div>
        )}

        <div className="cs-modal-actions">
          <button className="cs-btn" onClick={onClose}>{t('usage.modal.close')}</button>
        </div>
      </div>
    </div>
  );
}

/* ─── Billing ────────────────────────────────────────────────────────────── */

// Channel keys keep `usdt-*` internally for DB CHECK constraint compatibility.
// Display labels show USDC — that's what we actually accept now.
const USDT_CHANNELS = [
  { key: 'usdt-trc20', title: 'USDC (TRC20)', enKey: 'pay.usdc.trc.tag',
    noteKey: 'pay.usdc.trc.warn',     icon: 'diamond', accent: '#2775CA' },
  { key: 'usdt-sol',   title: 'USDC (Solana)', enKey: 'pay.usdc.sol.tag',
    noteKey: 'pay.usdc.sol.warn',       icon: 'circle',  accent: '#2775CA' },
  { key: 'usdt-evm',   title: 'USDC (EVM)', enKey: 'pay.usdc.evm.tag',
    noteKey: 'pay.usdc.evm.warn',     icon: 'hexagon', accent: '#2775CA' },
];

function Billing({ me }) {
  const [topups, setTopups] = useState([]);
  const [activeIntent, setActiveIntent] = useState(null);  // intent payload from /topup-intent
  const [loadingChannel, setLoadingChannel] = useState(null);

  const refresh = useCallback(() => {
    PrismAPI.get('/account/topups').then(d => setTopups(d.data || [])).catch(() => {});
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  async function startUSDT(channel, amount_usd) {
    setLoadingChannel(channel);
    try {
      const data = await PrismAPI.post('/account/topup-intent', { channel, amount_usd });
      setActiveIntent(data);
      refresh();
    } catch (err) {
      alert(t('billing.usdt.create_failed') + (err.message || ''));
    } finally {
      setLoadingChannel(null);
    }
  }

  return (
    <>
      <div className="cs-metrics">
        <Metric label={t('console.metric.usd_wallet')} value={fmtUSD(me.balance_usd)}
          meta={t('console.metric.usd_meta', { usd: fmtUSD(me.total_topped_up_usd) }).split(' · ')[0]}
          icon="dollar" accent="green"/>
        <Metric label={t('console.metric.cny_wallet')} value={`¥${(me.balance_cny ?? 0).toFixed(2)}`}
          meta={t('console.metric.cny_meta', { cny: `¥${(me.total_topped_up_cny ?? 0).toFixed(2)}` }).split(' · ')[0]}
          icon="zap" accent="magenta"/>
        <Metric label={t('billing.metric.fee')} value="1.5%" meta="cost = price"/>
        <Metric label={t('billing.metric.fx')} value="6.5 / 7.0"
          meta={t('billing.metric.fx_meta')}/>
      </div>

      <section className="cs-section">
        <h2>{t('billing.usd.title')}</h2>
        <p style={{color: 'var(--text-muted)', fontSize: 13, marginBottom: 16}}>
          {t('billing.usd.intro')}
        </p>
        <div className="cs-pay-grid">
          {USDT_CHANNELS.map(ch => (
            <UsdtCard key={ch.key} channel={ch}
              onStart={(amt) => startUSDT(ch.key, amt)}
              loading={loadingChannel === ch.key}/>
          ))}
        </div>
      </section>

      <section className="cs-section">
        <h2>{t('billing.cny.title')}</h2>
        <p style={{color: 'var(--text-muted)', fontSize: 13, marginBottom: 16}}>
          {t('billing.cny.intro', { email: me.email, ops: 'ops@ai100trading.cn' })}
        </p>
        <div className="cs-pay-grid">
          <DomesticPayCard
            titleKey="pay.alipay.title" en={t('billing.alipay.label')}
            qrUrl="/suanli/qr-alipay.jpg"
            tone="alipay"/>
          <DomesticPayCard
            titleKey="pay.wechat.title" en={t('billing.wechat.label')}
            qrUrl="/suanli/qr-wechat.jpg"
            tone="wechat"/>
        </div>
      </section>

      <section className="cs-section">
        <h2>{t('billing.history.title')}</h2>
        {topups.length === 0 ? (
          <div className="cs-empty">{t('billing.history.empty')}</div>
        ) : (
          <table className="cs-table">
            <thead>
              <tr>
                <th>{t('console.col.time')}</th>
                <th>{t('billing.history.col.channel')}</th>
                <th>{t('billing.history.col.amount')}</th>
                <th>{t('billing.history.col.fee')}</th>
                <th>{t('billing.history.col.credited')}</th>
                <th>{t('console.col.status')}</th>
                <th>memo</th>
                <th>{t('billing.history.col.tx')}</th>
              </tr>
            </thead>
            <tbody>
              {topups.map(t => (
                <tr key={t.id}>
                  <td className="mono" style={{fontSize: 11}}>{t.created_at?.slice(0, 19)}</td>
                  <td className="mono">{t.channel}</td>
                  <td>{fmtUSD(t.amount_usd)}</td>
                  <td className="mono">{fmtUSD(t.fee_usd)}</td>
                  <td>{fmtUSD(t.credited_usd)}</td>
                  <td><StatusPill status={t.status === 'paid' ? 'ok' : t.status}/></td>
                  <td className="mono" style={{fontSize: 11}}>{t.memo || '-'}</td>
                  <td className="mono" style={{fontSize: 11}}>{t.external_ref?.slice(0, 14) || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {activeIntent && (
        <UsdtIntentModal
          intent={activeIntent}
          onClose={() => { setActiveIntent(null); refresh(); }}
          onPaid={() => { setActiveIntent(null); refresh(); }}/>
      )}
    </>
  );
}

function UsdtCard({ channel, onStart, loading }) {
  const [amount, setAmount] = useState(50);
  const fee = (amount * 0.015).toFixed(2);
  const credited = (amount - amount * 0.015).toFixed(2);
  return (
    <div className="cs-pay-card" style={{borderColor: channel.accent + '40'}}>
      <div className="cs-pay-card-head">
        <span className="cs-pay-icon" style={{
          background: channel.accent + '14',
          color: channel.accent,
          borderColor: channel.accent + '33',
        }}>
          <Icon name={channel.icon} size={20}/>
        </span>
        <div>
          <div className="cs-pay-card-title">{channel.title}</div>
          <div className="cs-pay-card-en mono">{t(channel.enKey)}</div>
        </div>
      </div>
      <div className="cs-pay-card-note mono">{t(channel.noteKey)}</div>

      <label className="cs-label" style={{marginTop: 12}}>{t('billing.usdt.amount_label')}</label>
      <div style={{display: 'flex', gap: 8}}>
        <input className="cs-input" type="number" min={5} max={100000} step={1}
          value={amount} onChange={e => setAmount(Number(e.target.value))}/>
        <button
          className="cs-btn cs-btn-primary"
          disabled={loading || amount < 5}
          onClick={() => onStart(amount)}>
          {loading ? t('billing.usdt.generating') : t('billing.usdt.go')}
        </button>
      </div>
      <div className="cs-pay-card-foot mono">
        {t('billing.usdt.foot', { fee, credited })}
      </div>
    </div>
  );
}

function UsdtIntentModal({ intent, onClose, onPaid }) {
  const [now, setNow] = useState(Date.now());
  const [status, setStatus] = useState(intent.status || 'pending');

  // Tick every second for countdown
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  // Poll topups every 8s; if our intent flipped to 'paid', notify
  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const d = await PrismAPI.get('/account/topups');
        const mine = (d.data || []).find(t => t.id === intent.id);
        if (mine && mine.status === 'paid') {
          setStatus('paid');
          clearInterval(poll);
          setTimeout(() => onPaid(), 2000);
        }
      } catch {}
    }, 8000);
    return () => clearInterval(poll);
  }, [intent.id, onPaid]);

  const expiresAt = intent.expires_at ? new Date(intent.expires_at).getTime() : 0;
  const remainSec = Math.max(0, Math.floor((expiresAt - now) / 1000));
  const mins = Math.floor(remainSec / 60);
  const secs = String(remainSec % 60).padStart(2, '0');

  const copyAddr = () => navigator.clipboard?.writeText(intent.address);
  const copyAmt = () => navigator.clipboard?.writeText(String(intent.expected_amount_usd));

  return (
    <div className="cs-modal-overlay" onClick={onClose}>
      <div className="cs-modal" onClick={e => e.stopPropagation()}
        style={{maxWidth: 560}}>
        <h2 style={{marginTop: 0}}>
          {status === 'paid' ? t('billing.intent.paid_title') : t('billing.intent.title', { ch: intent.channel.toUpperCase() })}
        </h2>

        {status !== 'paid' && (
          <>
            <div className="cs-pay-banner mono"
                 dangerouslySetInnerHTML={{ __html: t('billing.intent.banner', {
                   amt: intent.expected_amount_usd,
                   min: mins,
                   sec: secs,
                   net: intent.network ? t('billing.intent.network', { net: intent.network.toUpperCase() }) : '',
                 }) }}/>

            <label className="cs-label">{t('billing.intent.addr')}</label>
            <div className="cs-pay-row">
              <code className="cs-pay-addr mono">{intent.address}</code>
              <button className="cs-btn" onClick={copyAddr}>{t('billing.intent.copy_addr')}</button>
            </div>

            <label className="cs-label" style={{marginTop: 12}}>
              {t('billing.intent.amt')}
            </label>
            <div className="cs-pay-row">
              <code className="cs-pay-addr mono" style={{fontSize: 18, color: 'var(--accent-amber)'}}>
                ${intent.expected_amount_usd} USDC
              </code>
              <button className="cs-btn" onClick={copyAmt}>{t('billing.intent.copy_amt')}</button>
            </div>

            <div className="cs-pay-warn mono"
                 dangerouslySetInnerHTML={{ __html: t('billing.intent.warn', { memo: intent.memo }) }}/>

            <div style={{marginTop: 16, fontSize: 13, color: 'var(--text-muted)'}}>
              {t('billing.intent.tail')}
            </div>
          </>
        )}

        {status === 'paid' && (
          <div className="cs-pay-success">
            <p dangerouslySetInnerHTML={{ __html: t('billing.intent.success_amt', { amt: intent.credited_usd }) }}/>
            <p>{t('billing.intent.refresh')}</p>
          </div>
        )}

        <div className="cs-modal-actions">
          <button className="cs-btn" onClick={onClose}>{t('usage.modal.close')}</button>
        </div>
      </div>
    </div>
  );
}

function DomesticPayCard({ titleKey, en, qrUrl, tone }) {
  const [imgError, setImgError] = useState(false);
  const title = t(titleKey);
  return (
    <div className={`cs-pay-card cs-pay-card-${tone}`}>
      <div className="cs-pay-card-head">
        <div>
          <div className="cs-pay-card-title">{title}</div>
          <div className="cs-pay-card-en mono">{en}</div>
        </div>
      </div>
      <div className="cs-qr-box">
        {imgError ? (
          <div className="cs-qr-placeholder mono">
            {t('billing.qr.placeholder', { file: qrUrl.split('/').pop() })}
          </div>
        ) : (
          <img src={qrUrl} alt={title} className="cs-qr-img"
            onError={() => setImgError(true)}/>
        )}
      </div>
      <div className="cs-pay-card-foot mono">
        {t('billing.qr.foot')}
      </div>
    </div>
  );
}

/* ─── Settings ───────────────────────────────────────────────────────────── */

function Settings({ me, setMe }) {
  const [name, setName] = useState(me.display_name || '');
  const [oldPwd, setOldPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [msg, setMsg] = useState('');

  async function saveProfile(e) {
    e.preventDefault();
    setMsg('');
    try {
      const updated = await PrismAPI.patch('/account/me', { display_name: name });
      setMe(updated);
      setMsg(t('settings.saved_ok'));
    } catch (err) {
      setMsg('✗ ' + err.message);
    }
  }

  async function changePwd(e) {
    e.preventDefault();
    setMsg('');
    try {
      await PrismAPI.post('/auth/change-password', { old_password: oldPwd, new_password: newPwd });
      setMsg(t('settings.pwd_changed'));
      setOldPwd(''); setNewPwd('');
    } catch (err) {
      setMsg('✗ ' + err.message);
    }
  }

  return (
    <>
      <section className="cs-section">
        <h2>{t('settings.profile.title')}</h2>
        <form onSubmit={saveProfile} style={{maxWidth: 480}}>
          <label className="auth-label">{t('settings.display_name')}</label>
          <input className="auth-input" value={name} onChange={e => setName(e.target.value)}
            style={{width: '100%', boxSizing: 'border-box'}}/>
          <button className="cs-btn cs-btn-primary" type="submit">{t('settings.save')}</button>
        </form>
      </section>

      <section className="cs-section">
        <h2>{t('settings.changepwd.title')}</h2>
        <form onSubmit={changePwd} style={{maxWidth: 480}}>
          <label className="auth-label">{t('settings.current_pwd')}</label>
          <input className="auth-input" type="password" required value={oldPwd}
            onChange={e => setOldPwd(e.target.value)}
            style={{width: '100%', boxSizing: 'border-box'}}/>
          <label className="auth-label">{t('settings.new_pwd')}</label>
          <input className="auth-input" type="password" required minLength={10} value={newPwd}
            onChange={e => setNewPwd(e.target.value)}
            style={{width: '100%', boxSizing: 'border-box'}}/>
          <button className="cs-btn cs-btn-primary" type="submit">{t('settings.changepwd_btn')}</button>
        </form>
      </section>

      {msg && <div className="auth-error" style={{
        background: msg.startsWith('✓') ? 'rgba(16,185,129,0.10)' : 'rgba(236,72,153,0.10)',
        borderColor: msg.startsWith('✓') ? 'rgba(16,185,129,0.3)' : 'rgba(236,72,153,0.3)',
        color: msg.startsWith('✓') ? 'var(--accent-green)' : '#f9a8d4',
      }}>{msg}</div>}
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<ConsoleApp/>);
