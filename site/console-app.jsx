/* Prism Console SPA — single hash-routed app with 5 tabs. */

const { useState, useEffect, useCallback } = React;

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
  copy:      '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  x:         '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  check:     '<polyline points="20 6 9 17 4 12"/>',
  chevronDown:  '<polyline points="6 9 12 15 18 9"/>',
  chevronRight: '<polyline points="9 18 15 12 9 6"/>',
  // Pay icons (for USDT cards — geometric shapes)
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
  { id: 'overview', label: '概览',     icon: 'home' },
  { id: 'keys',     label: 'API Keys', icon: 'key' },
  { id: 'usage',    label: '用量',     icon: 'chart' },
  { id: 'billing',  label: '充值',     icon: 'wallet' },
  { id: 'settings', label: '设置',     icon: 'settings' },
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
  if (!me) return <div className="cs-main"><div className="cs-empty">加载中…</div></div>;

  return (
    <div className="cs-shell">
      <aside className="cs-sidebar">
        <div className="cs-brand">
          <span className="cs-brand-mark">P</span>
          <span className="cs-brand-name">Prism</span>
        </div>
        {TABS.map(t => (
          <a key={t.id} href={`#${t.id}`}
             className={`cs-nav-link ${tab === t.id ? 'active' : ''}`}>
            <Icon name={t.icon}/>
            <span>{t.label}</span>
          </a>
        ))}
        <div className="cs-nav-foot">
          {me.email}
          <br/>
          <span className="mono" style={{fontSize: 11, color: 'var(--text-muted)'}}>tier: {me.tier}</span>
          <button className="cs-logout" onClick={logout}>退出登录 →</button>
        </div>
      </aside>

      <main className="cs-main">
        <div className="cs-page-header">
          <h1>{TABS.find(t => t.id === tab).label}</h1>
          <div className="cs-balance-pill">
            余额：<strong>{fmtUSD(me.balance_usd)}</strong>
            <a href="#billing" className="cs-btn cs-btn-primary" style={{padding: '4px 12px'}}>充值</a>
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
        <Metric label="当前余额" value={fmtUSD(me.balance_usd)} meta={`累计充值 ${fmtUSD(me.total_topped_up_usd)}`}/>
        <Metric label="本月调用" value={fmtCompact(totalRequests)} meta="近 30 天"/>
        <Metric label="本月成本" value={fmtUSD(totalCost)} meta="近 30 天"/>
        <Metric label="默认限速" value={`${me.default_rpm} RPM`} meta={`tier: ${me.tier}`}/>
      </div>

      <section className="cs-section">
        <h2>最近请求</h2>
        {recent.length === 0 ? (
          <div className="cs-empty">暂无请求记录。配置 API Key 后调用任一模型即出现。</div>
        ) : (
          <table className="cs-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>模型</th>
                <th>状态</th>
                <th>Tokens (in/out)</th>
                <th>成本</th>
                <th>延迟</th>
                <th>详情</th>
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
                    <a href={`#usage/${r.request_id}`} className="cs-btn" style={{padding: '4px 10px'}}>查看</a>
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
    if (!confirm('确定撤销该 Key？已使用此 Key 的客户端会立即失效。')) return;
    await PrismAPI.delete(`/account/api-keys/${id}`);
    refresh();
  }

  return (
    <>
      <div className="cs-row-between" style={{marginBottom: 16}}>
        <p style={{color: 'var(--text-muted)', fontSize: 13, margin: 0}}>
          Prism Key 是你接入 Claude Code / Cursor / Codex 等客户端的凭证。
        </p>
        <button className="cs-btn cs-btn-primary" onClick={() => setCreating(true)}>+ 新建 Key</button>
      </div>

      {keys && keys.length === 0 ? (
        <div className="cs-empty">还没创建过 Key。点上面"新建 Key"开始。</div>
      ) : keys && (
        <table className="cs-table">
          <thead>
            <tr>
              <th>名称</th>
              <th>前缀…后4</th>
              <th>限速 (RPM)</th>
              <th>状态</th>
              <th>最近使用</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {keys.map(k => (
              <tr key={k.id}>
                <td>{k.name || '-'}</td>
                <td className="mono">{k.prefix}…{k.last4}</td>
                <td className="mono">{k.rate_limit_rpm || '默认'}</td>
                <td>
                  {k.enabled
                    ? <span className="cs-pill cs-pill-ok">enabled</span>
                    : <span className="cs-pill cs-pill-err">revoked</span>}
                </td>
                <td className="mono" style={{fontSize: 11, color: 'var(--text-muted)'}}>
                  {k.last_used_at?.slice(0, 19) || '从未'}
                </td>
                <td>
                  {k.enabled && (
                    <button className="cs-btn cs-btn-danger" onClick={() => revoke(k.id)}>撤销</button>
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
        <h3>新建 API Key</h3>
        <div style={{marginBottom: 12}}>
          <label className="auth-label">名称（可选）</label>
          <input className="auth-input" value={name} onChange={e => setName(e.target.value)}
            placeholder="例如：MacBook Claude Code" style={{width: '100%', boxSizing: 'border-box'}}/>
        </div>
        <div>
          <label className="auth-label">RPM 限速（可选，留空用默认 tier 限速）</label>
          <input className="auth-input" type="number" min={1} value={rpm}
            onChange={e => setRpm(e.target.value)} placeholder="600"
            style={{width: '100%', boxSizing: 'border-box'}}/>
        </div>
        <div className="cs-modal-actions">
          <button className="cs-btn" onClick={onClose} disabled={busy}>取消</button>
          <button className="cs-btn cs-btn-primary" onClick={submit} disabled={busy}>
            {busy ? '创建中…' : '创建'}
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
        <h3>Key 已创建</h3>
        <p style={{color: 'var(--text-muted)', fontSize: 13}}>
          这是<strong>唯一一次</strong>显示完整 Key。立即复制并保存到安全的地方——
          关闭此窗口后只能看到前缀和后 4 位。
        </p>
        <div className="cs-key-display">
          <span style={{flex: 1}}>{data.key}</span>
          <button className="cs-btn" onClick={copy}>{copied ? '已复制' : '复制'}</button>
        </div>
        <p style={{color: 'var(--text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)'}}>
          # 接入 Claude Code:<br/>
          export ANTHROPIC_BASE_URL=https://www.ai100trading.cn/suanli-api<br/>
          export ANTHROPIC_AUTH_TOKEN={data.key.slice(0, 14)}…<br/>
          <br/>
          # 接入 OpenAI SDK / Cursor:<br/>
          base_url=https://www.ai100trading.cn/suanli-api/v1<br/>
          api_key={data.key.slice(0, 14)}…
        </p>
        <div className="cs-modal-actions">
          <button className="cs-btn cs-btn-primary" onClick={onClose}>我已保存</button>
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
          <label className="cs-filter-label">起始日期</label>
          <input className="cs-input cs-input-date" type="date"
            value={filters.since}
            onChange={e => setFilters({...filters, since: e.target.value})}/>
        </div>
        <div>
          <label className="cs-filter-label">结束日期</label>
          <input className="cs-input cs-input-date" type="date"
            value={filters.until}
            onChange={e => setFilters({...filters, until: e.target.value})}/>
        </div>
        <div>
          <label className="cs-filter-label">模型</label>
          <select className="cs-input"
            value={filters.model}
            onChange={e => setFilters({...filters, model: e.target.value})}>
            <option value="">全部模型</option>
            {models.map(m => (
              <option key={m.model_id} value={m.model_id}>
                {m.model_id} ({m.requests})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="cs-filter-label">状态</label>
          <select className="cs-input"
            value={filters.status}
            onChange={e => setFilters({...filters, status: e.target.value})}>
            <option value="">全部状态</option>
            <option value="ok">ok</option>
            <option value="error">error</option>
            <option value="partial">partial</option>
            <option value="cancelled">cancelled</option>
          </select>
        </div>
        <div style={{alignSelf: 'flex-end'}}>
          <button className="cs-btn"
            onClick={() => setFilters({since: weekAgo, until: todayStr, model: '', status: ''})}>
            重置
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="cs-summary-cards">
        <Metric label="请求数" value={fmtCompact(summary.total_requests || 0)}
                meta="该时间段" icon="zap" accent="cyan"/>
        <Metric label="输入 tokens" value={fmtCompact(summary.total_input_tokens || 0)}
                icon="arrowDown" accent="purple"/>
        <Metric label="输出 tokens" value={fmtCompact(summary.total_output_tokens || 0)}
                icon="arrowUp" accent="magenta"/>
        <Metric label="总成本" value={fmtUSD(summary.total_cost_usd || 0)}
                meta="cost = price · 0% 加价" icon="dollar" accent="green"/>
      </div>

      {/* Aggregate section */}
      <section className="cs-section">
        <div className="cs-section-head">
          <h2>汇总</h2>
          <div className="cs-row" style={{gap: 6}}>
            <span style={{fontSize: 12, color: 'var(--text-muted)', marginRight: 6}}>分组：</span>
            {[
              {id: 'model', label: '按模型'},
              {id: 'channel', label: '按渠道（可展开）'},
              {id: 'day', label: '按日期'},
              {id: 'key', label: '按 Key'},
            ].map(g => (
              <button key={g.id}
                className={`cs-btn ${groupBy === g.id ? 'cs-btn-primary' : ''}`}
                onClick={() => { setGroupBy(g.id); setExpanded(null); }}
                style={{fontSize: 12, padding: '6px 12px'}}>
                {g.label}
              </button>
            ))}
          </div>
        </div>

        {aggData.length === 0 ? (
          <div className="cs-empty">该时间段无请求数据</div>
        ) : (
          <table className="cs-table">
            <thead>
              <tr>
                <th>{groupByLabel(groupBy)}</th>
                <th>请求数</th>
                <th>输入 tokens</th>
                <th>输出 tokens</th>
                <th>成本 (USD)</th>
                <th>平均延迟</th>
              </tr>
            </thead>
            <tbody>
              {aggData.map((r, i) => {
                const isChannel = groupBy === 'channel';
                const childKey = parseInt(r.bucket || '0', 10);
                const isOpen = isChannel && expanded === childKey;
                const expandable = isChannel && (r.models || []).length > 0;
                const display = isChannel
                  ? (r.channel_name ? `${r.channel_name} (#${r.bucket})` : `(unrouted)`)
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
          <h2>请求明细</h2>
          <div className="cs-page-ctrl">
            <span className="mono cs-page-info">
              {total === 0 ? '0 条' : `${fromN}–${toN} / 共 ${total} 条`}
            </span>
            <select className="cs-input"
              value={pageSize}
              onChange={e => { setPageSize(Number(e.target.value)); setPage(1); }}
              style={{width: 90}}>
              <option value={25}>25 / 页</option>
              <option value={50}>50 / 页</option>
              <option value={100}>100 / 页</option>
            </select>
            <button className="cs-btn" disabled={page <= 1 || loadingPage}
              onClick={() => setPage(p => Math.max(1, p - 1))}>← 上一页</button>
            <span className="mono cs-page-info">
              {pages > 0 ? `${page} / ${pages}` : '-'}
            </span>
            <button className="cs-btn" disabled={page >= pages || loadingPage}
              onClick={() => setPage(p => Math.min(pages, p + 1))}>下一页 →</button>
          </div>
        </div>

        {requests.data.length === 0 ? (
          <div className="cs-empty">该时间段+筛选条件下无请求</div>
        ) : (
          <table className="cs-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>模型</th>
                <th>状态</th>
                <th>输入 tok</th>
                <th>输出 tok</th>
                <th>延迟</th>
                <th>成本</th>
                <th>详情</th>
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
                  <td><a href={`#usage/${r.request_id}`} className="cs-btn" style={{padding: '4px 10px'}}>查看</a></td>
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
  return ({model: '模型', channel: '渠道', day: '日期', key: 'API Key'})[g] || g;
}

function RequestDetailModal({ d, onClose }) {
  const ch = d.routing?.served_by_channel;
  return (
    <div className="cs-modal-overlay" onClick={onClose}>
      <div className="cs-modal" onClick={e => e.stopPropagation()} style={{minWidth: 600}}>
        <h3>请求详情</h3>
        <div style={{display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 14px', fontSize: 13}}>
          <span style={{color: 'var(--text-muted)'}}>请求 ID</span>
          <span className="mono">{d.request_id}</span>
          <span style={{color: 'var(--text-muted)'}}>模型</span>
          <span>{d.model_id}</span>
          <span style={{color: 'var(--text-muted)'}}>状态</span>
          <span><StatusPill status={d.status}/></span>
          <span style={{color: 'var(--text-muted)'}}>时间</span>
          <span className="mono">{d.created_at}</span>
          <span style={{color: 'var(--text-muted)'}}>流式</span>
          <span>{d.is_streaming ? '是' : '否'}</span>
        </div>

        <h4 style={{margin: '20px 0 10px', fontFamily: 'var(--font-display)'}}>
          🎯 渠道明牌（差异化）
        </h4>
        {ch ? (
          <div className="cs-channel-card">
            <div className="cs-channel-name">{ch.name}</div>
            <div className="cs-channel-meta">
              <span>provider: <strong>{ch.provider}</strong></span>
              {ch.region && <span>region: <strong>{ch.region}</strong></span>}
            </div>
            <div className="cs-channel-meta">
              <span>{ch.policy.no_training ? '✓ 不训练' : '⚠ 可能训练'}</span>
              <span>日志保留 {ch.policy.log_retention_days || '?'} 天</span>
            </div>
          </div>
        ) : (
          <div className="cs-empty" style={{padding: 20}}>请求未到达上游（错误或超时）</div>
        )}

        {d.routing?.tried_channels?.length > 1 && (
          <>
            <h4 style={{margin: '20px 0 10px', fontFamily: 'var(--font-display)'}}>重试历史</h4>
            <table className="cs-table">
              <thead>
                <tr><th>顺序</th><th>Channel ID</th><th>HTTP 状态</th><th>结果</th></tr>
              </thead>
              <tbody>
                {d.routing.tried_channels.map((t, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td className="mono">{t.channel_id}</td>
                    <td className="mono">{t.status || '-'}</td>
                    <td className="mono" style={{fontSize: 11}}>{t.error?.slice(0, 80) || 'ok'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        <h4 style={{margin: '20px 0 10px', fontFamily: 'var(--font-display)'}}>Token 分解</h4>
        <table className="cs-table">
          <tbody>
            <tr><td>Input (prompt)</td><td className="mono">{d.tokens.prompt.toLocaleString()}</td></tr>
            <tr><td>Output (completion)</td><td className="mono">{d.tokens.completion.toLocaleString()}</td></tr>
            {d.tokens.cache_read > 0 && <tr><td>Cache read</td><td className="mono">{d.tokens.cache_read.toLocaleString()}</td></tr>}
            {d.tokens.cache_write > 0 && <tr><td>Cache write</td><td className="mono">{d.tokens.cache_write.toLocaleString()}</td></tr>}
            {d.tokens.reasoning > 0 && <tr><td>Reasoning</td><td className="mono">{d.tokens.reasoning.toLocaleString()}</td></tr>}
            <tr><td><strong>成本</strong></td><td className="mono"><strong>{fmtUSD(d.cost_usd)}</strong></td></tr>
          </tbody>
        </table>

        {d.error_message && (
          <div className="auth-error" style={{marginTop: 16}}>{d.error_message}</div>
        )}

        <div className="cs-modal-actions">
          <button className="cs-btn" onClick={onClose}>关闭</button>
        </div>
      </div>
    </div>
  );
}

/* ─── Billing ────────────────────────────────────────────────────────────── */

const USDT_CHANNELS = [
  { key: 'usdt-trc20', title: 'USDT (TRC20)', en: 'Tron · 国内首选',
    note: '链上费 ≈ $1 · 推荐金额 ≥ $50',     icon: 'diamond', accent: '#DC2626' },
  { key: 'usdt-sol',   title: 'USDT (Solana)', en: 'SPL · 美区首选',
    note: '链上费 ≈ $0.001 · 任意金额',       icon: 'circle',  accent: '#7C3AED' },
  { key: 'usdt-evm',   title: 'USDT (EVM)', en: 'BSC / Polygon / Arbitrum / ETH',
    note: 'BSC 链上费 ≈ $0.3 · 推荐 BSC',     icon: 'hexagon', accent: '#0891B2' },
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
      alert('创建充值意向失败：' + (err.message || ''));
    } finally {
      setLoadingChannel(null);
    }
  }

  return (
    <>
      <div className="cs-metrics">
        <Metric label="当前余额" value={fmtUSD(me.balance_usd)}/>
        <Metric label="累计充值" value={fmtUSD(me.total_topped_up_usd)}/>
        <Metric label="手续费" value="0.05%" meta="万分之五"/>
        <Metric label="加价" value="0%" meta="cost = price"/>
      </div>

      <section className="cs-section">
        <h2>USDT 自动到账</h2>
        <p style={{color: 'var(--text-muted)', fontSize: 13, marginBottom: 16}}>
          点击任一通道生成专属充值地址 + 精确金额 · 链上扫到自动入账（30 秒内）·
          余额永不过期 · 万分之五手续费
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
        <h2>国内支付（人工核对）</h2>
        <p style={{color: 'var(--text-muted)', fontSize: 13, marginBottom: 16}}>
          扫码付款后请把支付截图 + 你的邮箱（<span className="mono">{me.email}</span>）
          发到运营邮箱 <span className="mono">ops@ai100trading.cn</span>，工作时间 1 小时内入账。
          v0.4 计划接入支付宝 PC / 微信 Native 接口实现自动到账。
        </p>
        <div className="cs-pay-grid">
          <DomesticPayCard
            title="支付宝" en="Alipay · 君 (**瑞)"
            qrUrl="/suanli/qr-alipay.jpg"
            tone="alipay"/>
          <DomesticPayCard
            title="微信支付" en="WeChat Pay · 六一学长 (**瑞)"
            qrUrl="/suanli/qr-wechat.jpg"
            tone="wechat"/>
        </div>
      </section>

      <section className="cs-section">
        <h2>充值记录</h2>
        {topups.length === 0 ? (
          <div className="cs-empty">还没充值记录。点上方按钮发起一笔充值。</div>
        ) : (
          <table className="cs-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>通道</th>
                <th>金额</th>
                <th>手续费</th>
                <th>实际到账</th>
                <th>状态</th>
                <th>memo</th>
                <th>tx hash</th>
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
          <div className="cs-pay-card-en mono">{channel.en}</div>
        </div>
      </div>
      <div className="cs-pay-card-note mono">{channel.note}</div>

      <label className="cs-label" style={{marginTop: 12}}>充值金额（USD）</label>
      <div style={{display: 'flex', gap: 8}}>
        <input className="cs-input" type="number" min={5} max={100000} step={1}
          value={amount} onChange={e => setAmount(Number(e.target.value))}/>
        <button
          className="cs-btn cs-btn-primary"
          disabled={loading || amount < 5}
          onClick={() => onStart(amount)}>
          {loading ? '生成中…' : '立即充值'}
        </button>
      </div>
      <div className="cs-pay-card-foot mono">
        最低 $5 · 约 ${(amount * 0.0005).toFixed(2)} 手续费 ·
        到账 ${(amount - amount * 0.0005).toFixed(2)}
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
          {status === 'paid' ? '✓ 已到账' : `${intent.channel.toUpperCase()} 充值`}
        </h2>

        {status !== 'paid' && (
          <>
            <div className="cs-pay-banner mono">
              请在 <strong>{mins}:{secs}</strong> 内向以下地址转账
              <strong> 精确金额 ${intent.expected_amount_usd}</strong>
              {intent.network ? ` · 网络: ${intent.network.toUpperCase()}` : ''}
            </div>

            <label className="cs-label">收款地址</label>
            <div className="cs-pay-row">
              <code className="cs-pay-addr mono">{intent.address}</code>
              <button className="cs-btn" onClick={copyAddr}>复制地址</button>
            </div>

            <label className="cs-label" style={{marginTop: 12}}>
              精确金额 · 必须分毫不差
            </label>
            <div className="cs-pay-row">
              <code className="cs-pay-addr mono" style={{fontSize: 18, color: 'var(--accent-amber)'}}>
                ${intent.expected_amount_usd} USDT
              </code>
              <button className="cs-btn" onClick={copyAmt}>复制金额</button>
            </div>

            <div className="cs-pay-warn mono">
              ⚠️ memo: <strong>{intent.memo}</strong> ·
              金额最后 4 位 µ¢ 用于识别你的充值 · 多了少了不到账
            </div>

            <div style={{marginTop: 16, fontSize: 13, color: 'var(--text-muted)'}}>
              转账后此页面 30 秒内自动检测到账 · 你也可以关掉此窗稍后回来看「充值记录」
            </div>
          </>
        )}

        {status === 'paid' && (
          <div className="cs-pay-success">
            <p>到账金额：<strong>${intent.credited_usd}</strong></p>
            <p>余额刷新中…</p>
          </div>
        )}

        <div className="cs-modal-actions">
          <button className="cs-btn" onClick={onClose}>关闭</button>
        </div>
      </div>
    </div>
  );
}

function DomesticPayCard({ title, en, qrUrl, tone }) {
  const [imgError, setImgError] = useState(false);
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
            （二维码待补 · {qrUrl.split('/').pop()}）
          </div>
        ) : (
          <img src={qrUrl} alt={`${title} 收款码`} className="cs-qr-img"
            onError={() => setImgError(true)}/>
        )}
      </div>
      <div className="cs-pay-card-foot mono">
        扫码付款后发支付截图 + 邮箱到 ops@ai100trading.cn
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
      setMsg('✓ 已保存');
    } catch (err) {
      setMsg('✗ ' + err.message);
    }
  }

  async function changePwd(e) {
    e.preventDefault();
    setMsg('');
    try {
      await PrismAPI.post('/auth/change-password', { old_password: oldPwd, new_password: newPwd });
      setMsg('✓ 密码已修改');
      setOldPwd(''); setNewPwd('');
    } catch (err) {
      setMsg('✗ ' + err.message);
    }
  }

  return (
    <>
      <section className="cs-section">
        <h2>个人资料</h2>
        <form onSubmit={saveProfile} style={{maxWidth: 480}}>
          <label className="auth-label">显示名（可选）</label>
          <input className="auth-input" value={name} onChange={e => setName(e.target.value)}
            style={{width: '100%', boxSizing: 'border-box'}}/>
          <button className="cs-btn cs-btn-primary" type="submit">保存</button>
        </form>
      </section>

      <section className="cs-section">
        <h2>修改密码</h2>
        <form onSubmit={changePwd} style={{maxWidth: 480}}>
          <label className="auth-label">当前密码</label>
          <input className="auth-input" type="password" required value={oldPwd}
            onChange={e => setOldPwd(e.target.value)}
            style={{width: '100%', boxSizing: 'border-box'}}/>
          <label className="auth-label">新密码（至少 10 位）</label>
          <input className="auth-input" type="password" required minLength={10} value={newPwd}
            onChange={e => setNewPwd(e.target.value)}
            style={{width: '100%', boxSizing: 'border-box'}}/>
          <button className="cs-btn cs-btn-primary" type="submit">修改密码</button>
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
