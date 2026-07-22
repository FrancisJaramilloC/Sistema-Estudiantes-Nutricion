import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import Sidebar from './Sidebar';
import AntropometriaDashboard from './AntropometriaDashboard';
import UserManagement from './UserManagement';
import AccessibilityButton from './AccessibilityButton';
import HeartRateDashboard from './HeartRateDashboard';
import PlanAlimenticio from './PlanAlimenticio';
import AuditoriaPanel from './AuditoriaPanel';

export default function Dashboard({ token, username, onLogout, currentHash }) {
  const [userPayload, setUserPayload] = useState(null);
  const [role, setRole] = useState('Estudiantes');
  const [activeTab, setActiveTab] = useState('inicio');
  const [showSensitiveData, setShowSensitiveData] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 768) setSidebarOpen(true);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const [tasks, setTasks] = useState([]);
  const [auditError, setAuditError] = useState('');
  const [auditLoading, setAuditLoading] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);

  const [loginEvents, setLoginEvents] = useState([]);
  const [loginAuditError, setLoginAuditError] = useState('');
  const [loginAuditLoading, setLoginAuditLoading] = useState(false);

  useEffect(() => {
    if (currentHash === '#/dashboard/antropometria') setActiveTab('antropometria');
    else if (currentHash === '#/dashboard/plan-nutricional') setActiveTab('plan');
    else if (currentHash === '#/dashboard/usuarios' && role === 'Docentes') setActiveTab('usuarios');
    else if (currentHash === '#/dashboard/auditoria' && role === 'Docentes') setActiveTab('auditoria');
    else if (currentHash === '#/dashboard/ritmo-cardiaco') setActiveTab('ritmo');
    else setActiveTab('inicio');
  }, [currentHash, role]);

  useEffect(() => {
    if (token) {
      try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
          window.atob(base64).split('').map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')
        );
        const payload = JSON.parse(jsonPayload);
        setUserPayload(payload);
        setRole(payload['cognito:groups']?.includes('Docentes') ? 'Docentes' : 'Estudiantes');
      } catch (e) {
        console.error('Error decodificando token', e);
      }
    }
  }, [token]);

  const loadAuditTasks = async () => {
    if (role !== 'Docentes') return;
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

  const loadLoginAudit = async () => {
    if (role !== 'Docentes') return;
    setLoginAuditLoading(true);
    setLoginAuditError('');
    try {
      const data = await apiService.getLoginAudit(token);
      setLoginEvents(data || []);
    } catch (err) {
      setLoginAuditError(err.message || 'No autorizado para ver auditoría de accesos.');
    } finally {
      setLoginAuditLoading(false);
    }
  };

  useEffect(() => {
    if (role === 'Docentes') {
      loadAuditTasks();
      loadLoginAudit();
    }
  }, [role]);

  useEffect(() => {
    if (role === 'Docentes') loadAuditTasks();
  }, [role]);

  const maskText = (text, type) => {
    if (!text) return 'Cargando...';
    if (showSensitiveData) return text;
    switch (type) {
      case 'name':
        return text.split(' ').map(part => {
          if (part.length <= 2) return part;
          return part[0] + '•'.repeat(part.length - 2) + part[part.length - 1];
        }).join(' ');
      case 'cedula':
        if (text.length <= 6) return '••••••';
        return text.substring(0, 3) + '•'.repeat(text.length - 6) + text.substring(text.length - 3);
      case 'birthdate':
        return text.replace(/-(\d{2})-(\d{2})$/, '-••-••');
      case 'email':
        const parts = text.split('@');
        if (parts.length < 2) return text;
        const user = parts[0];
        const domain = parts[1];
        if (user.length <= 2) return '••@' + domain;
        return user.substring(0, 2) + '•'.repeat(user.length - 2) + '@' + domain;
      default:
        return '••••••••';
    }
  };

  return (
    <div className={`dashboard-wrapper ${sidebarOpen ? '' : 'sidebar-collapsed'}`}>
      <Sidebar username={username} role={role} userPayload={userPayload} activeTab={activeTab} onLogout={onLogout} sidebarOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      <div className="dashboard-main">
        <div className="dashboard-topbar">
          <button className="hamburger-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
            ☰
          </button>
        </div>
        {activeTab === 'antropometria' && <AntropometriaDashboard token={token} />}
        {activeTab === 'plan' && <PlanAlimenticio token={token} />}
        {activeTab === 'ritmo' && <HeartRateDashboard token={token} userPayload={userPayload} role={role} />}

        {activeTab === 'usuarios' && role === 'Docentes' && (
          <UserManagement token={token} currentUsername={username} />
        )}

        {activeTab === 'auditoria' && role === 'Docentes' && (
          <AuditoriaPanel token={token} />
        )}

        {activeTab === 'inicio' && (
          <div className="dashboard-content">
            <div className="content-header">
              <h1>Panel de Control NutriA</h1>
              <p>Gestiona tu información de perfil y accede a los reportes de auditoría.</p>
            </div>

            <div className="dashboard-grid">
              <div className="card profile-card">
                <div className="profile-header">
                  <h2>Información del Usuario</h2>
                  <button onClick={() => setShowSensitiveData(!showSensitiveData)} className="toggle-data-btn">
                    {showSensitiveData ? 'Ocultar Datos' : 'Mostrar Datos'}
                  </button>
                </div>
                <div className="profile-grid">
                  <div>
                    <span className="profile-label">Nombre Completo</span>
                    <p className="profile-value">{maskText(userPayload?.name, 'name')}</p>
                  </div>
                  <div>
                    <span className="profile-label">Cédula</span>
                    <p className="profile-value">{maskText(userPayload?.profile, 'cedula')}</p>
                  </div>
                  <div>
                    <span className="profile-label">Fecha de Nacimiento</span>
                    <p className="profile-value">{maskText(userPayload?.birthdate, 'birthdate')}</p>
                  </div>
                  <div>
                    <span className="profile-label">Correo Electrónico</span>
                    <p className="profile-value">{maskText(userPayload?.email, 'email')}</p>
                  </div>
                </div>
              </div>

              {role === 'Docentes' && (
                <div className="card audit-card">
                  <div className="profile-header">
                    <h2>Auditoría de Planes</h2>
                    <button onClick={loadAuditTasks} className="btn btn-secondary" style={{ width: 'auto', padding: '4px 10px', fontSize: '0.8rem' }} disabled={auditLoading}>
                      Refrescar
                    </button>
                  </div>
                  {auditError && <div className="error-msg">{auditError}</div>}
                  {auditLoading ? (
                    <div className="spinner-container"><div className="spinner" style={{ borderColor: 'rgba(30,63,32,0.1)', borderTopColor: 'hsl(var(--primary))' }}></div></div>
                  ) : tasks.length === 0 ? (
                    <p className="empty-state">No hay tareas registradas.</p>
                  ) : (
                    <div className="task-list">
                      {tasks.map((task) => (
                        <div key={task.task_id} onClick={() => setSelectedTask(selectedTask?.task_id === task.task_id ? null : task)}
                          className={`task-item ${selectedTask?.task_id === task.task_id ? 'task-selected' : ''}`}>
                          <div className="task-summary">
                            <div>
                              <p className="task-patient">Paciente: {task.paciente_id || 'N/A'}</p>
                              <p className="task-id">{task.tipo_plan}</p>
                            </div>
                            <span className={`task-status status-${task.estado_actual?.toLowerCase()}`}>{task.estado_actual}</span>
                          </div>
                          {selectedTask?.task_id === task.task_id && (
                            <div className="task-detail">
                              <p><strong>Creado:</strong> {task.created_at || 'N/A'}</p>
                              {task.alimentos?.length > 0 ? (
                                <ul>{task.alimentos.map((al, i) => <li key={i}>{al.nombre} ({al.cantidad}) - {al.comida}</li>)}</ul>
                              ) : <p className="empty-state">Sin alimentos.</p>}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {role === 'Docentes' && (
                <div className="card audit-card">
                  <div className="profile-header">
                    <h2>Auditoría de Accesos</h2>
                    <button onClick={loadLoginAudit} className="btn btn-secondary" style={{ width: 'auto', padding: '4px 10px', fontSize: '0.8rem' }} disabled={loginAuditLoading}>
                      Refrescar
                    </button>
                  </div>
                  {loginAuditError && <div className="error-msg">{loginAuditError}</div>}
                  {loginAuditLoading ? (
                    <div className="spinner-container"><div className="spinner" style={{ borderColor: 'rgba(30,63,32,0.1)', borderTopColor: 'hsl(var(--primary))' }}></div></div>
                  ) : loginEvents.length === 0 ? (
                    <p className="empty-state">No hay eventos de acceso registrados.</p>
                  ) : (
                    <div className="task-list">
                      {loginEvents.map((event) => (
                        <div key={event.event_id} className="task-item">
                          <div className="task-summary">
                            <div>
                              <p className="task-patient">{event.username}</p>
                              <p className="task-id">{new Date(event.timestamp + 'Z').toLocaleString('es-EC')}{event.reason ? ` — ${event.reason}` : ''}</p>
                            </div>
                            <span className={`task-status status-${event.success ? 'completado' : 'fallido'}`}>
                              {event.success ? 'EXITOSO' : 'FALLIDO'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

      </div>
      <AccessibilityButton />
    </div>
  );
}
