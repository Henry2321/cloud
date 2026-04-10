import { useState } from 'react';

function EyeIcon({ open }) {
  return open ? (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );
}

function Auth({ onLogin }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [form, setForm] = useState({ username: '', password: '', confirm: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError('');
    setSuccess('');
  }

  function handleSubmit(e) {
    e.preventDefault();
    const { username, password, confirm } = form;

    if (!username.trim() || !password.trim()) {
      setError('Vui lòng điền đầy đủ thông tin.');
      return;
    }

    if (mode === 'register') {
      if (password !== confirm) {
        setError('Mật khẩu xác nhận không khớp.');
        return;
      }
      const users = JSON.parse(localStorage.getItem('cspm_users') || '{}');
      if (users[username]) {
        setError('Tên đăng nhập đã tồn tại.');
        return;
      }
      users[username] = password;
      localStorage.setItem('cspm_users', JSON.stringify(users));
      setSuccess('Đăng ký thành công! Đang chuyển sang đăng nhập...');
      setForm({ username, password: '', confirm: '' });
      setTimeout(() => {
        setMode('login');
        setError('');
        setSuccess('');
      }, 1200);
      return;
    }

    // login
    const users = JSON.parse(localStorage.getItem('cspm_users') || '{}');
    if (users[username] !== password) {
      setError('Sai tên đăng nhập hoặc mật khẩu.');
      return;
    }
    localStorage.setItem('cspm_session', username);
    setSuccess('Đăng nhập thành công! Đang chuyển trang...');
    setTimeout(() => onLogin(username), 800);
  }

  return (
    <div className="auth-shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />

      <div className="auth-card panel">
        <div className="auth-header">
          <span className="eyebrow">Cloud posture command center</span>
          <h1>CSPM Dashboard</h1>
        </div>

        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab${mode === 'login' ? ' is-active' : ''}`}
            onClick={() => { setMode('login'); setError(''); setSuccess(''); }}
          >
            Đăng nhập
          </button>
          <button
            type="button"
            className={`auth-tab${mode === 'register' ? ' is-active' : ''}`}
            onClick={() => { setMode('register'); setError(''); setSuccess(''); }}
          >
            Đăng ký
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-field">
            <label>Tên đăng nhập</label>
            <input
              name="username"
              type="text"
              placeholder="Nhập tên đăng nhập..."
              value={form.username}
              onChange={handleChange}
              autoComplete="username"
            />
          </div>

          <div className="auth-field">
            <label>Mật khẩu</label>
            <div className="auth-input-wrap">
              <input
                name="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Nhập mật khẩu..."
                value={form.password}
                onChange={handleChange}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
              <button type="button" className="eye-btn" onClick={() => setShowPassword(v => !v)}>
                <EyeIcon open={showPassword} />
              </button>
            </div>
          </div>

          {mode === 'register' && (
            <div className="auth-field">
              <label>Xác nhận mật khẩu</label>
              <div className="auth-input-wrap">
                <input
                  name="confirm"
                  type={showConfirm ? 'text' : 'password'}
                  placeholder="Nhập lại mật khẩu..."
                  value={form.confirm}
                  onChange={handleChange}
                  autoComplete="new-password"
                />
                <button type="button" className="eye-btn" onClick={() => setShowConfirm(v => !v)}>
                  <EyeIcon open={showConfirm} />
                </button>
              </div>
            </div>
          )}

          {error && <p className="auth-error">{error}</p>}
          {success && <p className="auth-success">{success}</p>}

          <button type="submit" className="primary-button auth-submit">
            {mode === 'login' ? 'Đăng nhập' : 'Đăng ký'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Auth;
