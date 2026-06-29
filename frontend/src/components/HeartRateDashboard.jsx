import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

function getBpmStatus(bpm) {
  if (bpm < 60) return { label: 'Bajo', className: 'bpm-low' };
  if (bpm <= 100) return { label: 'Normal', className: 'bpm-normal' };
  return { label: 'Elevado', className: 'bpm-high' };
}

function formatDate(isoString) {
  try {
    const d = new Date(isoString);
    return d.toLocaleString('es-EC', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  } catch {
    return isoString;
  }
}

function RegisterDeviceForm({ token, onRegistered }) {
  const [studentId, setStudentId] = useState('');
  const [nombre, setNombre] = useState('ESP32 Cardíaco');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [apiKeyResult, setApiKeyResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!studentId.trim()) return;
    setLoading(true);
    setError('');
    setApiKeyResult(null);
    try {
      const data = await apiService.registerDevice(token, studentId.trim(), nombre.trim());
      setApiKeyResult(data);
    } catch (err) {
      setError(err.message || 'Error al registrar dispositivo');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (apiKeyResult?.api_key) {
      navigator.clipboard.writeText(apiKeyResult.api_key)
        .then(() => alert('API Key copiada al portapapeles'))
        .catch(() => alert('No se pudo copiar. Selecciona la clave manualmente.'));
    }
  };

  return (
    <div className="card">
      <h2>🔐 Registrar Nuevo Dispositivo</h2>
      <p style={{ fontSize: '0.9rem', color: 'hsl(var(--text-secondary))', marginBottom: '12px' }}>
        Genera una API Key para asociar un ESP32 a un estudiante. Guarda la clave, no se mostrará de nuevo.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="inline-fields" style={{ marginBottom: 0 }}>
          <div className="form-group">
            <label>ID del Estudiante</label>
            <input
              type="text"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="ej. estudiante_prueba"
              disabled={loading}
              required
            />
          </div>
          <div className="form-group">
            <label>Nombre del Dispositivo</label>
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="ESP32 Cardíaco"
              disabled={loading}
            />
          </div>
        </div>
        <div className="form-actions" style={{ marginTop: '12px' }}>
          <button type="submit" className="btn" disabled={loading || !studentId.trim()}>
            {loading ? <div className="spinner"></div> : 'Generar API Key'}
          </button>
        </div>
      </form>

      {error && <div className="error-msg" style={{ marginTop: '12px' }}>{error}</div>}

      {apiKeyResult && (
        <div className="hr-api-key-box">
          <p className="hr-api-key-label">
            ⚠️ API Key generada para <strong>{apiKeyResult.nombre}</strong>
          </p>
          <div className="hr-api-key-value">{apiKeyResult.api_key}</div>
          <p className="hr-api-key-warning">
            Guarda esta clave en el código del ESP32. No podrás recuperarla después.
          </p>
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <button className="btn btn-secondary" onClick={copyToClipboard} style={{ fontSize: '0.85rem', padding: '6px 14px' }}>
              📋 Copiar
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => { setApiKeyResult(null); setStudentId(''); setNombre('ESP32 Cardíaco'); onRegistered(); }}
              style={{ fontSize: '0.85rem', padding: '6px 14px' }}
            >
              ✅ Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function DeviceList({ token }) {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchDevices = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await apiService.listDevices(token);
      setDevices(data.devices || []);
    } catch (err) {
      setError(err.message || 'Error al listar dispositivos');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchDevices(); }, [fetchDevices]);

  return (
    <div className="card">
      <div className="profile-header">
        <h2>📡 Dispositivos Registrados</h2>
        <button className="btn btn-secondary" onClick={fetchDevices} disabled={loading}
          style={{ width: 'auto', padding: '4px 10px', fontSize: '0.8rem' }}>
          {loading ? <div className="spinner"></div> : '🔄 Refrescar'}
        </button>
      </div>

      {error && <div className="error-msg">{error}</div>}

      {devices.length === 0 && !loading && (
        <p className="empty-state">No hay dispositivos registrados.</p>
      )}

      {devices.length > 0 && (
        <div className="hr-table-wrapper">
          <table className="hr-table">
            <thead>
              <tr>
                <th>Dispositivo</th>
                <th>ID</th>
                <th>Estudiante</th>
                <th>Estado</th>
                <th>Registrado</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((d) => (
                <tr key={d.device_id}>
                  <td>{d.nombre}</td>
                  <td className="hr-device-id">{d.device_id?.substring(0, 8)}...</td>
                  <td>{d.student_id}</td>
                  <td>
                    <span className={`hr-badge ${d.activo ? 'bpm-normal' : 'bpm-low'}`}>
                      {d.activo ? '✅ Activo' : '❌ Inactivo'}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.85rem', color: 'hsl(var(--text-muted))' }}>
                    {d.created_at ? formatDate(d.created_at) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="hr-count">{devices.length} dispositivo(s)</p>
        </div>
      )}
    </div>
  );
}

export default function HeartRateDashboard({ token, userPayload, role }) {
  const isDocente = role === 'Docentes';
  const [studentId, setStudentId] = useState('');
  const [readings, setReadings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchReadings = useCallback(async () => {
    if (!studentId.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await apiService.getHeartReadings(token, studentId.trim());
      setReadings(data.readings || []);
      setLastRefresh(new Date().toLocaleTimeString('es-EC'));
    } catch (err) {
      setError(err.message || 'Error al obtener lecturas');
    } finally {
      setLoading(false);
    }
  }, [token, studentId]);

  useEffect(() => {
    if (!autoRefresh || !studentId.trim()) return;
    const interval = setInterval(fetchReadings, 10000);
    return () => clearInterval(interval);
  }, [autoRefresh, studentId, fetchReadings]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') fetchReadings();
  };

  const handleDeviceRegistered = () => {
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="dashboard-content">
      <div className="content-header">
        <h1>Monitoreo de Ritmo Cardíaco</h1>
        <p>Visualiza las lecturas de ritmo cardíaco enviadas por dispositivos ESP32 asociados a estudiantes.</p>
      </div>

      <div className="dashboard-grid">
        {isDocente && (
          <>
            <RegisterDeviceForm token={token} onRegistered={handleDeviceRegistered} />
            <DeviceList key={refreshKey} token={token} />
          </>
        )}

        <div className="card">
          <h2>Consultar Lecturas</h2>
          <div className="hr-search-row">
            <div className="form-group" style={{ flex: 1 }}>
              <label>ID del Estudiante</label>
              <input
                type="text"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="ej. estudiante_prueba"
              />
            </div>
            <button className="btn" onClick={fetchReadings} disabled={loading || !studentId.trim()} style={{ marginTop: '24px', height: '40px' }}>
              {loading ? <div className="spinner"></div> : 'Buscar'}
            </button>
          </div>

          <p style={{ fontSize: '0.82rem', color: 'hsl(var(--text-muted))', marginBottom: '8px' }}>
            💡 Las lecturas son enviadas automáticamente por el ESP32 cada 5 segundos.
          </p>

          <div className="hr-controls">
            <label className="hr-auto-refresh">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              Auto-actualizar cada 10s
            </label>
            {lastRefresh && (
              <span className="hr-last-refresh">Última actualización: {lastRefresh}</span>
            )}
          </div>

          {error && <div className="error-msg">{error}</div>}

          {readings.length === 0 && !loading && studentId.trim() && (
            <p className="empty-state">No hay lecturas registradas para este estudiante.</p>
          )}

          {!studentId.trim() && (
            <p className="empty-state">Ingresa el ID de un estudiante para consultar sus lecturas.</p>
          )}

          {readings.length > 0 && (
            <div className="hr-table-wrapper">
              <table className="hr-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Fecha/Hora</th>
                    <th>BPM</th>
                    <th>Estado</th>
                    <th>Dispositivo</th>
                  </tr>
                </thead>
                <tbody>
                  {readings.map((r, i) => {
                    const status = getBpmStatus(r.bpm);
                    return (
                      <tr key={r.reading_id || i}>
                        <td>{i + 1}</td>
                        <td>{formatDate(r.timestamp)}</td>
                        <td className={`bpm-value ${status.className}`}>{r.bpm}</td>
                        <td><span className={`hr-badge ${status.className}`}>{status.label}</span></td>
                        <td className="hr-device-id">{r.device_id?.substring(0, 8) || '-'}...</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <p className="hr-count">Mostrando {readings.length} lectura(s)</p>
            </div>
          )}
        </div>
      </div>

      <details className="dev-tools">
        <summary>🛠️ Información del Dispositivo</summary>
        <div className="hr-device-info">
          <p><strong>Endpoint:</strong> POST /api/v1/devices/reading</p>
          <p><strong>Autenticación:</strong> Header X-Api-Key</p>
          <p><strong>Formato:</strong> {'{"bpm": 72, "timestamp": "2026-06-28T10:30:00Z"}'}</p>
          <p><strong>Rango BPM:</strong> 30 - 220</p>
        </div>
      </details>
    </div>
  );
}
