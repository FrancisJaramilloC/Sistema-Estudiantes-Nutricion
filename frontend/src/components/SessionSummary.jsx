import React from 'react';

function formatDuration(seconds) {
  if (!seconds) return '—';
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s > 0 ? `${m}m ${s}s` : `${m}m`;
}

export default function SessionSummary({ session }) {
  if (!session) return null;

  const zones = session.zone_distribution_pct || {};
  const hasReadings = session.reading_count > 0;

  return (
    <div className="session-summary">
      <div className="summary-grid">
        <div className="summary-stat">
          <span className="summary-label">Promedio</span>
          <span className="summary-value">{session.avg_bpm}</span>
          <span className="summary-unit">BPM</span>
        </div>
        <div className="summary-stat">
          <span className="summary-label">Mínimo</span>
          <span className="summary-value">{session.min_bpm}</span>
          <span className="summary-unit">BPM</span>
        </div>
        <div className="summary-stat">
          <span className="summary-label">Máximo</span>
          <span className="summary-value">{session.max_bpm}</span>
          <span className="summary-unit">BPM</span>
        </div>
        <div className="summary-stat">
          <span className="summary-label">Variabilidad</span>
          <span className="summary-value">{session.std_dev_bpm}</span>
          <span className="summary-unit">SD</span>
        </div>
      </div>

      {hasReadings && (
        <div className="zone-bar-container">
          <div className="zone-bar">
            <div
              className="zone-segment zone-bajo"
              style={{ width: `${Math.max(zones.bajo || 0, 1)}%` }}
              title={`Bajo: ${zones.bajo}%`}
            />
            <div
              className="zone-segment zone-normal"
              style={{ width: `${Math.max(zones.normal || 0, 1)}%` }}
              title={`Normal: ${zones.normal}%`}
            />
            <div
              className="zone-segment zone-elevado"
              style={{ width: `${Math.max(zones.elevado || 0, 1)}%` }}
              title={`Elevado: ${zones.elevado}%`}
            />
          </div>
          <div className="zone-labels">
            <span>&lt;60 Bajo {zones.bajo}%</span>
            <span>60-100 Normal {zones.normal}%</span>
            <span>&gt;100 Elevado {zones.elevado}%</span>
          </div>
        </div>
      )}

      <div className="summary-footer">
        <span>Duración: {formatDuration(session.duration_seconds)}</span>
        <span>Lecturas: {session.reading_count}</span>
      </div>
    </div>
  );
}
