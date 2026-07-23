import { useState, useEffect, useRef, useCallback } from 'react';
import { createReadingStream } from '../services/stream';

const MAX_LIVE_READINGS = 120;

export function useReadingStream(token, deviceId) {
  const [liveReadings, setLiveReadings] = useState([]);
  const [isLive, setIsLive] = useState(false);
  const [error, setError] = useState(null);
  const cleanupRef = useRef(null);

  const addReading = useCallback((reading) => {
    setLiveReadings((prev) => {
      const next = [...prev, reading];
      if (next.length > MAX_LIVE_READINGS) {
        return next.slice(next.length - MAX_LIVE_READINGS);
      }
      return next;
    });
  }, []);

  useEffect(() => {
    if (!token || !deviceId) return;

    setIsLive(false);
    setError(null);
    setLiveReadings([]);

    const cleanup = createReadingStream(token, deviceId, {
      onReading: (data) => {
        addReading(data);
        setIsLive(true);
      },
      onError: (msg) => {
        setError(msg);
        setIsLive(false);
      },
      onDisconnect: () => {
        setIsLive(false);
      },
    });

    cleanupRef.current = cleanup;
    return () => cleanup();
  }, [token, deviceId, addReading]);

  const latestReading = liveReadings.length > 0 ? liveReadings[liveReadings.length - 1] : null;

  return { liveReadings, latestReading, isLive, error };
}
