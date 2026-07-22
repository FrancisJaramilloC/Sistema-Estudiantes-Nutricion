import React, { useState } from 'react';
import useAntropometria from '../hooks/useAntropometria';
import { apiService } from '../services/api';

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

  const [antecedentes, setAntecedentes] = useState('');
  const [sugerenciaLoading, setSugerenciaLoading] = useState(false);
  const [sugerenciaError, setSugerenciaError] = useState('');
  const [sugerencia, setSugerencia] = useState(null);
  const [confirmarAceptacion, setConfirmarAceptacion] = useState(false);
  const [aceptando, setAceptando] = useState(false);
  const [aceptado, setAceptado] = useState(false);

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

  const handleGenerarSugerencia = async () => {
    if (!resultados.tmb_harris) {
      setSugerenciaError('Primero completa los datos antropométricos para calcular TMB.');
      return;
    }
    setSugerenciaLoading(true);
    setSugerenciaError('');
    setSugerencia(null);
    setAceptado(false);
    setConfirmarAceptacion(false);
    try {
      const datos = {
        peso_kg: parseFloat(formData.peso_kg) || 0,
        estatura_m: parseFloat(formData.estatura_m) || 0,
        edad: parseInt(formData.edad) || 0,
        sexo_biologico: formData.sexo_biologico,
        factor_actividad: parseFloat(formData.factor_actividad),
        imc_clasificacion: resultados.imc_clasificacion || 'Normal',
        icc_riesgo: resultados.icc_riesgo || 'Bajo',
        antecedentes: antecedentes.split(',').map((a) => a.trim()).filter(Boolean),
      };
      const data = await apiService.generarSugerencia(token, datos);
      setSugerencia(data);
    } catch (err) {
      setSugerenciaError(err.message || 'Error al generar la sugerencia.');
    } finally {
      setSugerenciaLoading(false);
    }
  };

  const handleAceptarSugerencia = async () => {
    if (!confirmarAceptacion) {
      setConfirmarAceptacion(true);
      return;
    }
    setAceptando(true);
    setSugerenciaError('');
    try {
      await apiService.aceptarSugerencia(token, sugerencia.sugerencia_id);
      setAceptado(true);
      setConfirmarAceptacion(false);
    } catch (err) {
      setSugerenciaError(err.message || 'Error al aceptar la sugerencia.');
    } finally {
      setAceptando(false);
    }
  };

  const renderBarra = (label, value, max, unit, color) => {
    const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
    return (
      <div style={{ marginBottom: '10px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '3px' }}>
          <span style={{ color: 'hsl(var(--text-secondary))' }}>{label}</span>
          <span style={{ fontWeight: 600, color: 'hsl(var(--text-primary))' }}>{Math.round(value)} {unit}</span>
        </div>
        <div className="tmb-bar" style={{ height: '10px' }}>
          <div style={{ height: '100%', borderRadius: '4px', background: color, width: `${pct}%`, transition: 'width 0.5s ease-out' }} />
        </div>
      </div>
    );
  };

  return (
    <div className="antropometria-dashboard">
      <div className="antropometria-header">
        <h1>Evaluación Antropométrica, Metabólica y Sugerencia</h1>
        <p>Calcula IMC, ICC, TMB y GET en tiempo real, y genera automáticamente una sugerencia de plan nutricional.</p>
      </div>

      <div className="antropometria-grid">
        <div className="card anthrop-card">
          <h2>Datos de Entrada</h2>

          <div className="slider-group">
            <label>Peso (kg)</label>
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
            <label>Estatura (m)</label>
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
            <label>Cintura (cm)</label>
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
            <label>Cadera (cm)</label>
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
            {loading ? <div className="spinner"></div> : 'Guardar'}
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

      <div className="antropometria-grid" style={{ marginTop: '24px' }}>
        <div className="card anthrop-card">
          <h2>Sugerencia de Plan Nutricional</h2>
          <p style={{ fontSize: '0.82rem', color: 'hsl(var(--text-muted))', marginBottom: '16px' }}>
            Genera automáticamente una sugerencia de plan basada en los cálculos antropométricos y antecedentes del paciente.
          </p>

          {sugerenciaError && <div className="error-msg">{sugerenciaError}</div>}
          {aceptado && <div className="success-msg">Sugerencia aceptada y plan creado exitosamente.</div>}

          <div className="inline-fields">
            <div className="form-group" style={{ flex: 1 }}>
              <label>IMC Clasificación</label>
              <input type="text" value={resultados.imc_clasificacion || '—'} disabled
                style={{ background: 'rgba(30,63,32,0.03)' }} />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label>Riesgo ICC</label>
              <input type="text" value={resultados.icc_riesgo || '—'} disabled
                style={{ background: 'rgba(30,63,32,0.03)' }} />
            </div>
          </div>

          <div className="form-group">
            <label>Antecedentes (separados por coma)</label>
            <input type="text"
              value={antecedentes}
              onChange={(e) => setAntecedentes(e.target.value)}
              placeholder="ej. diabetes tipo 2, hipertensión" />
          </div>

          <button className="btn" onClick={handleGenerarSugerencia} disabled={sugerenciaLoading || !resultados.tmb_harris}>
            {sugerenciaLoading ? <div className="spinner"></div> : 'Generar Sugerencia de Plan'}
          </button>
        </div>

        <div className="card anthrop-results">
          <h2>Resultado de la Sugerencia</h2>

          {!sugerencia && !sugerenciaLoading && (
            <div className="results-empty">
              <span className="results-empty-icon">💡</span>
              <h3>Genera una sugerencia</h3>
              <p>Completa los datos antropométricos y presiona "Generar Sugerencia de Plan" para obtener una propuesta automática.</p>
            </div>
          )}

          {sugerenciaLoading && (
            <div className="spinner-container">
              <div className="spinner" style={{ borderColor: 'rgba(30,63,32,0.1)', borderTopColor: 'hsl(var(--primary))' }}></div>
            </div>
          )}

          {sugerencia && (
            <div className="results-content">
              {(sugerencia.tmb_harris || sugerencia.tmb_calculada) && (
                <div className="result-section">
                  <h3>Metabolismo Basal (TMB)</h3>
                  <div className="tmb-card" style={{ marginBottom: '12px' }}>
                    <div className="tmb-title">Fórmula de Harris-Benedict</div>
                    <div className="tmb-row">
                      <span>TMB Calculada</span>
                      <strong>{sugerencia.tmb_harris || sugerencia.tmb_calculada} kcal</strong>
                    </div>
                    <div className="tmb-bar">
                      <div className="tmb-bar-fill tmb-bar-blue" style={{ width: `${Math.min(((sugerencia.tmb_harris || sugerencia.tmb_calculada) / 3500) * 100, 100)}%` }} />
                    </div>
                    <div className="tmb-row">
                      <span>GET Diario</span>
                      <strong className="tmb-get">{sugerencia.objetivo_kcal || sugerencia.get_diario || sugerencia.gasto_energetico_total || '—'} kcal</strong>
                    </div>
                    <div className="tmb-bar">
                      <div className="tmb-bar-fill tmb-bar-green" style={{ width: `${Math.min(((sugerencia.objetivo_kcal || sugerencia.get_diario || sugerencia.gasto_energetico_total || 0) / 4000) * 100, 100)}%` }} />
                    </div>
                  </div>
                </div>
              )}

              {(sugerencia.distribucion_macros || sugerencia.distribucion_macronutrientes) && (
                <div className="result-section">
                  <h3>Distribución de Macronutrientes</h3>
                  {renderBarra('Proteínas',
                    sugerencia.distribucion_macros?.gramos_proteina_recomendados
                    || sugerencia.distribucion_macronutrientes?.proteina_g
                    || sugerencia.distribucion_macronutrientes?.proteina || 0, 300, 'g', '#3b82f6')}
                  {renderBarra('Grasas',
                    sugerencia.distribucion_macros?.gramos_grasa_recomendados
                    || sugerencia.distribucion_macronutrientes?.grasa_g
                    || sugerencia.distribucion_macronutrientes?.grasa || 0, 150, 'g', '#f59e0b')}
                  {renderBarra('Carbohidratos',
                    sugerencia.distribucion_macros?.gramos_carbohidratos_recomendados
                    || sugerencia.distribucion_macronutrientes?.carbohidratos_g
                    || sugerencia.distribucion_macronutrientes?.carbohidratos || 0, 500, 'g', '#16a34a')}
                </div>
              )}

              {sugerencia.alimentos_sugeridos && sugerencia.alimentos_sugeridos.length > 0 && (
                <div className="result-section">
                  <h3>Alimentos Sugeridos</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {sugerencia.alimentos_sugeridos.map((al, idx) => (
                      <div key={idx} style={{
                        background: 'rgba(30,63,32,0.02)',
                        border: '1px solid rgba(30,63,32,0.06)',
                        borderRadius: '8px',
                        padding: '8px 12px',
                        fontSize: '0.82rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <span style={{ fontWeight: 600 }}>{al.nombre || al}</span>
                        {al.porcion && <span style={{ fontSize: '0.72rem', color: 'hsl(var(--text-muted))' }}>{al.porcion}</span>}
                        {al.comida && <span className={`food-meal-badge meal-${al.comida.toLowerCase()}`}>{al.comida}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(sugerencia.formula_utilizada || sugerencia.descripcion_formula) && (
                <div className="result-section">
                  <h3>Fórmula Utilizada (Auditable)</h3>
                  <div className="tmb-info" style={{ fontSize: '0.8rem', whiteSpace: 'pre-wrap' }}>
                    {sugerencia.descripcion_formula || sugerencia.formula_utilizada}
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', gap: '10px', marginTop: '16px', flexWrap: 'wrap' }}>
                <button
                  className="btn"
                  onClick={handleAceptarSugerencia}
                  disabled={aceptando || aceptado}
                  style={{
                    flex: '1 1 120px',
                    margin: 0,
                    backgroundColor: aceptado ? '#16a34a' : confirmarAceptacion ? '#dc2626' : undefined,
                  }}
                >
                  {aceptando ? <div className="spinner"></div> :
                    aceptado ? 'Plan Creado' :
                    confirmarAceptacion ? 'Confirmar Aceptación' : 'Aceptar'}
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => { setSugerencia(null); setAceptado(false); setConfirmarAceptacion(false); }}
                  disabled={aceptando}
                  style={{ flex: '1 1 120px', margin: 0, borderColor: 'rgba(220,38,38,0.3)', color: '#dc2626' }}
                >
                  Descartar
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
