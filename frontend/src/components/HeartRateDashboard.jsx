import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import { useReadingStream } from '../hooks/useReadingStream';
import { useSessions } from '../hooks/useSessions';
import BpmGauge from './BpmGauge';
import LiveChart from './LiveChart';
import SessionCard from './SessionCard';
import SessionSummary from './SessionSummary';
import MedicalAlerts from './MedicalAlerts';

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

function PairingCodeGenerator({ token, role, onGenerated }) {
  const isDocente = role === 'Docentes';
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [codeData, setCodeData] = useState(null);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState('');

  useEffect(() => {
    if (!codeData) return;
    const expiresAt = new Date(codeData.expires_at).getTime();
    const tick = () => {
      const left = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
      setSecondsLeft(left);
      if (left <= 0) setCodeData(null);
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [codeData]);

  useEffect(() => {
    if (!isDocente) return;
    let active = true;
    apiService.listUsers(token)
      .then((data) => {
        if (!active) return;
        const list = Array.isArray(data) ? data : (data.users || []);
        const estudiantes = list.filter(
          (u) => (u.role === 'Estudiantes') || (u.groups || []).includes('Estudiantes')
        );
        setStudents(estudiantes);
      })
      .catch(() => setStudents([]));
    return () => { active = false; };
  }, [isDocente, token]);

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    setCodeData(null);
    try {
      const targetStudent = isDocente ? selectedStudent : undefined;
      if (isDocente && !targetStudent) {
        throw new Error('Selecciona un estudiante para generar el código.');
      }
      const data = await apiService.createPairingCode(token, targetStudent);
      setCodeData(data);
      if (onGenerated) onGenerated();
    } catch (err) {
      setError(err.message || 'Error al generar el código de emparejamiento');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (codeData?.code) {
      navigator.clipboard.writeText(codeData.code)
        .then(() => alert('Código copiado al portapapeles'))
        .catch(() => alert('No se pudo copiar. Selecciona el código manualmente.'));
    }
  };

  return (
    <div className="card pairing-card">
      <h2>Emparejar ESP32</h2>
      <p className="card-hint">
        {isDocente
          ? 'Genera un código temporal para un estudiante. El código vincula el dispositivo a la cuenta del estudiante.'
          : 'Genera un código temporal. Ingrésalo en el portal del ESP32 para vincular el dispositivo.'}
      </p>

      {isDocente && (
        <div className="form-group">
          <label>Estudiante</label>
          <select
            value={selectedStudent}
            onChange={(e) => setSelectedStudent(e.target.value)}
            disabled={loading || !!codeData}
          >
            <option value="">-- Selecciona un estudiante --</option>
            {students.map((s) => (
              <option key={s.username} value={s.username}>
                {s.nombre ? `${s.nombre} (${s.username})` : s.username}
              </option>
            ))}
          </select>
        </div>
      )}

      <button type="button" className="btn" onClick={handleGenerate} disabled={loading || !!codeData}>
        {loading ? <div className="spinner"></div> : 'Generar código'}
      </button>

      {error && <div className="error-msg">{error}</div>}

      {codeData && (
        <div className="hr-api-key-box">
          <p className="hr-api-key-label">
            Código para <strong>{codeData.student_id}</strong> (expira en {secondsLeft}s)
          </p>
          <div className="hr-api-key-value">{codeData.code}</div>
          <p className="hr-api-key-warning">Ingresa este código en el portal cautivo del ESP32.</p>
          <div className="code-actions">
            <button className="btn btn-secondary" onClick={copyToClipboard}>Copiar</button>
            <button className="btn btn-secondary" onClick={() => setCodeData(null)}>Cerrar</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function HeartRateDashboard({ token, userPayload, role }) {
  const isDocente = role === 'Docentes';
  const [devices, setDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState('');
  const [selectedSession, setSelectedSession] = useState(null);
  const [rawReadings, setRawReadings] = useState([]);
  const [showRaw, setShowRaw] = useState(false);
  const [loadingReadings, setLoadingReadings] = useState(false);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  const { liveReadings, latestReading, isLive } = useReadingStream(token, selectedDeviceId);
  const { sessions, currentSession, loading: sessionsLoading, refresh: refreshSessions } = useSessions(token, selectedDeviceId);

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const data = isDocente
          ? await apiService.listDevices(token)
          : await apiService.getMyDevices(token);
        const list = data.devices || [];
        setDevices(list);
        if (list.length > 0 && !selectedDeviceId) {
          setSelectedDeviceId(list[0].device_id);
        }
      } catch (err) {
        setError(err.message || 'Error al cargar dispositivos');
      }
    };
    fetchDevices();
  }, [token, isDocente, refreshKey]);

  const fetchRawReadings = useCallback(async () => {
    if (!selectedDeviceId) return;
    setLoadingReadings(true);
    try {
      const data = await apiService.getHeartReadings(token, selectedDeviceId);
      setRawReadings(data.readings || []);
    } catch (err) {
      setError(err.message || 'Error al obtener lecturas');
    } finally {
      setLoadingReadings(false);
    }
  }, [token, selectedDeviceId]);

  useEffect(() => {
    if (selectedDeviceId) {
      fetchRawReadings();
      setSelectedSession(null);
    }
  }, [selectedDeviceId, fetchRawReadings]);

  const handleDeviceRegistered = () => {
    setRefreshKey((k) => k + 1);
  };

  const handleSelectSession = (session) => {
    setSelectedSession(session);
  };

  const displaySession = selectedSession || currentSession;
  const currentBpm = latestReading?.bpm || displaySession?.latest_reading?.bpm || null;

  return (
    <div className="dashboard-content">
      <div className="content-header">
        <h1>Monitoreo de Ritmo Cardíaco</h1>
        <p>Visualiza lecturas en tiempo real, sesiones de monitoreo y resumen médico por paciente.</p>
      </div>

      <div className="session-layout">
        <div className="session-sidebar">
          <PairingCodeGenerator token={token} role={role} onGenerated={handleDeviceRegistered} />

          <div className="card">
            <h2>Dispositivo</h2>
            <div className="form-group">
              <select
                value={selectedDeviceId}
                onChange={(e) => setSelectedDeviceId(e.target.value)}
                style={{ width: '100%', height: '40px' }}
              >
                <option value="">-- Selecciona --</option>
                {devices.map((d) => (
                  <option key={d.device_id} value={d.device_id}>
                    {d.nombre} - {d.student_id}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="card">
            <div className="card-header-row">
              <h2>Sesiones</h2>
              <button className="btn btn-secondary btn-sm" onClick={refreshSessions} disabled={sessionsLoading}>
                {sessionsLoading ? <div className="spinner" /> : '↻'}
              </button>
            </div>
            {sessions.length === 0 && !sessionsLoading && (
              <p className="empty-state">Sin sesiones registradas.</p>
            )}
            <div className="session-list">
              {sessions.map((s, i) => (
                <SessionCard
                  key={`${s.start_time}-${i}`}
                  session={s}
                  selected={selectedSession?.start_time === s.start_time}
                  onClick={() => handleSelectSession(s)}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="session-main">
          <div className="session-top-row">
            <BpmGauge
              bpm={currentBpm}
              isLive={isLive}
              label={displaySession ? `Sesión ${displaySession.classification === 'normal' ? 'Normal' : displaySession.classification === 'atencion' ? 'En Observación' : 'Crítica'}` : 'Sin sesión activa'}
            />
            <LiveChart readings={liveReadings} />
          </div>

          {displaySession && (
            <div className="session-details">
              <div className="session-detail-card">
                <h3>Resumen de la Sesión</h3>
                <SessionSummary session={displaySession} />
              </div>
              <div className="session-detail-card">
                <MedicalAlerts session={displaySession} />
              </div>
            </div>
          )}

          {!displaySession && currentBpm && (
            <div className="session-details">
              <div className="session-detail-card">
                <h3>Esperando datos de sesión...</h3>
                <p className="empty-state">Los datos de la sesión se calcularán cuando haya suficientes lecturas.</p>
              </div>
            </div>
          )}

          <div className="card">
            <div className="card-header-row">
              <h2>Lecturas Crudas</h2>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowRaw(!showRaw)}>
                {showRaw ? 'Ocultar' : 'Mostrar'}
              </button>
            </div>
            {showRaw && (
              loadingReadings ? (
                <div className="spinner" />
              ) : rawReadings.length === 0 ? (
                <p className="empty-state">Sin lecturas registradas.</p>
              ) : (
                <div className="hr-table-wrapper">
                  <table className="hr-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Fecha/Hora</th>
                        <th>BPM</th>
                        <th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rawReadings.map((r, i) => {
                        const status = getBpmStatus(r.bpm);
                        return (
                          <tr key={r.reading_id || i}>
                            <td>{i + 1}</td>
                            <td>{formatDate(r.timestamp)}</td>
                            <td className={`bpm-value ${status.className}`}>{r.bpm}</td>
                            <td><span className={`hr-badge ${status.className}`}>{status.label}</span></td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  <p className="hr-count">{rawReadings.length} lectura(s)</p>
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
