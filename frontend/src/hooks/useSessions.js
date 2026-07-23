import { useState, useEffect, useCallback } from 'react';
import { fetchSessions, fetchCurrentSession } from '../services/stream';

export function useSessions(token, deviceId) {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadSessions = useCallback(async () => {
    if (!token || !deviceId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSessions(token, deviceId);
      setSessions(data.sessions || []);
    } catch (err) {
      setError(err.message || 'Error al cargar sesiones');
    } finally {
      setLoading(false);
    }
  }, [token, deviceId]);

  const loadCurrentSession = useCallback(async () => {
    if (!token || !deviceId) return;
    try {
      const data = await fetchCurrentSession(token, deviceId);
      setCurrentSession(data.session || null);
    } catch (err) {
      console.warn('[Sessions] Error loading current session:', err);
    }
  }, [token, deviceId]);

  useEffect(() => {
    loadSessions();
    loadCurrentSession();
  }, [loadSessions, loadCurrentSession]);

  return { sessions, currentSession, loading, error, refresh: loadSessions, refreshCurrent: loadCurrentSession };
}
