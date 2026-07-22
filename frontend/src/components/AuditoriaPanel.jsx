import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

const EVENT_TYPES = [
  { value: '', label: 'Todos los eventos' },
  { value: 'LOGIN_SUCCESS', label: 'Inicio de sesión exitoso' },
  { value: 'LOGIN_FAILED', label: 'Inicio de sesión fallido' },
  { value: 'CREATE_PATIENT', label: 'Paciente creado' },
  { value: 'UPDATE_PATIENT', label: 'Paciente actualizado' },
  { value: 'CREATE_PLAN', label: 'Plan creado' },
  { value: 'UPDATE_PLAN', label: 'Plan actualizado' },
  { value: 'DELETE_PLAN', label: 'Plan eliminado' },
  { value: 'CREATE_USER', label: 'Usuario creado' },
  { value: 'GENERAR_SUGERENCIA', label: 'Sugerencia generada' },
  { value: 'ACEPTAR_SUGERENCIA', label: 'Sugerencia aceptada' },
  { value: 'GENERAR_REPORTE', label: 'Reporte generado' },
];

const EVENT_COLORS = {
  LOGIN_SUCCESS: { bg: '#dcfce7', color: '#166534' },
  LOGIN_FAILED: { bg: '#fef2f2', color: '#991b1b' },
  CREATE_PATIENT: { bg: '#eff6ff', color: '#1d4ed8' },
  UPDATE_PATIENT: { bg: '#eff6ff', color: '#1d4ed8' },
  CREATE_PLAN: { bg: '#f5f3ff', color: '#6d28d9' },
  UPDATE_PLAN: { bg: '#f5f3ff', color: '#6d28d9' },
  DELETE_PLAN: { bg: '#fef2f2', color: '#991b1b' },
  CREATE_USER: { bg: '#ecfdf5', color: '#047857' },
  GENERAR_SUGERENCIA: { bg: '#fff7ed', color: '#c2410c' },
  ACEPTAR_SUGERENCIA: { bg: '#ecfdf5', color: '#047857' },
  GENERAR_REPORTE: { bg: '#f5f3ff', color: '#6d28d9' },
};

export default function AuditoriaPanel({ token }) {
  const [eventos, setEventos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [filtroTipo, setFiltroTipo] = useState('');
  const [filtroUsuario, setFiltroUsuario] = useState('');
  const [filtroFechaDesde, setFiltroFechaDesde] = useState('');
  const [filtroFechaHasta, setFiltroFechaHasta] = useState('');
  const [ultimaActualizacion, setUltimaActualizacion] = useState(null);

  const loadEventos = async () => {
    setLoading(true);
    setError('');
    try {
      const filtros = {};
      if (filtroTipo) filtros.event_type = filtroTipo;
      if (filtroUsuario.trim()) filtros.usuario = filtroUsuario.trim();
      if (filtroFechaDesde) filtros.fecha_desde = filtroFechaDesde;
      if (filtroFechaHasta) filtros.fecha_hasta = filtroFechaHasta;
      filtros.limite = 100;
      const data = await apiService.getAuditEvents(token, filtros);
      setEventos(data || []);
      setUltimaActualizacion(new Date());
    } catch (err) {
      setError(err.message || 'Error al cargar eventos de auditoría.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) loadEventos();
  }, [token]);

  const handleBuscar = () => {
    loadEventos();
  };

  const limpiarFiltros = () => {
    setFiltroTipo('');
    setFiltroUsuario('');
    setFiltroFechaDesde('');
    setFiltroFechaHasta('');
  };

  const getBadgeStyle = (eventType, success) => {
    if (success === false || success === 'false') {
      return { background: '#fef2f2', color: '#991b1b' };
    }
    if (success === true || success === 'true') {
      return { background: '#dcfce7', color: '#166534' };
    }
    const colors = EVENT_COLORS[eventType];
    if (colors) return { background: colors.bg, color: colors.color };
    return { background: 'rgba(30,63,32,0.05)', color: 'hsl(var(--text-secondary))' };
  };

  return (
    <div className="dashboard-content">
      <div className="content-header" style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Panel de Auditoría</h1>
          <p>Registro ampliado de eventos del sistema con filtros por tipo, usuario y rango de fechas.</p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {ultimaActualizacion && (
            <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))' }}>
              Última act.: {ultimaActualizacion.toLocaleTimeString('es-EC')}
            </span>
          )}
          <button onClick={loadEventos} className="toggle-data-btn" disabled={loading}>
            {loading ? 'Cargando...' : 'Refrescar'}
          </button>
        </div>
      </div>

      <div className="card" style={{ padding: '20px', marginBottom: '0' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 0.8fr 0.8fr auto auto', gap: '10px', alignItems: 'end' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Tipo de Evento</label>
            <select value={filtroTipo} onChange={(e) => setFiltroTipo(e.target.value)} style={{ padding: '8px 12px', fontSize: '0.85rem' }}>
              {EVENT_TYPES.map((et) => (
                <option key={et.value} value={et.value}>{et.label}</option>
              ))}
            </select>
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Usuario / Actor</label>
            <input
              type="text"
              value={filtroUsuario}
              onChange={(e) => setFiltroUsuario(e.target.value)}
              placeholder="Buscar por usuario..."
              style={{ padding: '8px 12px', fontSize: '0.85rem' }}
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Fecha Desde</label>
            <input
              type="date"
              value={filtroFechaDesde}
              onChange={(e) => setFiltroFechaDesde(e.target.value)}
              style={{ padding: '8px 12px', fontSize: '0.85rem' }}
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Fecha Hasta</label>
            <input
              type="date"
              value={filtroFechaHasta}
              onChange={(e) => setFiltroFechaHasta(e.target.value)}
              style={{ padding: '8px 12px', fontSize: '0.85rem' }}
            />
          </div>
          <button className="btn" onClick={handleBuscar} disabled={loading} style={{ margin: 0, padding: '8px 16px', fontSize: '0.85rem', width: 'auto' }}>
            {loading ? <div className="spinner"></div> : 'Buscar'}
          </button>
          <button className="btn btn-secondary" onClick={limpiarFiltros} disabled={loading} style={{ margin: 0, padding: '8px 16px', fontSize: '0.85rem', width: 'auto' }}>
            Limpiar
          </button>
        </div>
      </div>

      {error && <div className="error-msg">{error}</div>}

      <div className="card" style={{ padding: '24px', overflowX: 'auto' }}>
        {loading ? (
          <div className="spinner-container">
            <div className="spinner" style={{ borderColor: 'rgba(30,63,32,0.1)', borderTopColor: 'hsl(var(--primary))' }}></div>
          </div>
        ) : eventos.length === 0 ? (
          <div className="results-empty">
            <span className="results-empty-icon">📋</span>
            <h3>Sin eventos registrados</h3>
            <p>No se encontraron eventos de auditoría con los filtros aplicados.</p>
          </div>
        ) : (
          <>
            <div style={{ fontSize: '0.8rem', color: 'hsl(var(--text-muted))', marginBottom: '12px', textAlign: 'right' }}>
              {eventos.length} evento{eventos.length !== 1 ? 's' : ''} encontrado{eventos.length !== 1 ? 's' : ''}
            </div>
            <table className="food-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid hsl(var(--card-border))', textAlign: 'left' }}>
                  <th style={{ padding: '10px 8px', fontSize: '0.78rem' }}>Fecha/Hora</th>
                  <th style={{ padding: '10px 8px', fontSize: '0.78rem' }}>Actor</th>
                  <th style={{ padding: '10px 8px', fontSize: '0.78rem' }}>Tipo de Evento</th>
                  <th style={{ padding: '10px 8px', fontSize: '0.78rem' }}>Entidad</th>
                  <th style={{ padding: '10px 8px', fontSize: '0.78rem' }}>ID Entidad</th>
                  <th style={{ padding: '10px 8px', fontSize: '0.78rem', textAlign: 'center' }}>Resultado</th>
                  <th style={{ padding: '10px 8px', fontSize: '0.78rem' }}>Detalle</th>
                </tr>
              </thead>
              <tbody>
                {eventos.map((ev, idx) => {
                  const badgeStyle = getBadgeStyle(ev.event_type, ev.success);
                  const ts = ev.timestamp ? new Date(ev.timestamp + (ev.timestamp.includes('Z') ? '' : 'Z')).toLocaleString('es-EC') : '—';
                  return (
                    <tr key={ev.event_id || idx} style={{ borderBottom: '1px solid rgba(0,0,0,0.03)' }}>
                      <td style={{ padding: '10px 8px', fontSize: '0.78rem', whiteSpace: 'nowrap', color: 'hsl(var(--text-muted))' }}>
                        {ts}
                      </td>
                      <td style={{ padding: '10px 8px', fontSize: '0.82rem', fontWeight: 600 }}>
                        {ev.usuario || ev.username || ev.actor || '—'}
                      </td>
                      <td style={{ padding: '10px 8px' }}>
                        <span style={{
                          fontSize: '0.72rem',
                          fontWeight: 600,
                          padding: '2px 8px',
                          borderRadius: '8px',
                          whiteSpace: 'nowrap',
                          ...badgeStyle
                        }}>
                          {ev.event_type}
                        </span>
                      </td>
                      <td style={{ padding: '10px 8px', fontSize: '0.82rem' }}>
                        {ev.entity || ev.entidad || '—'}
                      </td>
                      <td style={{ padding: '10px 8px', fontSize: '0.78rem', fontFamily: 'monospace', color: 'hsl(var(--text-muted))' }}>
                        {ev.entity_id || ev.entidad_id || '—'}
                      </td>
                      <td style={{ padding: '10px 8px', textAlign: 'center' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: '2px 10px',
                          borderRadius: '12px',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          background: ev.success === false || ev.success === 'false' ? '#fef2f2' : ev.success === true || ev.success === 'true' ? '#ecfdf5' : 'rgba(0,0,0,0.03)',
                          color: ev.success === false || ev.success === 'false' ? '#dc2626' : ev.success === true || ev.success === 'true' ? '#047857' : 'hsl(var(--text-muted))',
                        }}>
                          {ev.success === false || ev.success === 'false' ? 'FALLIDO' :
                           ev.success === true || ev.success === 'true' ? 'EXITOSO' :
                           ev.result || '—'}
                        </span>
                      </td>
                      <td style={{ padding: '10px 8px', fontSize: '0.78rem', color: 'hsl(var(--text-secondary))', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {ev.detail || ev.detalle || ev.reason || '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </>
        )}
      </div>
    </div>
  );
}
