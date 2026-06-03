import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

export default function Dashboard({ token, username, onLogout }) {
  const [userPayload, setUserPayload] = useState(null);
  const [role, setRole] = useState('Estudiantes');
  
  // Estados para formulario de plan (Estudiantes/Docentes)
  const [pacienteId, setPacienteId] = useState('');
  const [tipoPlan, setTipoPlan] = useState('Balanceado');
  const [planResult, setPlanResult] = useState('');
  const [planError, setPlanError] = useState('');
  const [planLoading, setPlanLoading] = useState(false);

  // Estados para auditoría (Solo Docentes)
  const [tasks, setTasks] = useState([]);
  const [auditError, setAuditError] = useState('');
  const [auditLoading, setAuditLoading] = useState(false);

  // Decodificar el token JWT al montar el componente
  useEffect(() => {
    if (token) {
      try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
          window.atob(base64)
            .split('')
            .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        );
        const payload = JSON.parse(jsonPayload);
        setUserPayload(payload);
        
        // Obtener rol
        const groups = payload['cognito:groups'] || [];
        if (groups.includes('Docentes')) {
          setRole('Docentes');
        } else {
          setRole('Estudiantes');
        }
      } catch (e) {
        console.error('Error decodificando token', e);
      }
    }
  }, [token]);

  // Cargar tareas de auditoría si el usuario es Docente
  const loadAuditTasks = async () => {
    setAuditLoading(true);
    setAuditError('');
    try {
      const data = await apiService.getAdminTasks(token);
      setTasks(data || []);
    } catch (err) {
      setAuditError(err.message || 'No autorizado para ver auditoría.');
    } finally {
      setAuditLoading(false);
    }
  };

  useEffect(() => {
    if (role === 'Docentes') {
      loadAuditTasks();
    }
  }, [role]);

  const handleRequestPlan = async (e) => {
    e.preventDefault();
    setPlanResult('');
    setPlanError('');
    
    if (!pacienteId.trim()) {
      setPlanError('Debe ingresar un ID de paciente.');
      return;
    }

    setPlanLoading(true);
    try {
      const data = await apiService.createPlan(token, {
        paciente_id: pacienteId,
        tipo_plan: tipoPlan
      });
      setPlanResult(`¡Plan solicitado! Task ID: ${data.task_id} (Estado: ${data.status})`);
      setPacienteId('');
      
      // Si es docente, refrescar la lista de tareas automáticamente
      if (role === 'Docentes') {
        setTimeout(loadAuditTasks, 1500);
      }
    } catch (err) {
      setPlanError(err.message || 'Error al solicitar el plan nutricional.');
    } finally {
      setPlanLoading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: '600px', width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ fontSize: '1.8rem', textAlign: 'left', margin: 0 }}>Panel NutriA</h1>
        <button onClick={onLogout} className="btn btn-secondary" style={{ width: 'auto', marginTop: 0, padding: '8px 16px' }}>
          Salir
        </button>
      </div>

      {/* Información del Usuario */}
      <div style={{ 
        background: 'rgba(255, 255, 255, 0.03)', 
        border: '1px solid hsl(var(--card-border))', 
        borderRadius: '12px', 
        padding: '16px', 
        marginBottom: '24px' 
      }}>
        <p style={{ fontWeight: 600, color: 'hsl(var(--text-primary))' }}>
          Usuario: <span style={{ color: 'hsl(var(--primary))' }}>{username}</span>
        </p>
        <p style={{ fontSize: '0.85rem', color: 'hsl(var(--text-secondary))', marginTop: '4px' }}>
          Rol en Nube: <strong style={{ color: role === 'Docentes' ? '#34d399' : '#60a5fa' }}>{role}</strong>
        </p>
        {userPayload && userPayload.email && (
          <p style={{ fontSize: '0.85rem', color: 'hsl(var(--text-muted))', marginTop: '4px' }}>
            Email: {userPayload.email}
          </p>
        )}
      </div>

      {/* Formulario de Solicitud de Plan */}
      <div style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '1.2rem', textAlign: 'left', marginBottom: '16px', color: 'hsl(var(--text-primary))' }}>
          Generar Plan Nutricional
        </h2>
        {planError && <div className="error-msg">{planError}</div>}
        {planResult && <div className="success-msg">{planResult}</div>}
        
        <form onSubmit={handleRequestPlan} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="pacienteId">Identificación del Paciente</label>
            <input 
              type="text" 
              id="pacienteId"
              value={pacienteId}
              onChange={(e) => setPacienteId(e.target.value)}
              placeholder="ej. PAC-983"
              disabled={planLoading}
              required
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="tipoPlan">Tipo de Plan Nutricional</label>
            <select 
              id="tipoPlan"
              value={tipoPlan}
              onChange={(e) => setTipoPlan(e.target.value)}
              disabled={planLoading}
              required
            >
              <option value="Balanceado">Balanceado</option>
              <option value="Keto (Cetogénico)">Keto (Cetogénico)</option>
              <option value="Vegano">Vegano</option>
              <option value="Hiperproteico">Hiperproteico</option>
            </select>
          </div>

          <button type="submit" className="btn" disabled={planLoading}>
            {planLoading ? <div className="spinner"></div> : 'Solicitar Plan Nutricional'}
          </button>
        </form>
      </div>

      {/* Historial de Auditoría (Solo para Docentes) */}
      {role === 'Docentes' ? (
        <div style={{ 
          borderTop: '1px solid hsl(var(--card-border))', 
          paddingTop: '20px' 
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h2 style={{ fontSize: '1.2rem', textAlign: 'left', margin: 0, color: 'hsl(var(--text-primary))' }}>
              Auditoría de Tareas (DynamoDB)
            </h2>
            <button 
              onClick={loadAuditTasks} 
              className="btn btn-secondary" 
              style={{ width: 'auto', marginTop: 0, padding: '4px 10px', fontSize: '0.8rem' }}
              disabled={auditLoading}
            >
              Refrescar
            </button>
          </div>

          {auditError && <div className="error-msg">{auditError}</div>}

          {auditLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '20px' }}>
              <div className="spinner" style={{ borderColor: 'rgba(255,255,255,0.1)', borderTopColor: 'hsl(var(--primary))' }}></div>
            </div>
          ) : tasks.length === 0 ? (
            <p style={{ textAlign: 'center', color: 'hsl(var(--text-muted))', padding: '16px 0' }}>
              No hay tareas registradas en la base de datos.
            </p>
          ) : (
            <div style={{ 
              maxHeight: '200px', 
              overflowY: 'auto', 
              display: 'flex', 
              flexDirection: 'column', 
              gap: '8px',
              paddingRight: '4px'
            }}>
              {tasks.map((task) => (
                <div key={task.task_id} style={{ 
                  background: 'rgba(10, 13, 20, 0.4)', 
                  border: '1px solid hsl(var(--card-border))', 
                  borderRadius: '8px', 
                  padding: '10px 12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginRight: '8px' }}>
                    <p style={{ fontSize: '0.8rem', fontWeight: 600 }}>Paciente: {task.paciente_id || 'N/A'}</p>
                    <p style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', marginTop: '2px' }}>
                      ID: {task.task_id.substring(0, 8)}...
                    </p>
                  </div>
                  <span style={{ 
                    fontSize: '0.75rem', 
                    fontWeight: 600, 
                    padding: '3px 8px', 
                    borderRadius: '20px',
                    background: task.status === 'COMPLETADO' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                    color: task.status === 'COMPLETADO' ? '#34d399' : '#fbbf24',
                    border: task.status === 'COMPLETADO' ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid rgba(245, 158, 11, 0.2)'
                  }}>
                    {task.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div style={{ 
          borderTop: '1px solid hsl(var(--card-border))', 
          paddingTop: '20px',
          textAlign: 'center',
          color: 'hsl(var(--text-muted))',
          fontSize: '0.85rem'
        }}>
          💡 Panel de auditoría de DynamoDB disponible solo para cuentas con rol de **Docente**.
        </div>
      )}

      {/* Mostrar Token para Depuración / Evaluación del Profesor */}
      <div style={{ marginTop: '24px' }}>
        <p style={{ fontSize: '0.8rem', color: 'hsl(var(--text-muted))', marginBottom: '8px' }}>
          Token JWT activo (para pruebas en Swagger / Postman):
        </p>
        <div className="token-container">{token}</div>
      </div>
    </div>
  );
}
