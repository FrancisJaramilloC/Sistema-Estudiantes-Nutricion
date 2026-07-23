import React from 'react';

const CLASS_COLORS = {
  normal: { bg: '#22c55e', label: 'Normal' },
  atencion: { bg: '#eab308', label: 'Atención' },
  critico: { bg: '#ef4444', label: 'Crítico' },
};

function formatDuration(seconds) {
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s > 0 ? `${m}m ${s}s` : `${m}m`;
}

function formatTime(isoString) {
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString('es-EC', { hour: '2-digit', minute: '2-digit' });
  } catch {
    return isoString;
  }
}

function formatDate(isoString) {
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString('es-EC', { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

export default function SessionCard({ session, selected, onClick }) {
  const cls = CLASS_COLORS[session.classification] || CLASS_COLORS.normal;
  const isToday = (() => {
    try {
      const d = new Date(session.start_time);
      const now = new Date();
      return d.toDateString() === now.toDateString();
    } catch { return false; }
  })();

  return (
    <div
      className={`session-card ${selected ? 'session-selected' : ''}`}
      style={{ borderLeftColor: cls.bg }}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
    >
      <div className="session-card-header">
        <span className="session-card-day">
          {isToday ? 'Hoy' : formatDate(session.start_time)}
        </span>
        <span className="session-card-time">
          {formatTime(session.start_time)}
        </span>
        <span className="session-card-class" style={{ background: cls.bg }}>
          {cls.label}
        </span>
      </div>
      <div className="session-card-metrics">
        <span className="session-metric">
          <strong>{session.avg_bpm}</strong> avg
        </span>
        <span className="session-metric">
          <strong>{session.min_bpm}</strong>–<strong>{session.max_bpm}</strong> rango
        </span>
        <span className="session-metric">
          <strong>{formatDuration(session.duration_seconds)}</strong>
        </span>
        <span className="session-metric">
          <strong>{session.reading_count}</strong> lecturas
        </span>
      </div>
    </div>
  );
}
