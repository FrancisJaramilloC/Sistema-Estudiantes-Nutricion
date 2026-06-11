import React, { useState } from 'react';
import { apiService } from '../services/api';

export default function LoginRegister({ onLoginSuccess }) {
  const [activeTab, setActiveTab] = useState('login'); // 'login' o 'register'
  
  // Estados para inputs comunes
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  
  // Estados adicionales para registro
  const [email, setEmail] = useState('');
  const [nombre, setNombre] = useState('');
  const [cedula, setCedula] = useState('');
  const [fechaNacimiento, setFechaNacimiento] = useState('');
  const [role, setRole] = useState('Estudiantes');
  const [adminKey, setAdminKey] = useState('');
  
  // Estados de control
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Algoritmo de validación de Cédula Ecuatoriana
  const validateEcuadorianCedula = (val) => {
    if (!/^\d{10}$/.test(val)) return false;
    
    const provincia = parseInt(val.substring(0, 2), 10);
    if (provincia < 1 || provincia > 24) return false;
    
    const tercerDigito = parseInt(val.charAt(2), 10);
    if (tercerDigito >= 6) return false;
    
    // Coeficientes del algoritmo
    const coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2];
    let suma = 0;
    
    for (let i = 0; i < 9; i++) {
      let valor = parseInt(val.charAt(i), 10) * coeficientes[i];
      if (valor >= 10) valor -= 9;
      suma += valor;
    }
    
    const digitoVerificador = parseInt(val.charAt(9), 10);
    const residuo = suma % 10;
    const digitoCalculado = residuo === 0 ? 0 : 10 - residuo;
    
    return digitoVerificador === digitoCalculado;
  };

  // Validaciones del lado del cliente
  const validateForm = () => {
    // Validación de usuario
    if (!username.trim()) {
      setError('El nombre de usuario es obligatorio.');
      return false;
    }
    if (username.trim().length < 4) {
      setError('El nombre de usuario debe tener al menos 4 caracteres.');
      return false;
    }

    if (activeTab === 'register') {
      // 1. Validación de Nombre Completo
      const nameRegex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{3,60}$/;
      if (!nameRegex.test(nombre.trim())) {
        setError('El nombre completo debe tener mínimo 3 letras y no contener números o caracteres especiales.');
        return false;
      }
      
      // 2. Validación de Cédula Ecuatoriana
      if (!validateEcuadorianCedula(cedula)) {
        setError('La cédula ingresada no es válida en el territorio ecuatoriano.');
        return false;
      }

      // 3. Validación de Correo Electrónico
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email.trim())) {
        setError('Por favor, ingresa un correo electrónico válido (ejemplo@dominio.com).');
        return false;
      }

      // 4. Validación de Fecha de Nacimiento (Mayor de 18 años)
      if (!fechaNacimiento) {
        setError('La fecha de nacimiento es obligatoria.');
        return false;
      }
      const birthDate = new Date(fechaNacimiento);
      const today = new Date();
      let age = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }
      if (age < 18) {
        setError('Debes ser mayor de 18 años para registrarte en el sistema.');
        return false;
      }
      if (age > 100) {
        setError('Por favor, ingresa una fecha de nacimiento válida.');
        return false;
      }

      // 5. Validación de Clave Docente
      if (role === 'Docentes' && !adminKey.trim()) {
        setError('La clave de validación del docente es obligatoria.');
        return false;
      }
    }

    // Validación de Contraseña
    if (!password || password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres.');
      return false;
    }
    
    const hasNumber = /\d/.test(password);
    const hasSpecial = /[^A-Za-z0-9]/.test(password);
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);

    if (activeTab === 'register') {
      if (!hasNumber || !hasSpecial || !hasUpper || !hasLower) {
        setError('La contraseña debe tener: mayúscula, minúscula, número y un carácter especial.');
        return false;
      }
    }
    
    return true;
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setError('');
    setSuccess('');
    setPassword('');
    setAdminKey(''); // Limpiar clave docente al cambiar pestaña
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
        const data = await apiService.register(
          username, 
          email, 
          password, 
          role, 
          nombre.trim(), 
          cedula.trim(), 
          fechaNacimiento,
          adminKey.trim()
        );
        setSuccess('¡Cuenta registrada con éxito! Verifica tu correo electrónico e inicia sesión.');
        setTimeout(() => {
          setActiveTab('login');
          setError('');
          setSuccess('');
          setPassword('');
          setAdminKey('');
        }, 4000);
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
        
        {/* Nombre completo (Solo Registro) */}
        {activeTab === 'register' && (
          <div className="form-group">
            <label htmlFor="nombre">Nombre Completo</label>
            <input 
              type="text" 
              id="nombre"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="ej. Juan Pérez"
              disabled={loading}
              required
            />
          </div>
        )}

        {/* Cédula (Solo Registro) */}
        {activeTab === 'register' && (
          <div className="form-group">
            <label htmlFor="cedula">Cédula de Identidad</label>
            <input 
              type="text" 
              id="cedula"
              value={cedula}
              onChange={(e) => setCedula(e.target.value)}
              placeholder="ej. 1723456789"
              maxLength="10"
              disabled={loading}
              required
            />
          </div>
        )}

        {/* Nombre de usuario (Común) */}
        <div className="form-group">
          <label htmlFor="username">Nombre de Usuario</label>
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

        {/* Correo Electrónico (Solo Registro) */}
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

        {/* Fecha de Nacimiento (Solo Registro) */}
        {activeTab === 'register' && (
          <div className="form-group">
            <label htmlFor="fechaNacimiento">Fecha de Nacimiento</label>
            <input 
              type="date" 
              id="fechaNacimiento"
              value={fechaNacimiento}
              onChange={(e) => setFechaNacimiento(e.target.value)}
              disabled={loading}
              required
            />
          </div>
        )}

        {/* Contraseña (Común) */}
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
              Debe incluir: 8+ caracteres, mayúscula, minúscula, número y un símbolo.
            </span>
          )}
        </div>

        {/* Rol (Solo Registro) */}
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

        {/* Clave de Validación Docente (Solo Registro si el rol es Docentes) */}
        {activeTab === 'register' && role === 'Docentes' && (
          <div className="form-group animate-fade-in">
            <label htmlFor="adminKey">Clave de Validación de Docente</label>
            <input 
              type="password" 
              id="adminKey"
              value={adminKey}
              onChange={(e) => setAdminKey(e.target.value)}
              placeholder="Ingrese la clave secreta de docente"
              disabled={loading}
              required
            />
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
