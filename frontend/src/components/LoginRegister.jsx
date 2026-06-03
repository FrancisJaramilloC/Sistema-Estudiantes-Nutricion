import React, { useState } from 'react';
import { apiService } from '../services/api';

export default function LoginRegister({ onLoginSuccess }) {
  const [activeTab, setActiveTab] = useState('login'); // 'login' o 'register'
  
  // Estados para inputs
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Estudiantes');
  
  // Estados de control
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Validaciones del lado del cliente
  const validateForm = () => {
    if (!username.trim()) {
      setError('El nombre de usuario es obligatorio.');
      return false;
    }
    if (activeTab === 'register') {
      if (!email.trim() || !email.includes('@')) {
        setError('Por favor, ingresa un correo electrónico válido.');
        return false;
      }
    }
    if (!password || password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres.');
      return false;
    }
    // Opcional: validaciones más rigurosas de contraseña para cumplir políticas de Cognito
    const hasNumber = /\d/.test(password);
    const hasSpecial = /[^A-Za-z0-9]/.test(password);
    if (activeTab === 'register' && (!hasNumber || !hasSpecial)) {
      setError('La contraseña debe contener al menos un número y un carácter especial.');
      return false;
    }
    return true;
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setError('');
    setSuccess('');
    setPassword('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!validateForm()) return;

    setLoading(true);
    try {
      if (activeTab === 'login') {
        const data = await apiService.login(username, password);
        setSuccess('¡Inicio de sesión exitoso!');
        setTimeout(() => {
          onLoginSuccess(data.id_token, username);
        }, 1000);
      } else {
        const data = await apiService.register(username, email, password, role);
        setSuccess(data.message || 'Usuario registrado con éxito. Ya puedes iniciar sesión.');
        // Cambiar a pestaña de login tras un breve delay
        setTimeout(() => {
          setActiveTab('login');
          setError('');
          setSuccess('');
          setPassword('');
        }, 3000);
      }
    } catch (err) {
      setError(err.message || 'Ocurrió un error inesperado.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h1>Sistema NutriA</h1>
      <p className="text-center" style={{ marginBottom: '24px', color: 'hsl(var(--text-muted))' }}>
        Portal de Autenticación
      </p>

      {/* Tabs */}
      <div className="tabs-container">
        <button 
          className={`tab-btn ${activeTab === 'login' ? 'active' : ''}`}
          onClick={() => handleTabChange('login')}
          disabled={loading}
        >
          Iniciar Sesión
        </button>
        <button 
          className={`tab-btn ${activeTab === 'register' ? 'active' : ''}`}
          onClick={() => handleTabChange('register')}
          disabled={loading}
        >
          Registrarse
        </button>
      </div>

      {/* Alertas */}
      {error && <div className="error-msg">{error}</div>}
      {success && <div className="success-msg">{success}</div>}

      {/* Formulario */}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Usuario / Correo</label>
          <input 
            type="text" 
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="ej. pedro_nutri"
            disabled={loading}
            required
          />
        </div>

        {activeTab === 'register' && (
          <div className="form-group">
            <label htmlFor="email">Correo Electrónico</label>
            <input 
              type="email" 
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="correo@ejemplo.com"
              disabled={loading}
              required
            />
          </div>
        )}

        <div className="form-group">
          <label htmlFor="password">Contraseña</label>
          <input 
            type="password" 
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            disabled={loading}
            required
          />
          {activeTab === 'register' && (
            <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', marginTop: '4px' }}>
              Mínimo 8 caracteres, incluyendo un número y un símbolo especial.
            </span>
          )}
        </div>

        {activeTab === 'register' && (
          <div className="form-group">
            <label htmlFor="role">Rol en el Sistema</label>
            <select 
              id="role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              disabled={loading}
              required
            >
              <option value="Estudiantes">Estudiante</option>
              <option value="Docentes">Docente (Administrador)</option>
            </select>
          </div>
        )}

        <button type="submit" className="btn" disabled={loading}>
          {loading ? (
            <div className="spinner"></div>
          ) : activeTab === 'login' ? (
            'Iniciar Sesión'
          ) : (
            'Crear Cuenta'
          )}
        </button>
      </form>

      <div className="footer-text">
        Protegido mediante tecnología de autenticación AWS Cognito.
      </div>
    </div>
  );
}
