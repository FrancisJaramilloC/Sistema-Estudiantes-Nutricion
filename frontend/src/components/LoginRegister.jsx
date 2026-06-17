import React, { useState } from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import { apiService } from '../services/api';

function validateEcuadorianCedula(val) {
  if (!/^\d{10}$/.test(val)) return false;
  const provincia = parseInt(val.substring(0, 2), 10);
  if (provincia < 1 || provincia > 24) return false;
  const tercerDigito = parseInt(val.charAt(2), 10);
  if (tercerDigito >= 6) return false;
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
}

export default function LoginRegister({ onLoginSuccess }) {
  const [activeTab, setActiveTab] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [nombre, setNombre] = useState('');
  const [cedula, setCedula] = useState('');
  const [fechaNacimiento, setFechaNacimiento] = useState('');
  const [role, setRole] = useState('Estudiantes');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const calcularEdad = (fecha) => {
    if (!fecha) return null;
    const birth = new Date(fecha);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const mDiff = today.getMonth() - birth.getMonth();
    if (mDiff < 0 || (mDiff === 0 && today.getDate() < birth.getDate())) age--;
    return age;
  };

  const esMayorEdad = fechaNacimiento ? (calcularEdad(fechaNacimiento) >= 18) : true;

  const validateForm = () => {
    if (!username.trim()) { setError('El nombre de usuario es obligatorio.'); return false; }
    if (username.trim().length < 4) { setError('El nombre de usuario debe tener al menos 4 caracteres.'); return false; }

    if (activeTab === 'register') {
      const nameRegex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{3,60}$/;
      if (!nameRegex.test(nombre.trim())) { setError('El nombre completo debe tener mínimo 3 letras y no contener números.'); return false; }
      if (!validateEcuadorianCedula(cedula)) { setError('La cédula ingresada no es válida.'); return false; }
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email.trim())) { setError('Ingresa un correo válido.'); return false; }
      if (!fechaNacimiento) { setError('La fecha de nacimiento es obligatoria.'); return false; }
      const edad = calcularEdad(fechaNacimiento);
      if (edad < 18) { setError('Debes ser mayor de 18 años.'); return false; }
      if (!password || password.length < 8) { setError('La contraseña debe tener al menos 8 caracteres.'); return false; }
      const hasNumber = /\d/.test(password);
      const hasSpecial = /[^A-Za-z0-9]/.test(password);
      const hasUpper = /[A-Z]/.test(password);
      const hasLower = /[a-z]/.test(password);
      if (!hasNumber || !hasSpecial || !hasUpper || !hasLower) {
        setError('La contraseña debe tener: mayúscula, minúscula, número y símbolo.');
        return false;
      }
    }
    return true;
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setError('');
    setSuccess('');
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
        setTimeout(() => onLoginSuccess(data.id_token, username), 1000);
      } else {
        await apiService.register(username, email, password, role, nombre.trim(), cedula.trim(), fechaNacimiento);
        setSuccess('¡Cuenta registrada con éxito! Inicia sesión.');
        setTimeout(() => { setActiveTab('login'); setError(''); setSuccess(''); }, 4000);
      }
    } catch (err) {
      setError(err.message || 'Ocurrió un error.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card auth-card">
      <h1>Sistema NutriA</h1>
      <p className="text-center" style={{ marginBottom: '24px', color: 'hsl(var(--text-muted))' }}>
        Portal de Autenticación
      </p>

      <div className="tabs-container">
        <button className={`tab-btn ${activeTab === 'login' ? 'active' : ''}`}
          onClick={() => handleTabChange('login')} disabled={loading}>
          Iniciar Sesión
        </button>
        <button className={`tab-btn ${activeTab === 'register' ? 'active' : ''}`}
          onClick={() => handleTabChange('register')} disabled={loading}>
          Registrarse
        </button>
      </div>

      {error && <div className="error-msg">{error}</div>}
      {success && <div className="success-msg">{success}</div>}

      {activeTab === 'login' ? (
        <LoginForm
          username={username} password={password} loading={loading}
          onUsernameChange={setUsername} onPasswordChange={setPassword}
          onSubmit={handleSubmit}
        />
      ) : (
        <RegisterForm
          nombre={nombre} cedula={cedula} username={username}
          email={email} fechaNacimiento={fechaNacimiento}
          password={password} role={role} loading={loading}
          esMayorEdad={esMayorEdad}
          onNombreChange={setNombre} onCedulaChange={setCedula}
          onUsernameChange={setUsername} onEmailChange={setEmail}
          onFechaNacimientoChange={setFechaNacimiento}
          onPasswordChange={setPassword} onRoleChange={setRole}
          onSubmit={handleSubmit}
        />
      )}

      <div className="footer-text">
        Protegido mediante autenticación segura JWT.
      </div>
    </div>
  );
}
