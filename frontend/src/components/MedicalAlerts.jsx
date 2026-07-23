import React from 'react';

const CLASSIFICATION_CONFIG = {
  normal: { label: 'Normal', icon: '🟢', className: 'alert-normal' },
  atencion: { label: 'Requiere Atención', icon: '🟡', className: 'alert-warning' },
  critico: { label: 'Crítico', icon: '🔴', className: 'alert-critical' },
};

export default function MedicalAlerts({ session }) {
  if (!session) return null;

  const arrhythmias = session.arrhythmia_events || [];
  const brady = session.bradycardia_episodes || [];
  const tachy = session.tachycardia_episodes || [];
  const cls = CLASSIFICATION_CONFIG[session.classification] || CLASSIFICATION_CONFIG.normal;

  return (
    <div className="medical-alerts">
      <h3 className="alerts-title">Alertas Médicas</h3>

      <div className={`classification-banner ${cls.className}`}>
        <span className="classification-icon">{cls.icon}</span>
        <span className="classification-label">Clasificación: {cls.label}</span>
      </div>

      {brady.length === 0 && tachy.length === 0 && arrhythmias.length === 0 && (
        <p className="alerts-empty">Sin eventos significativos en esta sesión.</p>
      )}

      {brady.length > 0 && (
        <div className="alert-group">
          <h4 className="alert-group-title">Episodios de Bradicardia (&lt;60 BPM)</h4>
          {brady.map((ep, i) => (
            <div key={`brady-${i}`} className="alert-item alert-brady">
              <span className="alert-icon">⬇️</span>
              <div className="alert-body">
                <span className="alert-detail">
                  {ep.duration_readings} lecturas consecutivas, promedio {ep.avg_bpm} BPM
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tachy.length > 0 && (
        <div className="alert-group">
          <h4 className="alert-group-title">Episodios de Taquicardia (&gt;100 BPM)</h4>
          {tachy.map((ep, i) => (
            <div key={`tachy-${i}`} className="alert-item alert-tachy">
              <span className="alert-icon">⬆️</span>
              <div className="alert-body">
                <span className="alert-detail">
                  {ep.duration_readings} lecturas consecutivas, promedio {ep.avg_bpm} BPM
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {arrhythmias.length > 0 && (
        <div className="alert-group">
          <h4 className="alert-group-title">Eventos Arrítmicos</h4>
          {arrhythmias.slice(0, 5).map((ev, i) => (
            <div key={`arrh-${i}`} className="alert-item alert-arrhythmia">
              <span className="alert-icon">⚡</span>
              <div className="alert-body">
                <span className="alert-detail">
                  Cambio abrupto: {ev.from_bpm} → {ev.to_bpm} BPM (Δ{ev.delta})
                </span>
              </div>
            </div>
          ))}
          {arrhythmias.length > 5 && (
            <p className="alert-more">...y {arrhythmias.length - 5} eventos más</p>
          )}
        </div>
      )}
    </div>
  );
}
