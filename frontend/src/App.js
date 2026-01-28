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
    // Check for OAuth callback params first
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (token) {
      // OAuth callback - store token and mark as authenticated
      handleOAuthCallback(token, urlParams.get('user_id'), urlParams.get('username'));
      // Clear URL params
      window.history.replaceState({}, document.title, window.location.pathname);
      setIsAuthenticated(true);
    } else {
      // Check if user is authenticated on mount
      setIsAuthenticated(!!getToken());
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
