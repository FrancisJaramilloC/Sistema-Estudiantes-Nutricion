import React, { useState, useEffect } from 'react';
import LoginRegister from './components/LoginRegister';
import Dashboard from './components/Dashboard';
import { apiService } from './services/api';

function App() {
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState('');
  const [currentHash, setCurrentHash] = useState(window.location.hash || '#/login');

  // Monitorizar cambios en la URL (hash)
  useEffect(() => {
    const handleHashChange = () => {
      setCurrentHash(window.location.hash || '#/login');
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Cargar token desde localStorage al iniciar la app
  useEffect(() => {
    const savedToken = localStorage.getItem('nutria_token');
    const savedUser = localStorage.getItem('nutria_username');
    if (savedToken && savedUser) {
      try {
        const base64Url = savedToken.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
          window.atob(base64)
            .split('')
            .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        );
        const payload = JSON.parse(jsonPayload);
        const currentTime = Math.floor(Date.now() / 1000);
        if (payload.exp && payload.exp < currentTime) {
          // Token expirado, limpiar almacenamiento local
          localStorage.removeItem('nutria_token');
          localStorage.removeItem('nutria_username');
          setToken(null);
          setUsername('');
          window.location.hash = '#/login';
        } else {
          setToken(savedToken);
          setUsername(savedUser);
        }
      } catch (e) {
        console.error("Token no válido o expirado:", e);
        localStorage.removeItem('nutria_token');
        localStorage.removeItem('nutria_username');
        setToken(null);
        setUsername('');
        window.location.hash = '#/login';
      }
    } else {
      // Si no hay token guardado, forzar hash de login
      if (window.location.hash.startsWith('#/dashboard')) {
        window.location.hash = '#/login';
      }
    }
  }, []);

  // Redirecciones basadas en estado de sesión y ruta actual
  useEffect(() => {
    if (token) {
      if (!currentHash || currentHash === '#/login' || currentHash === '#') {
        window.location.hash = '#/dashboard/inicio';
      }
    } else {
      if (currentHash.startsWith('#/dashboard')) {
        window.location.hash = '#/login';
      }
    }
  }, [token, currentHash]);

  const handleLoginSuccess = (newToken, user) => {
    setToken(newToken);
    setUsername(user);
    localStorage.setItem('nutria_token', newToken);
    localStorage.setItem('nutria_username', user);
    window.location.hash = '#/dashboard/inicio';
  };

  const handleLogout = () => {
    apiService.logout(username);
    setToken(null);
    setUsername('');
    localStorage.removeItem('nutria_token');
    localStorage.removeItem('nutria_username');
    window.location.hash = '#/login';
  };

  return (
    <>
      {token ? (
        <Dashboard token={token} username={username} onLogout={handleLogout} currentHash={currentHash} />
      ) : (
        <LoginRegister onLoginSuccess={handleLoginSuccess} />
      )}
    </>
  );
}

export default App;
