import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import AntropometriaForm from './AntropometriaForm';

export default function Dashboard({ token, username, onLogout }) {
  const [userPayload, setUserPayload] = useState(null);
  const [role, setRole] = useState('Estudiantes');
  const [activeTab, setActiveTab] = useState('inicio'); // 'inicio' o 'antropometria'
  
  // Sensitive data visibility state
  const [showSensitiveData, setShowSensitiveData] = useState(false);

  // Estados para formulario de plan
  const [pacienteId, setPacienteId] = useState('');
  const [tipoPlan, setTipoPlan] = useState('Balanceado');
  const [planResult, setPlanResult] = useState('');
  const [planError, setPlanError] = useState('');
  const [planLoading, setPlanLoading] = useState(false);
  const [lastCreatedPlan, setLastCreatedPlan] = useState(null);

  // Food Builder States
  const [alimentos, setAlimentos] = useState([]);
  const [foodName, setFoodName] = useState('');
  const [foodQty, setFoodQty] = useState('');
  const [foodMeal, setFoodMeal] = useState('Desayuno');

  // Estados para auditoría (Solo Docentes)
  const [tasks, setTasks] = useState([]);
  const [auditError, setAuditError] = useState('');
  const [auditLoading, setAuditLoading] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null); // Expand task details in audit

  // Quick-Add foods list
  const quickAddFoods = [
    { nombre: 'Huevo Cocido', cantidad: '2 unidades', comida: 'Desayuno', icon: '🍳' },
    { nombre: 'Avena con Leche', cantidad: '1 taza', comida: 'Desayuno', icon: '🥣' },
    { nombre: 'Pechuga de Pollo', cantidad: '150g', comida: 'Almuerzo', icon: '🍗' },
    { nombre: 'Arroz Integral', cantidad: '100g', comida: 'Almuerzo', icon: '🍚' },
    { nombre: 'Salmón a la plancha', cantidad: '150g', comida: 'Cena', icon: '🐟' },
    { nombre: 'Ensalada Mixta', cantidad: '1 plato', comida: 'Almuerzo', icon: '🥗' },
    { nombre: 'Manzana verde', cantidad: '1 unidad', comida: 'Colación', icon: '🍎' }
  ];

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
    if (role === 'Docentes') {
      loadAuditTasks();
    }
  }, [role]);

  // Mask sensitive data dynamically
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
    setAlimentos([...alimentos, {
      nombre: foodName.trim(),
      cantidad: foodQty.trim(),
      comida: foodMeal
    }]);
    setFoodName('');
    setFoodQty('');
  };

  const handleRemoveFood = (index) => {
    setAlimentos(alimentos.filter((_, i) => i !== index));
  };

  const handleQuickAdd = (food) => {
    setAlimentos([...alimentos, {
      nombre: food.nombre,
      cantidad: food.cantidad,
      comida: food.comida
    }]);
  };

  const handleRequestPlan = async (e) => {
    e.preventDefault();
    setPlanResult('');
    setPlanError('');
    setLastCreatedPlan(null);
    
    if (!pacienteId.trim()) {
      setPlanError('Debe ingresar un ID de paciente.');
      return;
    }

    setPlanLoading(true);
    try {
      const data = await apiService.createPlan(token, {
        paciente_id: pacienteId,
        tipo_plan: tipoPlan,
        alimentos: alimentos
      });
      setPlanResult(`¡Plan solicitado! Task ID: ${data.task_id} (Estado: ${data.status})`);
      
      // Guardar el plan recién creado localmente para mostrar el reporte cuando se complete
      setLastCreatedPlan({
        task_id: data.task_id,
        paciente_id: pacienteId,
        tipo_plan: tipoPlan,
        alimentos: [...alimentos],
        estado_actual: 'PENDIENTE'
      });

      // Limpiar formulario
      setPacienteId('');
      setAlimentos([]);
      
      // Iniciar polling para este plan específico
      startPlanPolling(data.task_id);

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

  const startPlanPolling = (taskId) => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const statusData = await apiService.getTaskStatus(token, taskId);
        if (statusData.estado_actual === 'COMPLETADO') {
          clearInterval(interval);
          setPlanResult(`¡El plan nutricional se ha completado e incorporado con éxito!`);
          setLastCreatedPlan(statusData);
          if (role === 'Docentes') loadAuditTasks();
        } else if (statusData.estado_actual === 'FALLIDO' || attempts > 15) {
          clearInterval(interval);
          setPlanError(`El procesamiento del plan falló o se agotó el tiempo de espera.`);
        }
      } catch (e) {
        console.error("Error polling task status:", e);
      }
    }, 2000);
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'row',
      width: '100%',
      minHeight: '85vh',
      background: '#ffffff',
      border: '1px solid hsl(var(--card-border))',
      borderRadius: '24px',
      boxShadow: '0 12px 40px rgba(120, 110, 90, 0.05)',
      overflow: 'hidden',
      margin: '20px 0'
    }} className="dashboard-wrapper">
      
      {/* 1. SIDEBAR NAVIGATION */}
      <div style={{
        width: '280px',
        background: 'rgba(30, 63, 32, 0.02)',
        borderRight: '1px solid hsl(var(--card-border))',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        flexShrink: 0
      }} className="dashboard-sidebar">
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Logo Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.8rem' }}>🌿</span>
            <span style={{ fontSize: '1.4rem', fontWeight: 700, color: 'hsl(var(--primary))', letterSpacing: '-0.02em' }}>
              Portal NutriA
            </span>
          </div>

          {/* User Profile Summary */}
          <div style={{ 
            background: 'hsl(var(--card-bg))', 
            border: '1px solid hsl(var(--card-border))', 
            borderRadius: '16px', 
            padding: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              background: role === 'Docentes' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(96, 165, 250, 0.15)',
              color: role === 'Docentes' ? 'hsl(var(--primary))' : '#3b82f6',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              fontWeight: 700,
              fontSize: '1rem'
            }}>
              {username.substring(0, 2).toUpperCase()}
            </div>
            <div style={{ overflow: 'hidden' }}>
              <p style={{ fontWeight: 600, fontSize: '0.88rem', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {userPayload?.name?.split(' ')[0] || username}
              </p>
              <span style={{ 
                fontSize: '0.75rem', 
                fontWeight: 600, 
                color: role === 'Docentes' ? '#10b981' : '#3b82f6'
              }}>
                {role}
              </span>
            </div>
          </div>

          {/* Menu Items */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button 
              onClick={() => setActiveTab('inicio')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                width: '100%',
                padding: '12px 16px',
                border: 'none',
                borderRadius: '12px',
                background: activeTab === 'inicio' ? 'rgba(30, 63, 32, 0.08)' : 'transparent',
                color: activeTab === 'inicio' ? 'hsl(var(--primary))' : 'hsl(var(--text-secondary))',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.2s ease'
              }}
            >
              <span>🏠</span> Inicio
            </button>

            <button 
              onClick={() => setActiveTab('antropometria')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                width: '100%',
                padding: '12px 16px',
                border: 'none',
                borderRadius: '12px',
                background: activeTab === 'antropometria' ? 'rgba(30, 63, 32, 0.08)' : 'transparent',
                color: activeTab === 'antropometria' ? 'hsl(var(--primary))' : 'hsl(var(--text-secondary))',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.2s ease'
              }}
            >
              <span>⚖️</span> Antropometría
            </button>

            <button 
              onClick={() => setActiveTab('plan')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                width: '100%',
                padding: '12px 16px',
                border: 'none',
                borderRadius: '12px',
                background: activeTab === 'plan' ? 'rgba(30, 63, 32, 0.08)' : 'transparent',
                color: activeTab === 'plan' ? 'hsl(var(--primary))' : 'hsl(var(--text-secondary))',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.2s ease'
              }}
            >
              <span>🍎</span> Plan Nutricional
            </button>
          </div>
        </div>

        {/* Sidebar Footer Logout */}
        <button 
          onClick={onLogout} 
          className="btn btn-secondary" 
          style={{ width: '100%', marginTop: 0, padding: '10px 16px', fontSize: '0.9rem' }}
        >
          Cerrar Sesión
        </button>
      </div>

      {/* 2. MAIN CONTENT AREA */}
      <div style={{
        flex: 1,
        padding: '32px',
        overflowY: 'auto',
        maxHeight: '85vh'
      }} className="dashboard-main-content">

        {activeTab === 'antropometria' && (
          <AntropometriaForm token={token} />
        )}

        {activeTab === 'inicio' && (
          /* TAB 1: INICIO (DASHBOARD PRINCIPAL - PERFIL Y AUDITORÍA) */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <h1 style={{ fontSize: '2rem', textAlign: 'left', margin: 0 }}>Panel de Control NutriA</h1>
              <p style={{ color: 'hsl(var(--text-secondary))', fontSize: '0.95rem' }}>
                Gestiona tu información de perfil de forma segura y accede a los reportes de auditoría.
              </p>
            </div>

            {/* Side-by-side or stacked grid depending on role */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: role === 'Docentes' ? '1.2fr 0.8fr' : '1fr', 
              gap: '24px',
              alignItems: 'start'
            }} className="dashboard-grid">
              
              {/* Left Side: Profile Card */}
              <div className="card" style={{ padding: '24px', margin: 0, width: '100%', borderRadius: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(30, 63, 32, 0.08)', paddingBottom: '8px' }}>
                  <h2 style={{ fontSize: '1.2rem', textAlign: 'left', margin: 0, border: 'none', padding: 0 }}>
                    Información del Usuario
                  </h2>
                  <button 
                    onClick={() => setShowSensitiveData(!showSensitiveData)}
                    style={{
                      background: 'transparent',
                      border: '1px solid hsl(var(--card-border))',
                      borderRadius: '20px',
                      padding: '4px 10px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      color: 'hsl(var(--text-secondary))',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    {showSensitiveData ? '🙈 Ocultar Datos' : '👁️ Mostrar Datos'}
                  </button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px 20px', fontSize: '0.85rem' }}>
                  <div>
                    <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.72rem', textTransform: 'uppercase', marginBottom: '2px' }}>Nombre Completo</p>
                    <p style={{ fontWeight: 600, color: 'hsl(var(--text-primary))', margin: 0 }}>
                      {maskText(userPayload?.name, 'name')}
                    </p>
                  </div>
                  <div>
                    <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.72rem', textTransform: 'uppercase', marginBottom: '2px' }}>Cédula de Identidad</p>
                    <p style={{ fontWeight: 600, color: 'hsl(var(--text-primary))', margin: 0 }}>
                      {maskText(userPayload?.profile, 'cedula')}
                    </p>
                  </div>
                  <div>
                    <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.72rem', textTransform: 'uppercase', marginBottom: '2px' }}>Fecha de Nacimiento</p>
                    <p style={{ fontWeight: 600, color: 'hsl(var(--text-primary))', margin: 0 }}>
                      {maskText(userPayload?.birthdate, 'birthdate')}
                    </p>
                  </div>
                  <div>
                    <p style={{ color: 'hsl(var(--text-muted))', fontSize: '0.72rem', textTransform: 'uppercase', marginBottom: '2px' }}>Correo Electrónico</p>
                    <p style={{ fontWeight: 600, color: 'hsl(var(--text-primary))', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {maskText(userPayload?.email, 'email')}
                    </p>
                  </div>
                </div>
              </div>

              {/* Right Side: Teacher Audit Log */}
              {role === 'Docentes' && (
                <div className="card" style={{ padding: '24px', margin: 0, width: '100%', borderRadius: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(30, 63, 32, 0.08)', paddingBottom: '8px' }}>
                    <h2 style={{ fontSize: '1.2rem', textAlign: 'left', margin: 0, border: 'none', padding: 0 }}>
                      Auditoría de Planes (DynamoDB)
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
                      <div className="spinner" style={{ borderColor: 'rgba(30,63,32,0.1)', borderTopColor: 'hsl(var(--primary))' }}></div>
                    </div>
                  ) : tasks.length === 0 ? (
                    <p style={{ textAlign: 'center', color: 'hsl(var(--text-muted))', padding: '16px 0' }}>
                      No hay tareas registradas en la base de datos.
                    </p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '280px', overflowY: 'auto' }}>
                      {tasks.map((task) => (
                        <div 
                          key={task.task_id} 
                          onClick={() => setSelectedTask(selectedTask?.task_id === task.task_id ? null : task)}
                          style={{ 
                            background: 'rgba(30, 63, 32, 0.02)', 
                            border: '1px solid hsl(var(--card-border))', 
                            borderRadius: '8px', 
                            padding: '10px 12px',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            borderColor: selectedTask?.task_id === task.task_id ? 'hsl(var(--primary))' : 'hsl(var(--card-border))'
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <p style={{ fontSize: '0.8rem', fontWeight: 600, margin: 0 }}>Paciente: {task.paciente_id || 'N/A'}</p>
                              <p style={{ fontSize: '0.72rem', color: 'hsl(var(--text-muted))', marginTop: '2px', margin: 0 }}>
                                ID: {task.task_id.substring(0, 8)}... ({task.tipo_plan})
                              </p>
                            </div>
                            <span style={{ 
                              fontSize: '0.72rem', 
                              fontWeight: 700, 
                              padding: '2px 8px', 
                              borderRadius: '12px',
                              background: task.status === 'COMPLETADO' ? '#ecfdf5' : '#fff7ed',
                              color: task.status === 'COMPLETADO' ? '#047857' : '#c2410c'
                            }}>
                              {task.status}
                            </span>
                          </div>

                          {/* Expanded details */}
                          {selectedTask?.task_id === task.task_id && (
                            <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid rgba(0,0,0,0.05)', fontSize: '0.75rem', color: 'hsl(var(--text-secondary))', animation: 'fadeIn 0.2s ease-out' }}>
                              <p style={{ margin: '2px 0' }}><strong>Creado:</strong> {task.created_at || 'N/A'}</p>
                              {task.alimentos && task.alimentos.length > 0 ? (
                                <div style={{ marginTop: '6px' }}>
                                  <strong>Alimentos en el Menú:</strong>
                                  <ul style={{ paddingLeft: '14px', margin: '2px 0 0 0' }}>
                                    {task.alimentos.map((al, idx) => (
                                      <li key={idx}>{al.nombre} ({al.cantidad}) - {al.comida}</li>
                                    ))}
                                  </ul>
                                </div>
                              ) : (
                                <p style={{ margin: '4px 0', color: 'hsl(var(--text-muted))', fontStyle: 'italic' }}>Sin alimentos asociados.</p>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* DEVELOPER TOOLS COLLAPSIBLE PANEL */}
            <details style={{ 
              background: '#fdfdfc',
              border: '1px solid hsl(var(--card-border))',
              borderRadius: '12px',
              padding: '12px',
              cursor: 'pointer',
              marginTop: '16px'
            }}>
              <summary style={{ fontSize: '0.8rem', fontWeight: 600, color: 'hsl(var(--text-secondary))', userSelect: 'none' }}>
                🛠️ Herramientas de Desarrollador
              </summary>
              <div style={{ marginTop: '12px', cursor: 'default' }} onClick={(e) => e.stopPropagation()}>
                <p style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', margin: '0 0 8px 0' }}>
                  Token JWT activo para pruebas en Swagger / Postman:
                </p>
                <div className="token-container" style={{ margin: 0 }}>{token}</div>
              </div>
            </details>

          </div>
        )}

        {activeTab === 'plan' && (
          /* TAB 3: PLAN NUTRICIONAL (FORMULARIO Y FOOD BUILDER) */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <h1 style={{ fontSize: '2rem', textAlign: 'left', margin: 0 }}>Generación de Plan Nutricional</h1>
              <p style={{ color: 'hsl(var(--text-secondary))', fontSize: '0.95rem' }}>
                Solicita y calcula planes alimenticios personalizados en segundo plano ingresando la identificación del paciente y detallando su menú diario.
              </p>
            </div>

            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: lastCreatedPlan ? '1.2fr 0.8fr' : '1fr', 
              gap: '24px',
              alignItems: 'start'
            }} className="dashboard-grid">
              
              {/* Left Side: Generar Plan Card */}
              <div className="card" style={{ padding: '24px', margin: 0, width: '100%', borderRadius: '20px' }}>
                <h2 style={{ fontSize: '1.2rem', textAlign: 'left', marginBottom: '16px', borderBottom: '1px solid rgba(30, 63, 32, 0.08)', paddingBottom: '8px' }}>
                  Generar Plan Nutricional
                </h2>

                {planError && <div className="error-msg">{planError}</div>}
                {planResult && <div className="success-msg">{planResult}</div>}
                
                <form onSubmit={handleRequestPlan} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label htmlFor="pacienteId">Identificación Paciente</label>
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
                      <label htmlFor="tipoPlan">Tipo de Plan</label>
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
                  </div>

                  {/* FOOD BUILDER SUBFORM */}
                  <div style={{ 
                    background: 'rgba(30, 63, 32, 0.02)',
                    border: '1px solid hsl(var(--card-border))',
                    borderRadius: '12px',
                    padding: '16px',
                    marginTop: '8px'
                  }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'hsl(var(--text-secondary))', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Añadir Alimentos al Menú
                    </span>

                    {/* Quick-Add Chips */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', margin: '12px 0 16px 0' }}>
                      {quickAddFoods.map((qFood, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => handleQuickAdd(qFood)}
                          disabled={planLoading}
                          style={{
                            background: '#ffffff',
                            border: '1px solid hsl(var(--card-border))',
                            borderRadius: '20px',
                            padding: '4px 10px',
                            fontSize: '0.72rem',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            color: 'hsl(var(--text-primary))',
                            transition: 'all 0.15s ease'
                          }}
                          onMouseOver={(e) => e.currentTarget.style.borderColor = 'hsl(var(--primary))'}
                          onMouseOut={(e) => e.currentTarget.style.borderColor = 'hsl(var(--card-border))'}
                        >
                          <span>{qFood.icon}</span> {qFood.nombre} ({qFood.cantidad})
                        </button>
                      ))}
                    </div>

                    {/* Custom Food Row Input */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr 1fr', gap: '10px', alignItems: 'end' }}>
                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ fontSize: '0.7rem' }}>Nombre Alimento</label>
                        <input
                          type="text"
                          value={foodName}
                          onChange={(e) => setFoodName(e.target.value)}
                          placeholder="ej. Filete de Pescado"
                          disabled={planLoading}
                          style={{ padding: '8px 12px', fontSize: '0.85rem' }}
                        />
                      </div>
                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ fontSize: '0.7rem' }}>Porción/Cant.</label>
                        <input
                          type="text"
                          value={foodQty}
                          onChange={(e) => setFoodQty(e.target.value)}
                          placeholder="ej. 150g"
                          disabled={planLoading}
                          style={{ padding: '8px 12px', fontSize: '0.85rem' }}
                        />
                      </div>
                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ fontSize: '0.7rem' }}>Momento Comida</label>
                        <select
                          value={foodMeal}
                          onChange={(e) => setFoodMeal(e.target.value)}
                          disabled={planLoading}
                          style={{ padding: '8px 12px', fontSize: '0.85rem' }}
                        >
                          <option value="Desayuno">Desayuno</option>
                          <option value="Almuerzo">Almuerzo</option>
                          <option value="Cena">Cena</option>
                          <option value="Colación">Colación</option>
                        </select>
                      </div>
                    </div>
                    
                    <button 
                      type="button" 
                      onClick={handleAddFood} 
                      className="btn btn-secondary" 
                      disabled={planLoading}
                      style={{ marginTop: '12px', padding: '8px 12px', fontSize: '0.8rem', width: 'auto' }}
                    >
                      + Agregar a la Lista
                    </button>

                    {/* List of current foods */}
                    {alimentos.length > 0 && (
                      <div style={{ marginTop: '16px', maxHeight: '160px', overflowY: 'auto', borderTop: '1px solid rgba(0,0,0,0.05)', paddingTop: '12px' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                          <thead>
                            <tr style={{ borderBottom: '1px solid rgba(0,0,0,0.08)' }}>
                              <th style={{ padding: '6px', color: 'hsl(var(--text-muted))' }}>Alimento</th>
                              <th style={{ padding: '6px', color: 'hsl(var(--text-muted))' }}>Cantidad</th>
                              <th style={{ padding: '6px', color: 'hsl(var(--text-muted))' }}>Comida</th>
                              <th style={{ padding: '6px', textAlign: 'center' }} />
                            </tr>
                          </thead>
                          <tbody>
                            {alimentos.map((item, idx) => (
                              <tr key={idx} style={{ borderBottom: '1px solid rgba(0,0,0,0.03)' }}>
                                <td style={{ padding: '6px', fontWeight: 500 }}>{item.nombre}</td>
                                <td style={{ padding: '6px' }}>{item.cantidad}</td>
                                <td style={{ padding: '6px' }}>
                                  <span style={{
                                    fontSize: '0.7rem',
                                    padding: '2px 6px',
                                    borderRadius: '8px',
                                    background: item.comida === 'Desayuno' ? '#eff6ff' : item.comida === 'Almuerzo' ? '#ecfdf5' : item.comida === 'Cena' ? '#f5f3ff' : '#fff7ed',
                                    color: item.comida === 'Desayuno' ? '#1d4ed8' : item.comida === 'Almuerzo' ? '#047857' : item.comida === 'Cena' ? '#6d28d9' : '#c2410c'
                                  }}>
                                    {item.comida}
                                  </span>
                                </td>
                                <td style={{ padding: '6px', textAlign: 'center' }}>
                                  <button 
                                    type="button" 
                                    onClick={() => handleRemoveFood(idx)}
                                    style={{ border: 'none', background: 'transparent', color: '#ef4444', cursor: 'pointer', fontSize: '0.9rem' }}
                                    title="Quitar"
                                  >
                                    ✕
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>

                  <button type="submit" className="btn" disabled={planLoading || alimentos.length === 0} style={{ marginTop: '8px' }}>
                    {planLoading ? <div className="spinner"></div> : `Solicitar Plan (${alimentos.length} alimentos)`}
                  </button>
                </form>
              </div>

              {/* Right Side: Generated Plan Report */}
              {lastCreatedPlan && (
                <div className="card" style={{ padding: '24px', margin: 0, width: '100%', borderRadius: '20px', border: '1px solid rgba(16, 185, 129, 0.25)', background: 'rgba(16, 185, 129, 0.01)', animation: 'fadeIn 0.3s ease-out' }}>
                  <h2 style={{ fontSize: '1.2rem', textAlign: 'left', marginBottom: '14px', borderBottom: '1px solid rgba(30, 63, 32, 0.08)', paddingBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Reporte Plan Nutricional</span>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '12px',
                      background: lastCreatedPlan.estado_actual === 'COMPLETADO' ? '#ecfdf5' : '#fff7ed',
                      color: lastCreatedPlan.estado_actual === 'COMPLETADO' ? '#047857' : '#c2410c'
                    }}>
                      {lastCreatedPlan.estado_actual}
                    </span>
                  </h2>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.85rem' }}>
                    <p style={{ margin: 0 }}><strong>ID Paciente:</strong> {lastCreatedPlan.paciente_id}</p>
                    <p style={{ margin: 0 }}><strong>Tipo de Dieta:</strong> {lastCreatedPlan.tipo_plan}</p>
                    
                    {lastCreatedPlan.alimentos && lastCreatedPlan.alimentos.length > 0 ? (
                      <div style={{ marginTop: '8px' }}>
                        <strong style={{ display: 'block', marginBottom: '6px' }}>Menú Estructurado:</strong>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {['Desayuno', 'Almuerzo', 'Cena', 'Colación'].map((meal) => {
                            const mealFoods = lastCreatedPlan.alimentos.filter(f => f.comida === meal);
                            if (mealFoods.length === 0) return null;
                            return (
                              <div key={meal} style={{ borderLeft: '3px solid hsl(var(--primary))', paddingLeft: '8px', margin: '4px 0' }}>
                                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'hsl(var(--primary))', textTransform: 'uppercase' }}>{meal}</span>
                                <ul style={{ paddingLeft: '14px', margin: '2px 0 0 0', color: 'hsl(var(--text-primary))' }}>
                                  {mealFoods.map((f, i) => (
                                    <li key={i}>{f.nombre} ({f.cantidad})</li>
                                  ))}
                                </ul>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ) : (
                      <p style={{ color: 'hsl(var(--text-muted))', fontStyle: 'italic', margin: 0 }}>No se cargaron alimentos para este plan.</p>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* DEVELOPER TOOLS COLLAPSIBLE PANEL */}
            <details style={{ 
              background: '#fdfdfc',
              border: '1px solid hsl(var(--card-border))',
              borderRadius: '12px',
              padding: '12px',
              cursor: 'pointer',
              marginTop: '16px'
            }}>
              <summary style={{ fontSize: '0.8rem', fontWeight: 600, color: 'hsl(var(--text-secondary))', userSelect: 'none' }}>
                🛠️ Herramientas de Desarrollador
              </summary>
              <div style={{ marginTop: '12px', cursor: 'default' }} onClick={(e) => e.stopPropagation()}>
                <p style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', margin: '0 0 8px 0' }}>
                  Token JWT activo para pruebas en Swagger / Postman:
                </p>
                <div className="token-container" style={{ margin: 0 }}>{token}</div>
              </div>
            </details>

          </div>
        )}

      </div>

    </div>
  );
}
