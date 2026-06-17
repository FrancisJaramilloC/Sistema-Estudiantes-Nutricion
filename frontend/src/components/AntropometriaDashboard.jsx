import React, { useState } from 'react';
import useAntropometria from '../hooks/useAntropometria';
import { apiService } from '../services/api';

const tooltips = {
  peso_kg: 'Masa corporal total medida en kilogramos. Fundamental para el cálculo del IMC y TMB.',
  estatura_m: 'Altura medida en metros. Junto al peso, determina el Índice de Masa Corporal (IMC).',
  perimetro_cintura_cm: 'Circunferencia abdominal a la altura del ombligo. Indicador clave de riesgo cardiovascular según la OMS.',
  perimetro_cadera_cm: 'Circunferencia máxima de caderas. Se usa con la cintura para calcular el Índice Cintura-Cadera (ICC).',
};

const FACTORES_ACTIVIDAD = [
  { value: 1.2, label: 'Sedentario', detail: 'Sin ejercicio' },
  { value: 1.375, label: 'Ligero', detail: 'Ejercicio suave 1-3 veces/sem' },
  { value: 1.55, label: 'Moderado', detail: 'Ejercicio 3-5 veces/sem' },
  { value: 1.725, label: 'Intenso', detail: 'Ejercicio fuerte 6-7 veces/sem' },
  { value: 1.9, label: 'Muy Intenso', detail: 'Atletas, trabajo físico' },
];

export default function AntropometriaDashboard({ token }) {
  const [formData, setFormData] = useState({
    peso_kg: 70,
    estatura_m: 1.75,
    perimetro_cintura_cm: 85,
    perimetro_cadera_cm: 95,
    sexo_biologico: 'Masculino',
    edad: 25,
    factor_actividad: 1.55,
    efecto_termogenico: 10,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [persisted, setPersisted] = useState(false);

  const resultados = useAntropometria(formData);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setPersisted(false);
  };

  const handlePersist = async () => {
    setLoading(true);
    setError('');
    try {
      await apiService.calculateClinical(token, {
        peso_kg: formData.peso_kg,
        estatura_m: formData.estatura_m,
        perimetro_cintura_cm: formData.perimetro_cintura_cm,
        perimetro_cadera_cm: formData.perimetro_cadera_cm,
        sexo_biologico: formData.sexo_biologico,
        edad: formData.edad,
        factor_actividad: formData.factor_actividad,
        efecto_termogenico: formData.efecto_termogenico,
      });
      setPersisted(true);
    } catch (err) {
      setError(err.message || 'Error al persistir en base de datos.');
    } finally {
      setLoading(false);
    }
  };

  const getIMCPosition = () => {
    if (!resultados.imc) return 0;
    return Math.min((resultados.imc / 40) * 100, 100);
  };

  const getIMCBarColor = () => {
    if (!resultados.imc) return '#78716c';
    if (resultados.imc < 18.5) return '#fbbf24';
    if (resultados.imc < 25) return '#16a34a';
    if (resultados.imc < 30) return '#ea580c';
    return '#dc2626';
  };

  return (
    <div className="antropometria-dashboard">
      <div className="antropometria-header">
        <h1>Evaluación Antropométrica y Metabólica</h1>
        <p>Calcula IMC, ICC, TMB y GET en tiempo real. Ajusta los sliders para ver resultados instantáneos.</p>
      </div>

      <div className="antropometria-grid">
        <div className="card anthrop-card">
          <h2>Datos de Entrada</h2>

          <div className="slider-group">
            <label>
              Peso (kg)
              <span className="tooltip-trigger" title={tooltips.peso_kg}>?</span>
            </label>
            <div className="slider-row">
              <input
                type="range" min="30" max="250" step="0.1"
                value={formData.peso_kg}
                onChange={(e) => handleChange('peso_kg', parseFloat(e.target.value))}
              />
              <input
                type="number" step="0.1" min="30" max="250"
                value={formData.peso_kg}
                onChange={(e) => handleChange('peso_kg', parseFloat(e.target.value) || 0)}
                className="slider-value-input"
              />
            </div>
          </div>

          <div className="slider-group">
            <label>
              Estatura (m)
              <span className="tooltip-trigger" title={tooltips.estatura_m}>?</span>
            </label>
            <div className="slider-row">
              <input
                type="range" min="1.20" max="2.50" step="0.01"
                value={formData.estatura_m}
                onChange={(e) => handleChange('estatura_m', parseFloat(e.target.value))}
              />
              <input
                type="number" step="0.01" min="1.20" max="2.50"
                value={formData.estatura_m}
                onChange={(e) => handleChange('estatura_m', parseFloat(e.target.value) || 0)}
                className="slider-value-input"
              />
            </div>
          </div>

          <div className="slider-group">
            <label>
              Cintura (cm)
              <span className="tooltip-trigger" title={tooltips.perimetro_cintura_cm}>?</span>
            </label>
            <div className="slider-row">
              <input
                type="range" min="50" max="200" step="0.1"
                value={formData.perimetro_cintura_cm}
                onChange={(e) => handleChange('perimetro_cintura_cm', parseFloat(e.target.value))}
              />
              <input
                type="number" step="0.1" min="50" max="200"
                value={formData.perimetro_cintura_cm}
                onChange={(e) => handleChange('perimetro_cintura_cm', parseFloat(e.target.value) || 0)}
                className="slider-value-input"
              />
            </div>
          </div>

          <div className="slider-group">
            <label>
              Cadera (cm)
              <span className="tooltip-trigger" title={tooltips.perimetro_cadera_cm}>?</span>
            </label>
            <div className="slider-row">
              <input
                type="range" min="50" max="200" step="0.1"
                value={formData.perimetro_cadera_cm}
                onChange={(e) => handleChange('perimetro_cadera_cm', parseFloat(e.target.value))}
              />
              <input
                type="number" step="0.1" min="50" max="200"
                value={formData.perimetro_cadera_cm}
                onChange={(e) => handleChange('perimetro_cadera_cm', parseFloat(e.target.value) || 0)}
                className="slider-value-input"
              />
            </div>
          </div>

          <div className="inline-fields">
            <div className="form-group">
              <label>Edad (años)</label>
              <input type="number" min="1" max="120"
                value={formData.edad}
                onChange={(e) => handleChange('edad', parseInt(e.target.value) || 0)} />
            </div>
            <div className="form-group">
              <label>Sexo</label>
              <select value={formData.sexo_biologico}
                onChange={(e) => handleChange('sexo_biologico', e.target.value)}>
                <option value="Masculino">Masculino</option>
                <option value="Femenino">Femenino</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Factor de Actividad Física</label>
            <select value={formData.factor_actividad}
              onChange={(e) => handleChange('factor_actividad', parseFloat(e.target.value))}>
              {FACTORES_ACTIVIDAD.map((f) => (
                <option key={f.value} value={f.value}>{f.label} ({f.detail})</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <div className="eta-header">
              <label>Efecto Termogénico (ETA)</label>
              <span className="eta-value">{formData.efecto_termogenico}%</span>
            </div>
            <input type="range" min="1" max="10" step="1"
              value={formData.efecto_termogenico}
              onChange={(e) => handleChange('efecto_termogenico', parseInt(e.target.value))} />
          </div>

          {error && <div className="error-msg">{error}</div>}
          {persisted && <div className="success-msg">Resultados guardados en base de datos.</div>}

          <button className="btn" onClick={handlePersist} disabled={loading}>
            {loading ? <div className="spinner"></div> : 'Guardar en Base de Datos'}
          </button>
        </div>

        <div className="card anthrop-results">
          <h2>Resultados Analíticos</h2>

          {resultados.imc !== null ? (
            <div className="results-content">
              <div className="result-section">
                <h3>Índice de Masa Corporal (IMC)</h3>
                <div className="speedometer">
                  <div className="speedometer-bar">
                    <div className="speedometer-track">
                      <div className="speedometer-fill" style={{ width: `${getIMCPosition()}%`, background: getIMCBarColor() }} />
                    </div>
                    <div className="speedometer-labels">
                      <span style={{ color: '#fbbf24' }}>Bajo Peso</span>
                      <span style={{ color: '#16a34a' }}>Normal</span>
                      <span style={{ color: '#ea580c' }}>Sobrepeso</span>
                      <span style={{ color: '#dc2626' }}>Obesidad</span>
                    </div>
                    <div className="speedometer-value" style={{ color: getIMCBarColor() }}>
                      {resultados.imc} — <strong>{resultados.imc_clasificacion}</strong>
                    </div>
                  </div>
                </div>
              </div>

              <div className={`result-section icc-card ${resultados.icc_riesgo === 'Alto' ? 'icc-alert' : ''}`}>
                <h3>Índice Cintura-Cadera (ICC)</h3>
                <div className="icc-value" style={{ color: resultados.icc_color }}>
                  {resultados.icc}
                </div>
                <div className="icc-risk" style={{ background: resultados.icc_color }}>
                  Riesgo Cardiovascular: {resultados.icc_riesgo}
                </div>
                {resultados.icc_riesgo === 'Alto' && (
                  <div className="icc-warning-banner">
                    ⚠️ Riesgo cardiovascular alto. Se recomienda evaluación médica especializada.
                  </div>
                )}
              </div>

              <div className="result-section silhouette-section">
                <h3>Distribución de Grasa Corporal</h3>
                <div className="silhouette-container">
                  <span className="silhouette-icon">
                    {resultados.distribucion_grasa?.includes('Manzana') ? '🍎' : '🍐'}
                  </span>
                  <span className="silhouette-label">{resultados.distribucion_grasa}</span>
                </div>
              </div>

              <div className="result-section">
                <h3>Necesidades Energéticas Diarias (kcal)</h3>
                <div className="tmb-grid">
                  <div className="tmb-card">
                    <div className="tmb-title">Mifflin-St Jeor</div>
                    <div className="tmb-row">
                      <span>TMB Basal</span>
                      <strong>{resultados.tmb_mifflin} kcal</strong>
                    </div>
                    <div className="tmb-bar">
                      <div className="tmb-bar-fill tmb-bar-blue" style={{ width: `${Math.min((resultados.tmb_mifflin / 3500) * 100, 100)}%` }} />
                    </div>
                    <div className="tmb-row">
                      <span>GET Total</span>
                      <strong className="tmb-get">{resultados.gasto_total_mifflin} kcal</strong>
                    </div>
                    <div className="tmb-bar">
                      <div className="tmb-bar-fill tmb-bar-green" style={{ width: `${Math.min((resultados.gasto_total_mifflin / 3500) * 100, 100)}%` }} />
                    </div>
                  </div>
                  <div className="tmb-card">
                    <div className="tmb-title">Harris-Benedict</div>
                    <div className="tmb-row">
                      <span>TMB Basal</span>
                      <strong>{resultados.tmb_harris} kcal</strong>
                    </div>
                    <div className="tmb-bar">
                      <div className="tmb-bar-fill tmb-bar-blue" style={{ width: `${Math.min((resultados.tmb_harris / 3500) * 100, 100)}%` }} />
                    </div>
                    <div className="tmb-row">
                      <span>GET Total</span>
                      <strong className="tmb-get">{resultados.gasto_total_harris} kcal</strong>
                    </div>
                    <div className="tmb-bar">
                      <div className="tmb-bar-fill tmb-bar-green" style={{ width: `${Math.min((resultados.gasto_total_harris / 3500) * 100, 100)}%` }} />
                    </div>
                  </div>
                </div>
                <div className="tmb-info">
                  ℹ️ <strong>TMB:</strong> Calorías mínimas en reposo. <strong>GET:</strong> Requerimiento diario total (factor actividad {formData.factor_actividad} + ETA {formData.efecto_termogenico}%).
                </div>
              </div>
            </div>
          ) : (
            <div className="results-empty">
              <span className="results-empty-icon">📊</span>
              <h3>Ajusta los sliders para ver resultados</h3>
              <p>Los cálculos se actualizan instantáneamente al modificar cualquier valor.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
