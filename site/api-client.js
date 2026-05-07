/* Lightweight API client for Prism console.
 *
 * Stores JWT in localStorage under 'prism_token'.
 * Auto-attaches Authorization header to all calls.
 * Auto-redirects to /login on 401.
 */

(function () {
  const API_BASE = '/suanli-api';

  function getToken() {
    return localStorage.getItem('prism_token');
  }

  function setToken(token, expiresAt) {
    localStorage.setItem('prism_token', token);
    if (expiresAt) localStorage.setItem('prism_token_expires', expiresAt);
  }

  function clearToken() {
    localStorage.removeItem('prism_token');
    localStorage.removeItem('prism_token_expires');
  }

  function isLoggedIn() {
    return !!getToken();
  }

  async function call(method, path, { body, headers = {}, requireAuth = true } = {}) {
    const finalHeaders = { 'Content-Type': 'application/json', ...headers };
    if (requireAuth) {
      const tok = getToken();
      if (!tok) {
        location.href = '/login?next=' + encodeURIComponent(location.pathname + location.hash);
        throw new Error('Not authenticated');
      }
      finalHeaders.Authorization = 'Bearer ' + tok;
    }

    const res = await fetch(API_BASE + path, {
      method,
      headers: finalHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (res.status === 401 && requireAuth) {
      clearToken();
      location.href = '/login?next=' + encodeURIComponent(location.pathname + location.hash);
      throw new Error('Session expired');
    }

    let data = null;
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      data = await res.json();
    }

    if (!res.ok) {
      const err = new Error((data && data.error && data.error.message) || ('HTTP ' + res.status));
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  window.PrismAPI = {
    getToken, setToken, clearToken, isLoggedIn,
    get: (path, opts) => call('GET', path, opts),
    post: (path, body, opts) => call('POST', path, { ...opts, body }),
    patch: (path, body, opts) => call('PATCH', path, { ...opts, body }),
    delete: (path, opts) => call('DELETE', path, opts),
  };

  // Pull token from URL fragment after OAuth redirect
  if (location.hash && location.hash.includes('token=')) {
    const params = new URLSearchParams(location.hash.slice(1));
    const tok = params.get('token');
    const exp = params.get('expires_at');
    if (tok) {
      setToken(tok, exp);
      // Strip the fragment so a refresh doesn't re-process
      history.replaceState(null, '', location.pathname);
    }
  }
})();
