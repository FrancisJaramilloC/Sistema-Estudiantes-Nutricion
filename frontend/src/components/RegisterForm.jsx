import React, { useState, useMemo } from 'react';

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

function calcularEdad(fechaNacimiento) {
  if (!fechaNacimiento) return null;
  const birthDate = new Date(fechaNacimiento);
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
}

export default function RegisterForm({
  nombre, cedula, username, email, fechaNacimiento, password, loading, esMayorEdad,
  onNombreChange, onCedulaChange, onUsernameChange, onEmailChange,
  onFechaNacimientoChange, onPasswordChange, onSubmit,
}) {
  const cedulaValida = cedula.length === 10 ? validateEcuadorianCedula(cedula) : null;

  const nombreValido = useMemo(() => {
    if (!nombre) return null;
    return /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{3,60}$/.test(nombre.trim());
  }, [nombre]);

  const esBloqueado = loading || !esMayorEdad;

  return (
    <form onSubmit={onSubmit}>
      {!esMayorEdad && fechaNacimiento && (
        <div className="age-banner">
          ⚠️ Debes ser mayor de 18 años para registrarte en el sistema.
        </div>
      )}

      <div className="form-group">
        <label htmlFor="reg-nombre">Nombre Completo</label>
        <div className="input-feedback-wrapper">
          <input
            type="text"
            id="reg-nombre"
            value={nombre}
            onChange={(e) => onNombreChange(e.target.value)}
            placeholder="ej. Juan Pérez"
            disabled={loading}
            className={
              nombreValido === true ? 'input-valid' :
              nombreValido === false ? 'input-invalid' : ''
            }
            required
          />
          {nombre && (
            <span className={`input-status-icon ${nombreValido ? 'status-ok' : 'status-err'}`}>
              {nombreValido ? '✓' : '✗'}
            </span>
          )}
        </div>
        {nombreValido === false && (
          <span className="field-hint error-hint">Solo letras, mínimo 3 caracteres.</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="reg-cedula">Cédula de Identidad</label>
        <div className="input-feedback-wrapper">
          <input
            type="text"
            id="reg-cedula"
            value={cedula}
            onChange={(e) => onCedulaChange(e.target.value.replace(/\D/g, '').slice(0, 10))}
            placeholder="ej. 1723456789"
            maxLength="10"
            disabled={loading}
            className={
              cedulaValida === true ? 'input-valid' :
              cedulaValida === false ? 'input-invalid' : ''
            }
            required
          />
          {cedula.length === 10 && (
            <span className={`input-status-icon ${cedulaValida ? 'status-ok' : 'status-err'}`}>
              {cedulaValida ? '✓' : '✗'}
            </span>
          )}
        </div>
        {cedulaValida === false && (
          <span className="field-hint error-hint">Cédula inválida (Módulo 10).</span>
        )}
        {cedulaValida === true && (
          <span className="field-hint success-hint">Cédula válida.</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="reg-username">Nombre de Usuario</label>
        <input
          type="text"
          id="reg-username"
          value={username}
          onChange={(e) => onUsernameChange(e.target.value)}
          placeholder="ej. pedro_nutri"
          disabled={loading}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="reg-email">Correo Electrónico</label>
        <input
          type="email"
          id="reg-email"
          value={email}
          onChange={(e) => onEmailChange(e.target.value)}
          placeholder="correo@ejemplo.com"
          disabled={loading}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="reg-fecha">Fecha de Nacimiento</label>
        <input
          type="date"
          id="reg-fecha"
          value={fechaNacimiento}
          onChange={(e) => onFechaNacimientoChange(e.target.value)}
          disabled={loading}
          required
        />
        {fechaNacimiento && esMayorEdad && (
          <span className="field-hint success-hint">Edad: {calcularEdad(fechaNacimiento)} años.</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="reg-password">Contraseña</label>
        <input
          type="password"
          id="reg-password"
          value={password}
          onChange={(e) => onPasswordChange(e.target.value)}
          placeholder="••••••••"
          disabled={loading}
          required
        />
        <span className="field-hint">
          Debe incluir: 8+ caracteres, mayúscula, minúscula, número y un símbolo.
        </span>
      </div>

      <button type="submit" className="btn" disabled={esBloqueado}>
        {loading ? <div className="spinner"></div> : 'Crear Cuenta'}
      </button>
    </form>
  );
}
