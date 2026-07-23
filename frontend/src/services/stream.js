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

    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
      signal: abortController.signal,
    }).then(async (response) => {
      if (!response.ok) {
        throw new Error(`SSE error: ${response.status}`);
      }

      retryDelay = 1000;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = null;
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (currentEvent === 'reading') {
              try {
                const data = JSON.parse(dataStr);
                callbacks.onReading?.(data);
              } catch (e) {
                console.warn('[SSE] Error parsing reading:', e);
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
      callbacks.onError?.(err.message);
      scheduleReconnect();
    });
  }

  function scheduleReconnect() {
    if (abortController.signal.aborted) return;
    reconnectTimeout = setTimeout(() => {
      retryDelay = Math.min(retryDelay * 2, maxRetryDelay);
      connect();
    }, retryDelay);
  }

  connect();

  return () => {
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
