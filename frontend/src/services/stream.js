const getBaseUrl = () => {
  const hostname = window.location.hostname;
  return `http://${hostname}:8000`;
};

export function createReadingStream(token, deviceId, callbacks) {
  const url = `${getBaseUrl()}/api/v1/devices/readings/stream?device_id=${encodeURIComponent(deviceId)}`;
  const abortController = new AbortController();
  let reconnectTimeout = null;
  let retryDelay = 1000;
  const maxRetryDelay = 30000;

  function connect() {
    if (abortController.signal.aborted) return;

    console.log('[SSE] Conectando a', url);
    callbacks.onStatus?.('Conectando...');

    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
      signal: abortController.signal,
    }).then(async (response) => {
      if (!response.ok) {
        const text = await response.text().catch(() => '');
        throw new Error(`SSE HTTP ${response.status}: ${text.slice(0, 200)}`);
      }

      if (!response.body) {
        throw new Error('SSE: response.body es null (el navegador no soporta streaming)');
      }

      console.log('[SSE] Conectado');
      callbacks.onStatus?.('Conectado');
      retryDelay = 1000;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = '';
      let currentEvent = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log('[SSE] Stream cerrado por el servidor');
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            if (currentEvent === 'reading') {
              try {
                const data = JSON.parse(dataStr);
                callbacks.onReading?.(data);
              } catch (e) {
                console.warn('[SSE] Error parseando reading:', dataStr, e);
              }
            }
            currentEvent = null;
          }
        }
      }

      callbacks.onDisconnect?.();
      scheduleReconnect();
    }).catch((err) => {
      if (err.name === 'AbortError') return;
      console.error('[SSE] Error de conexión:', err.message);
      callbacks.onError?.(err.message);
      callbacks.onStatus?.('Error: ' + err.message);
      scheduleReconnect();
    });
  }

  function scheduleReconnect() {
    if (abortController.signal.aborted) return;
    console.log('[SSE] Reconectando en', retryDelay, 'ms');
    callbacks.onStatus?.('Reconectando en ' + (retryDelay / 1000) + 's...');
    reconnectTimeout = setTimeout(() => {
      retryDelay = Math.min(retryDelay * 2, maxRetryDelay);
      connect();
    }, retryDelay);
  }

  connect();

  return () => {
    console.log('[SSE] Limpiando');
    abortController.abort();
    if (reconnectTimeout) clearTimeout(reconnectTimeout);
  };
}

export function fetchSessions(token, deviceId, limit = 200) {
  const url = `${getBaseUrl()}/api/v1/devices/${encodeURIComponent(deviceId)}/sessions?limit=${limit}`;
  return fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  }).then((r) => r.json());
}

export function fetchCurrentSession(token, deviceId) {
  const url = `${getBaseUrl()}/api/v1/devices/${encodeURIComponent(deviceId)}/sessions/current`;
  return fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  }).then((r) => r.json());
}
