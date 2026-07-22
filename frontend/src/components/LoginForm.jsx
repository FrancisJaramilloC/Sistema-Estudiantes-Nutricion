import React from 'react';

export default function LoginForm({ username, password, loading, onUsernameChange, onPasswordChange, onSubmit }) {
  return (
    <form onSubmit={onSubmit}>
      <div className="form-group">
        <label htmlFor="login-username">Nombre de Usuario</label>
        <input
          type="text"
          id="login-username"
          value={username}
          onChange={(e) => onUsernameChange(e.target.value)}
          placeholder="ej. pedro_nutri"
          disabled={loading}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="login-password">Contraseña</label>
        <input
          type="password"
          id="login-password"
          value={password}
          onChange={(e) => onPasswordChange(e.target.value)}
          placeholder="••••••••"
          disabled={loading}
          required
        />
      </div>

      <button type="submit" className="btn" disabled={loading}>
        {loading ? <div className="spinner"></div> : 'Iniciar Sesión'}
      </button>
    </form>
  );
}
