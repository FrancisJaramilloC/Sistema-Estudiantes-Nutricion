import React, { useState, useEffect } from 'react';

const FEATURES = [
  { key: 'high-contrast', label: 'Alto Contraste', icon: '◐' },
  { key: 'grayscale', label: 'Escala de Grises', icon: '◑' },
  { key: 'invert-colors', label: 'Invertir Colores', icon: '◓' },
];

export default function AccessibilityButton() {
  const [open, setOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(() =>
    document.documentElement.classList.contains('a11y-dark'),
  );
  const [activeFeatures, setActiveFeatures] = useState(() => {
    const saved = {};
    for (const f of FEATURES) {
      saved[f.key] = document.documentElement.classList.contains(`a11y-${f.key}`);
    }
    return saved;
  });

  useEffect(() => {
    for (const f of FEATURES) {
      const cls = `a11y-${f.key}`;
      if (activeFeatures[f.key]) {
        document.documentElement.classList.add(cls);
      } else {
        document.documentElement.classList.remove(cls);
      }
    }
  }, [activeFeatures]);

  useEffect(() => {
    document.documentElement.classList.toggle('a11y-dark', darkMode);
  }, [darkMode]);

  const toggle = (key) => {
    setActiveFeatures((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="a11y-container">
      <button
        className="a11y-trigger"
        onClick={() => setOpen(!open)}
        aria-label="Opciones de accesibilidad"
        title="Accesibilidad"
      >
        ♿
      </button>
      {open && (
        <div className="a11y-panel">
          <div className="a11y-panel-header">Accesibilidad</div>
          <div className="a11y-divider" />
          <label className="a11y-option">
            <span className="a11y-option-icon">{darkMode ? '☀️' : '🌙'}</span>
            <span className="a11y-option-label">Modo Oscuro</span>
            <input
              type="checkbox"
              checked={darkMode}
              onChange={() => setDarkMode((prev) => !prev)}
            />
            <span className="a11y-toggle-track">
              <span className="a11y-toggle-thumb" />
            </span>
          </label>
          <div className="a11y-divider" />
          {FEATURES.map((f) => (
            <label key={f.key} className="a11y-option">
              <span className="a11y-option-icon">{f.icon}</span>
              <span className="a11y-option-label">{f.label}</span>
              <input
                type="checkbox"
                checked={activeFeatures[f.key]}
                onChange={() => toggle(f.key)}
              />
              <span className="a11y-toggle-track">
                <span className="a11y-toggle-thumb" />
              </span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
