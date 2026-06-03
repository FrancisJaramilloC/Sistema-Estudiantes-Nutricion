import React, { useState, useEffect } from 'react';
import LoginRegister from './components/LoginRegister';
import Dashboard from './components/Dashboard';

function App() {
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState('');

  // Cargar token desde localStorage al iniciar la app
  useEffect(() => {
    const savedToken = localStorage.getItem('nutria_token');
    const savedUser = localStorage.getItem('nutria_username');
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUsername(savedUser);
    }
  }, []);

  const handleLoginSuccess = (newToken, user) => {
    setToken(newToken);
    setUsername(user);
    localStorage.setItem('nutria_token', newToken);
    localStorage.setItem('nutria_username', user);
  };

  const handleLogout = () => {
    setToken(null);
    setUsername('');
    localStorage.removeItem('nutria_token');
    localStorage.removeItem('nutria_username');
  };

  return (
    <>
      {token ? (
        <Dashboard token={token} username={username} onLogout={handleLogout} />
      ) : (
        <LoginRegister onLoginSuccess={handleLoginSuccess} />
      )}
    </>
  );
}

export default App;
