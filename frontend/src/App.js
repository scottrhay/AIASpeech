import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import './theme/theme.css';
import Login from './pages/Login';
import HomePremium from './pages/HomePremium';
import ManageStyles from './pages/ManageStyles';
import { getToken, removeToken, handleOAuthCallback } from './services/auth';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // [SEC-001 FIX] Check fragment (#) first (secure), then fall back to query string (?) for
    // backward compatibility during rollout. Fragments never hit server logs or Referer headers.
    const fragment = window.location.hash.substring(1); // strip leading '#'
    const fragmentParams = new URLSearchParams(fragment);
    const queryParams = new URLSearchParams(window.location.search);
    // Prefer fragment, fall back to query string
    const token = fragmentParams.get('token') || queryParams.get('token');
    const userId = fragmentParams.get('user_id') || queryParams.get('user_id');
    const username = fragmentParams.get('username') || queryParams.get('username');

    console.log('[OAuth Debug] Token found:', !!token);

    if (token) {
      console.log('[OAuth Debug] Processing OAuth callback');
      handleOAuthCallback(token, userId, username);
      console.log('[OAuth Debug] Token stored in localStorage');
      // Clear URL params and fragment
      window.history.replaceState({}, document.title, window.location.pathname);
      setIsAuthenticated(true);
      console.log('[OAuth Debug] Authentication set to true');
    } else {
      // Check if user is authenticated on mount
      const existingToken = getToken();
      console.log('[OAuth Debug] Checking existing token:', !!existingToken);
      setIsAuthenticated(!!existingToken);
    }
    setIsLoading(false);
  }, []);

  const handleLogout = () => {
    removeToken();
    setIsAuthenticated(false);
  };

  // Show nothing while checking auth to prevent flash
  if (isLoading) {
    return null;
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              <Navigate to="/" />
            ) : (
              <Login onLogin={() => setIsAuthenticated(true)} />
            )
          }
        />
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <HomePremium onLogout={handleLogout} />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="/styles"
          element={
            isAuthenticated ? (
              <ManageStyles onLogout={handleLogout} />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
