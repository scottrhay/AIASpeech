import React, { useState, useEffect } from 'react';
import { login, register, handleOAuthCallback } from '../services/auth';
import './Login.css';

const API_URL = process.env.REACT_APP_API_URL || 'https://speech.aiacopilot.com/api/v1';

function Login({ onLogin }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    accessCode: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  // Handle OAuth callback (both success and error)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const oauthError = urlParams.get('error');
    const errorMessage = urlParams.get('message');

    if (token) {
      // OAuth success - store token and notify parent
      handleOAuthCallback(token, urlParams.get('user_id'), urlParams.get('username'));
      window.history.replaceState({}, document.title, window.location.pathname);
      onLogin();
    } else if (oauthError) {
      // OAuth error
      setError(errorMessage || 'Authentication failed. Please try again.');
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [onLogin]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      if (isRegistering) {
        // Validate access code
        if (formData.accessCode !== '49676') {
          setError('Invalid access code. Please contact administrator for access.');
          return;
        }
        await register(formData.username, formData.email, formData.password);
        setSuccess('Account created successfully! Please login.');
        setIsRegistering(false);
        setFormData({ username: '', email: '', password: '', accessCode: '' });
      } else {
        await login(formData.username, formData.password);
        onLogin();
      }
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred');
    }
  };

  const handleMicrosoftLogin = () => {
    setLoading(true);
    // Redirect to Microsoft OAuth
    window.location.href = `${API_URL}/auth/microsoft/login`;
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>AIA Speech Studio</h1>
        <p className="login-subtitle">Speech Creation Platform</p>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {/* Microsoft Sign In Button */}
        <button
          type="button"
          className="btn btn-microsoft"
          onClick={handleMicrosoftLogin}
          disabled={loading}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 23 23">
            <path fill="#f35325" d="M1 1h10v10H1z"/>
            <path fill="#81bc06" d="M12 1h10v10H12z"/>
            <path fill="#05a6f0" d="M1 12h10v10H1z"/>
            <path fill="#ffba08" d="M12 12h10v10H12z"/>
          </svg>
          <span>{loading ? 'Redirecting...' : 'Sign in with Microsoft'}</span>
        </button>

        <div className="login-divider">
          <span>or</span>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
            />
          </div>

          {isRegistering && (
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>

          {isRegistering && (
            <div className="form-group">
              <label>Credit Card (Access Code)</label>
              <input
                type="text"
                name="accessCode"
                value={formData.accessCode}
                onChange={handleChange}
                placeholder="Enter access code"
                required
              />
              <small className="form-hint">Contact administrator for access code</small>
            </div>
          )}

          <button type="submit" className="btn btn-primary">
            {isRegistering ? 'Register' : 'Login'}
          </button>
        </form>

        <div className="login-toggle">
          {isRegistering ? (
            <p>
              Already have an account?{' '}
              <button onClick={() => setIsRegistering(false)}>Login</button>
            </p>
          ) : (
            <p>
              Don't have an account?{' '}
              <button onClick={() => setIsRegistering(true)}>Register</button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Login;
