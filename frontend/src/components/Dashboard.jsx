import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import Sidebar from './Sidebar';
import AntropometriaDashboard from './AntropometriaDashboard';
import HeartRateDashboard from './HeartRateDashboard';

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

  const [pacienteId, setPacienteId] = useState('');
  const [tipoPlan, setTipoPlan] = useState('Balanceado');
  const [planResult, setPlanResult] = useState('');
  const [planError, setPlanError] = useState('');
  const [planLoading, setPlanLoading] = useState(false);
  const [lastCreatedPlan, setLastCreatedPlan] = useState(null);
  const [alimentos, setAlimentos] = useState([]);
  const [foodName, setFoodName] = useState('');
  const [foodQty, setFoodQty] = useState('');
  const [foodMeal, setFoodMeal] = useState('Desayuno');

  const [tasks, setTasks] = useState([]);
  const [auditError, setAuditError] = useState('');
  const [auditLoading, setAuditLoading] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);

  const quickAddFoods = [
    { nombre: 'Huevo Cocido', cantidad: '2 unidades', comida: 'Desayuno' },
    { nombre: 'Avena con Leche', cantidad: '1 taza', comida: 'Desayuno' },
    { nombre: 'Pechuga de Pollo', cantidad: '150g', comida: 'Almuerzo' },
    { nombre: 'Arroz Integral', cantidad: '100g', comida: 'Almuerzo' },
    { nombre: 'Salmón a la plancha', cantidad: '150g', comida: 'Cena' },
    { nombre: 'Ensalada Mixta', cantidad: '1 plato', comida: 'Almuerzo' },
    { nombre: 'Manzana verde', cantidad: '1 unidad', comida: 'Colación' },
  ];

  useEffect(() => {
    if (currentHash === '#/dashboard/antropometria') setActiveTab('antropometria');
    else if (currentHash === '#/dashboard/plan-nutricional') setActiveTab('plan');
    else if (currentHash === '#/dashboard/ritmo-cardiaco') setActiveTab('ritmo');
    else setActiveTab('inicio');
  }, [currentHash]);

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

  const handleAddFood = (e) => {
    e.preventDefault();
    if (!foodName.trim() || !foodQty.trim()) return;
    setAlimentos([...alimentos, { nombre: foodName.trim(), cantidad: foodQty.trim(), comida: foodMeal }]);
    setFoodName('');
    setFoodQty('');
  };

  const handleRemoveFood = (index) => setAlimentos(alimentos.filter((_, i) => i !== index));
  const handleQuickAdd = (food) => setAlimentos([...alimentos, { ...food }]);

  const startPlanPolling = (taskId) => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const statusData = await apiService.getTaskStatus(token, taskId);
        if (statusData.estado_actual === 'COMPLETADO') {
          clearInterval(interval);
          setPlanResult('¡El plan nutricional se ha completado!');
          setLastCreatedPlan(statusData);
          if (role === 'Docentes') loadAuditTasks();
        } else if (statusData.estado_actual === 'FALLIDO' || attempts > 15) {
          clearInterval(interval);
          setPlanError('El procesamiento falló o se agotó el tiempo de espera.');
        }
      } catch (e) {
        console.error("Error polling task status:", e);
      }
    }, 2000);
  };

  const handleRequestPlan = async (e) => {
    e.preventDefault();
    setPlanResult('');
    setPlanError('');
    setLastCreatedPlan(null);
    if (!pacienteId.trim()) { setPlanError('Debe ingresar un ID de paciente.'); return; }
    setPlanLoading(true);
    try {
      const data = await apiService.createPlan(token, { paciente_id: pacienteId, tipo_plan: tipoPlan, alimentos });
      setPlanResult('¡Plan solicitado! Estamos procesando tu solicitud...');
      setLastCreatedPlan({ task_id: data.task_id, paciente_id: pacienteId, tipo_plan: tipoPlan, alimentos: [...alimentos], estado_actual: 'PENDIENTE' });
      setPacienteId('');
      setAlimentos([]);
      startPlanPolling(data.task_id);
      if (role === 'Docentes') setTimeout(loadAuditTasks, 1500);
    } catch (err) {
      setPlanError(err.message || 'Error al solicitar el plan.');
    } finally {
      setPlanLoading(false);
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
        {activeTab === 'ritmo' && <HeartRateDashboard token={token} userPayload={userPayload} role={role} />}

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
                    {showSensitiveData ? '🙈 Ocultar' : '👁️ Mostrar'}
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
            </div>

            <details className="dev-tools">
              <summary>🛠️ Herramientas de Desarrollador</summary>
              <div><p>Token JWT activo:</p><div className="token-container">{token}</div></div>
            </details>
          </div>
        )}

        {activeTab === 'plan' && (
          <div className="dashboard-content">
            <div className="content-header">
              <h1>Generación de Plan Nutricional</h1>
              <p>Solicita planes alimenticios personalizados detallando el menú diario del paciente.</p>
            </div>

            <div className="dashboard-grid">
              <div className="card plan-form-card">
                <h2>Generar Plan Nutricional</h2>
                {planError && <div className="error-msg">{planError}</div>}
                {planResult && <div className="success-msg">{planResult}</div>}
                <form onSubmit={handleRequestPlan}>
                  <div className="inline-fields">
                    <div className="form-group">
                      <label>Identificación Paciente</label>
                      <input type="text" value={pacienteId} onChange={(e) => setPacienteId(e.target.value)} placeholder="ej. PAC-983" disabled={planLoading} required />
                    </div>
                    <div className="form-group">
                      <label>Tipo de Plan</label>
                      <select value={tipoPlan} onChange={(e) => setTipoPlan(e.target.value)} disabled={planLoading}>
                        <option value="Balanceado">Balanceado</option>
                        <option value="Keto (Cetogénico)">Keto (Cetogénico)</option>
                        <option value="Vegano">Vegano</option>
                        <option value="Hiperproteico">Hiperproteico</option>
                      </select>
                    </div>
                  </div>

                  <div className="food-builder">
                    <span className="food-builder-title">Añadir Alimentos al Menú</span>
                    <div className="quick-add-chips">
                      {quickAddFoods.map((qFood, idx) => (
                        <button key={idx} type="button" onClick={() => handleQuickAdd(qFood)} disabled={planLoading} className="chip">
                          {qFood.nombre} ({qFood.cantidad})
                        </button>
                      ))}
                    </div>
                    <div className="food-input-row">
                      <input type="text" value={foodName} onChange={(e) => setFoodName(e.target.value)} placeholder="Nombre del alimento" disabled={planLoading} />
                      <input type="text" value={foodQty} onChange={(e) => setFoodQty(e.target.value)} placeholder="Cantidad" disabled={planLoading} />
                      <select value={foodMeal} onChange={(e) => setFoodMeal(e.target.value)} disabled={planLoading}>
                        <option value="Desayuno">Desayuno</option>
                        <option value="Almuerzo">Almuerzo</option>
                        <option value="Cena">Cena</option>
                        <option value="Colación">Colación</option>
                      </select>
                      <button type="button" onClick={handleAddFood} className="btn btn-secondary" disabled={planLoading}>+</button>
                    </div>

                    {alimentos.length > 0 && (
                      <table className="food-table">
                        <thead><tr><th>Alimento</th><th>Cantidad</th><th>Comida</th><th></th></tr></thead>
                        <tbody>
                          {alimentos.map((item, idx) => (
                            <tr key={idx}>
                              <td>{item.nombre}</td><td>{item.cantidad}</td>
                              <td><span className={`food-meal-badge meal-${item.comida.toLowerCase()}`}>{item.comida}</span></td>
                              <td><button type="button" onClick={() => handleRemoveFood(idx)} className="remove-btn">✕</button></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>

                  <div className="form-actions">
                    <button type="submit" className="btn" disabled={planLoading || alimentos.length === 0}>
                      {planLoading ? <div className="spinner"></div> : `Generar Plan (${alimentos.length} alimentos)`}
                    </button>
                    {lastCreatedPlan && (
                      <button
                        type="button"
                        className="btn btn-pdf"
                        disabled={lastCreatedPlan.estado_actual !== 'COMPLETADO'}
                        onClick={() => apiService.downloadPlanPdf(token, lastCreatedPlan.task_id)}
                      >
                        Descargar PDF
                      </button>
                    )}
                  </div>
                </form>
              </div>

              {lastCreatedPlan && (
                <div className="card plan-report-card">
                  <div className="profile-header">
                    <h2>Reporte del Plan</h2>
                    <div className="report-header-actions">
                      <span className={`task-status status-${lastCreatedPlan.estado_actual?.toLowerCase()}`}>{lastCreatedPlan.estado_actual}</span>
                    </div>
                  </div>
                  <p><strong>Paciente:</strong> {lastCreatedPlan.paciente_id}</p>
                  <p><strong>Dieta:</strong> {lastCreatedPlan.tipo_plan}</p>
                  {lastCreatedPlan.alimentos?.length > 0 ? (
                    <div className="meal-report">
                      {['Desayuno', 'Almuerzo', 'Cena', 'Colación'].map((meal) => {
                        const items = lastCreatedPlan.alimentos.filter(f => f.comida === meal);
                        if (!items.length) return null;
                        return (
                          <div key={meal} className="meal-section">
                            <span className="meal-title">{meal}</span>
                            <ul>{items.map((f, i) => <li key={i}>{f.nombre} ({f.cantidad})</li>)}</ul>
                          </div>
                        );
                      })}
                    </div>
                  ) : <p className="empty-state">Sin alimentos.</p>}
                </div>
              )}
            </div>

            <details className="dev-tools">
              <summary>🛠️ Herramientas de Desarrollador</summary>
              <div><p>Token JWT activo:</p><div className="token-container">{token}</div></div>
            </details>
          </div>
        )}
      </div>
    </div>
  );
}
