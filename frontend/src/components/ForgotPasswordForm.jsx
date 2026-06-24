import React from 'react';

export default function ForgotPasswordForm({ email, loading, onEmailChange, onSubmit, onBack }) {
  return (
    <form onSubmit={onSubmit}>
      <p style={{ marginBottom: '20px', color: 'hsl(var(--text-secondary))', fontSize: '0.9rem' }}>
        Ingresa tu correo electrónico registrado y te enviaremos un enlace para restablecer tu contraseña.
      </p>

      <div className="form-group">
        <label htmlFor="forgot-email">Correo Electrónico</label>
        <input
          type="email"
          id="forgot-email"
          value={email}
          onChange={(e) => onEmailChange(e.target.value)}
          placeholder="correo@ejemplo.com"
          disabled={loading}
          required
        />
      </div>

      <button type="submit" className="btn" disabled={loading}>
        {loading ? <div className="spinner"></div> : 'Enviar Enlace'}
      </button>

      <button type="button" className="btn btn-secondary" onClick={onBack} disabled={loading}
        style={{ marginTop: '10px' }}>
        Volver al Inicio de Sesión
      </button>
    </form>
  );
}
