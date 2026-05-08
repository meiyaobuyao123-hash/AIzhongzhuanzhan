/* Prism Console SPA — single hash-routed app with 5 tabs. */

const { useState, useEffect, useCallback } = React;

const TABS = [
  { id: 'overview', label: '概览', en: 'overview' },
  { id: 'keys',     label: 'API Keys', en: 'keys' },
  { id: 'usage',    label: '用量', en: 'usage' },
  { id: 'billing',  label: '充值', en: 'billing' },
  { id: 'settings', label: '设置', en: 'settings' },
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
          <span className="cs-brand-name">Prism</span>
        </div>
        {TABS.map(t => (
          <a key={t.id} href={`#${t.id}`}
             className={`cs-nav-link ${tab === t.id ? 'active' : ''}`}>
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

function Metric({ label, value, meta }) {
  return (
    <div className="cs-metric">
      <div className="cs-metric-label">{label}</div>
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
  const [stats, setStats] = useState(null);
  const [groupBy, setGroupBy] = useState('model');
  const [requests, setRequests] = useState([]);
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    PrismAPI.get(`/usage/stats?group_by=${groupBy}`).then(setStats).catch(() => {});
  }, [groupBy]);

  useEffect(() => {
    PrismAPI.get('/usage/requests?size=50').then(d => setRequests(d.data || []));
  }, []);

  // Hash deep link: /console#usage/{request_id}
  useEffect(() => {
    const m = location.hash.match(/^#usage\/([\w-]+)$/);
    if (m) PrismAPI.get(`/usage/requests/${m[1]}`).then(setDetail);
    else setDetail(null);
    const handler = () => {
      const m = location.hash.match(/^#usage\/([\w-]+)$/);
      if (m) PrismAPI.get(`/usage/requests/${m[1]}`).then(setDetail);
      else setDetail(null);
    };
    window.addEventListener('hashchange', handler);
    return () => window.removeEventListener('hashchange', handler);
  }, []);

  return (
    <>
      <div className="cs-row" style={{marginBottom: 16, gap: 6}}>
        <span style={{fontSize: 12, color: 'var(--text-muted)', marginRight: 8}}>聚合：</span>
        {['model', 'channel', 'key', 'day'].map(g => (
          <button key={g} className={`cs-btn ${groupBy === g ? 'cs-btn-primary' : ''}`}
            onClick={() => setGroupBy(g)} style={{fontSize: 12, padding: '6px 12px'}}>
            {g}
          </button>
        ))}
      </div>

      {stats && (
        <section className="cs-section">
          <table className="cs-table">
            <thead>
              <tr>
                <th>{groupBy}</th>
                <th>请求数</th>
                <th>输入 tokens</th>
                <th>输出 tokens</th>
                <th>成本 (USD)</th>
                <th>平均延迟</th>
              </tr>
            </thead>
            <tbody>
              {(stats.data || []).map((r, i) => (
                <tr key={i}>
                  <td className="mono">{r.bucket || '-'}</td>
                  <td>{fmtCompact(r.requests)}</td>
                  <td className="mono">{fmtCompact(r.input_tokens)}</td>
                  <td className="mono">{fmtCompact(r.output_tokens)}</td>
                  <td>{fmtUSD(r.cost_usd)}</td>
                  <td className="mono">{r.avg_latency_ms ? r.avg_latency_ms + 'ms' : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section className="cs-section">
        <h2>最近 50 条请求</h2>
        <table className="cs-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>模型</th>
              <th>状态</th>
              <th>Tokens</th>
              <th>成本</th>
              <th>详情</th>
            </tr>
          </thead>
          <tbody>
            {requests.map(r => (
              <tr key={r.request_id}>
                <td className="mono" style={{fontSize: 11}}>{r.created_at?.slice(0, 19)}</td>
                <td>{r.model_id}</td>
                <td><StatusPill status={r.status}/></td>
                <td className="mono">{r.tokens.prompt} / {r.tokens.completion}</td>
                <td>{fmtUSD(r.cost_usd)}</td>
                <td><a href={`#usage/${r.request_id}`} className="cs-btn" style={{padding: '4px 10px'}}>查看</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {detail && <RequestDetailModal d={detail} onClose={() => location.hash = '#usage'}/>}
    </>
  );
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
    note: '链上费 ≈ $1 · 推荐金额 ≥ $50', icon: 'T', accent: '#EF4444' },
  { key: 'usdt-sol',   title: 'USDT (Solana)', en: 'SPL · 美区首选',
    note: '链上费 ≈ $0.001 · 任意金额', icon: '◎', accent: '#9333EA' },
  { key: 'usdt-evm',   title: 'USDT (EVM)', en: 'BSC / Polygon / Arbitrum / ETH',
    note: 'BSC 链上费 ≈ $0.3 · 推荐 BSC', icon: '⬢', accent: '#06B6D4' },
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
          background: channel.accent + '20',
          color: channel.accent,
          borderColor: channel.accent + '40',
        }}>{channel.icon}</span>
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
