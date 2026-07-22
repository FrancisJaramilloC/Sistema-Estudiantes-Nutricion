import React from 'react';

export default function ResetPasswordForm({
  username, resetToken, newPassword, confirmPassword, loading,
  onUsernameChange, onResetTokenChange, onNewPasswordChange, onConfirmPasswordChange,
  onSubmit, onBack
}) {
  const passwordsMatch = confirmPassword ? newPassword === confirmPassword : null;

  return (
    <form onSubmit={onSubmit}>
      <p style={{ marginBottom: '20px', color: 'hsl(var(--text-secondary))', fontSize: '0.9rem' }}>
        {resetToken
          ? 'Ingresa tu nueva contraseña a continuación.'
          : 'Revisa tu correo electrónico para obtener el código de verificación, luego completa los campos abaixo.'}
      </p>

      <div className="form-group">
        <label htmlFor="reset-username">Nombre de Usuario</label>
        <input
          type="text"
          id="reset-username"
          value={username}
          onChange={(e) => onUsernameChange(e.target.value)}
          placeholder="ej. pedro_nutri"
          disabled={loading}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="reset-token">Código de Verificación</label>
        <input
          type="text"
          id="reset-token"
          value={resetToken}
          onChange={(e) => onResetTokenChange(e.target.value)}
          placeholder="Ingresa el código recibido"
          disabled={loading}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="reset-password">Nueva Contraseña</label>
        <input
          type="password"
          id="reset-password"
          value={newPassword}
          onChange={(e) => onNewPasswordChange(e.target.value)}
          placeholder="••••••••"
          disabled={loading}
          required
        />
        <span className="field-hint">
          Debe incluir: 8+ caracteres, mayúscula, minúscula, número y un símbolo.
        </span>
      </div>

      <div className="form-group">
        <label htmlFor="reset-confirm">Confirmar Nueva Contraseña</label>
        <div className="input-feedback-wrapper">
          <input
            type="password"
            id="reset-confirm"
            value={confirmPassword}
            onChange={(e) => onConfirmPasswordChange(e.target.value)}
            placeholder="••••••••"
            disabled={loading}
            className={
              confirmPassword && newPassword
                ? (passwordsMatch ? 'input-valid' : 'input-invalid')
                : ''
            }
            required
          />
          {confirmPassword && (
            <span className={`input-status-icon ${passwordsMatch ? 'status-ok' : 'status-err'}`}>
              {passwordsMatch ? '✓' : '✗'}
            </span>
          )}
        </div>
        {confirmPassword && passwordsMatch === false && (
          <span className="field-hint error-hint">Las contraseñas no coinciden.</span>
        )}
      </div>

      <button type="submit" className="btn" disabled={loading || passwordsMatch === false}>
        {loading ? <div className="spinner"></div> : 'Restablecer Contraseña'}
      </button>

      <button type="button" className="btn btn-secondary" onClick={onBack} disabled={loading}
        style={{ marginTop: '10px' }}>
        Volver al Inicio de Sesión
      </button>
    </form>
  );
}
