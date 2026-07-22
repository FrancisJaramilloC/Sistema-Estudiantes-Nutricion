import React, { useState } from 'react';
import { apiService } from '../services/api';

const FACTORES_ACTIVIDAD = [
  { value: 1.2, label: 'Sedentario', detail: 'Sin ejercicio' },
  { value: 1.375, label: 'Ligero', detail: 'Ejercicio suave 1-3 veces/sem' },
  { value: 1.55, label: 'Moderado', detail: 'Ejercicio 3-5 veces/sem' },
  { value: 1.725, label: 'Intenso', detail: 'Ejercicio fuerte 6-7 veces/sem' },
  { value: 1.9, label: 'Muy Intenso', detail: 'Atletas, trabajo físico' },
];

export default function SugerenciaPlan({ token }) {
  const [formData, setFormData] = useState({
    peso_kg: 70,
    estatura_m: 1.75,
    edad: 25,
    sexo: 'Masculino',
    factor_actividad: 1.55,
    imc_clasificacion: 'Normal',
    icc_riesgo: 'Bajo',
    antecedentes: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sugerencia, setSugerencia] = useState(null);
  const [confirmarAceptacion, setConfirmarAceptacion] = useState(false);
  const [aceptando, setAceptando] = useState(false);
  const [aceptado, setAceptado] = useState(false);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setSugerencia(null);
    setAceptado(false);
    setConfirmarAceptacion(false);
  };

  const handleGenerar = async () => {
    setLoading(true);
    setError('');
    setSugerencia(null);
    setAceptado(false);
    setConfirmarAceptacion(false);
    try {
      const datos = {
        peso_kg: parseFloat(formData.peso_kg) || 0,
        estatura_m: parseFloat(formData.estatura_m) || 0,
        edad: parseInt(formData.edad) || 0,
        sexo: formData.sexo,
        factor_actividad: parseFloat(formData.factor_actividad),
        imc_clasificacion: formData.imc_clasificacion,
        icc_riesgo: formData.icc_riesgo,
        antecedentes: formData.antecedentes.split(',').map((a) => a.trim()).filter(Boolean),
      };
      const data = await apiService.generarSugerencia(token, datos);
      setSugerencia(data);
    } catch (err) {
      setError(err.message || 'Error al generar la sugerencia.');
    } finally {
      setLoading(false);
    }
  };

  const handleAceptar = async () => {
    if (!confirmarAceptacion) {
      setConfirmarAceptacion(true);
      return;
    }
    setAceptando(true);
    setError('');
    try {
      await apiService.aceptarSugerencia(token, sugerencia.sugerencia_id);
      setAceptado(true);
      setConfirmarAceptacion(false);
    } catch (err) {
      setError(err.message || 'Error al aceptar la sugerencia.');
    } finally {
      setAceptando(false);
    }
  };

  const handleEditar = () => {
    console.log('Abrir editor con sugerencia:', sugerencia);
  };

  const handleDescartar = () => {
    setSugerencia(null);
    setAceptado(false);
    setConfirmarAceptacion(false);
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
    <div className="dashboard-content">
      <div className="content-header">
        <h1>Sugerencia de Plan Nutricional</h1>
        <p>Genera automáticamente una sugerencia de plan basada en los datos antropométricos del paciente y sus antecedentes.</p>
      </div>

      <div className="antropometria-grid">
        <div className="card anthrop-card">
          <h2>Datos del Paciente</h2>

          {error && <div className="error-msg">{error}</div>}
          {aceptado && <div className="success-msg">Sugerencia aceptada y plan creado exitosamente.</div>}

          <div className="inline-fields">
            <div className="form-group">
              <label>Peso (kg)</label>
              <input type="number" step="0.1" min="30" max="250"
                value={formData.peso_kg}
                onChange={(e) => handleChange('peso_kg', e.target.value)} />
            </div>
            <div className="form-group">
              <label>Estatura (m)</label>
              <input type="number" step="0.01" min="1.20" max="2.50"
                value={formData.estatura_m}
                onChange={(e) => handleChange('estatura_m', e.target.value)} />
            </div>
          </div>

          <div className="inline-fields">
            <div className="form-group">
              <label>Edad (años)</label>
              <input type="number" min="1" max="120"
                value={formData.edad}
                onChange={(e) => handleChange('edad', e.target.value)} />
            </div>
            <div className="form-group">
              <label>Sexo</label>
              <select value={formData.sexo}
                onChange={(e) => handleChange('sexo', e.target.value)}>
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

          <div className="inline-fields">
            <div className="form-group">
              <label>Clasificación IMC</label>
              <select value={formData.imc_clasificacion}
                onChange={(e) => handleChange('imc_clasificacion', e.target.value)}>
                <option value="Bajo peso">Bajo peso</option>
                <option value="Normal">Normal</option>
                <option value="Sobrepeso">Sobrepeso</option>
                <option value="Obesidad">Obesidad</option>
              </select>
            </div>
            <div className="form-group">
              <label>Riesgo ICC</label>
              <select value={formData.icc_riesgo}
                onChange={(e) => handleChange('icc_riesgo', e.target.value)}>
                <option value="Bajo">Bajo</option>
                <option value="Moderado">Moderado</option>
                <option value="Alto">Alto</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Antecedentes (separados por coma)</label>
            <input type="text"
              value={formData.antecedentes}
              onChange={(e) => handleChange('antecedentes', e.target.value)}
              placeholder="ej. diabetes tipo 2, hipertensión" />
          </div>

          <button className="btn" onClick={handleGenerar} disabled={loading}>
            {loading ? <div className="spinner"></div> : 'Generar Sugerencia'}
          </button>
        </div>

        <div className="card anthrop-results">
          <h2>Resultado de la Sugerencia</h2>

          {!sugerencia && !loading && (
            <div className="results-empty">
              <span className="results-empty-icon">💡</span>
              <h3>Genera una sugerencia</h3>
              <p>Completa los datos del paciente y presiona "Generar Sugerencia" para obtener una propuesta nutricional automática.</p>
            </div>
          )}

          {loading && (
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
                  onClick={handleAceptar}
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
                  onClick={handleEditar}
                  style={{ flex: '1 1 120px', margin: 0 }}
                >
                  Editar
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={handleDescartar}
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
