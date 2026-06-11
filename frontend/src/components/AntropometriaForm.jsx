import React, { useState } from 'react';
import { apiService } from '../services/api';

export default function AntropometriaForm({ token }) {
  // Form fields
  const [pesoKg, setPesoKg] = useState('');
  const [estaturaM, setEstaturaM] = useState('');
  const [cinturaCm, setCinturaCm] = useState('');
  const [caderaCm, setCaderaCm] = useState('');
  const [sexoBiologico, setSexoBiologico] = useState('Masculino');

  // Control states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResults(null);

    // Frontend validations
    const peso = parseFloat(pesoKg);
    const estatura = parseFloat(estaturaM);
    const cintura = parseFloat(cinturaCm);
    const cadera = parseFloat(caderaCm);

    if (isNaN(peso) || peso <= 0 || peso > 500) {
      setError('Por favor, ingresa un peso válido en kg (ej. 70.5).');
      return;
    }
    if (isNaN(estatura) || estatura <= 0.4 || estatura > 2.8) {
      setError('Por favor, ingresa una estatura válida en metros (ej. 1.75).');
      return;
    }
    if (isNaN(cintura) || cintura <= 20 || cintura > 250) {
      setError('Por favor, ingresa un perímetro de cintura válido en cm.');
      return;
    }
    if (isNaN(cadera) || cadera <= 20 || cadera > 250) {
      setError('Por favor, ingresa un perímetro de cadera válido en cm.');
      return;
    }

    setLoading(true);
    try {
      const data = await apiService.calculateClinical(token, {
        peso_kg: peso,
        estatura_m: estatura,
        perimetro_cintura_cm: cintura,
        perimetro_cadera_cm: cadera,
        sexo_biologico: sexoBiologico
      });
      setResults(data);
    } catch (err) {
      setError(err.message || 'Error al procesar el cálculo antropométrico.');
    } finally {
      setLoading(false);
    }
  };

  const getImcColor = (classification) => {
    switch (classification) {
      case 'Normal': return '#16a34a';
      case 'Bajo peso': return '#fbbf24';
      case 'Sobrepeso': return '#ea580c';
      case 'Obesidad': return '#dc2626';
      default: return '#78716c';
    }
  };

  const getIccColor = (risk) => {
    switch (risk) {
      case 'Bajo': return '#16a34a';
      case 'Moderado': return '#fbbf24';
      case 'Alto': return '#dc2626';
      default: return '#78716c';
    }
  };

  // Helper to map BMI (15 - 40 range) to % for the SVG gauge
  const getBmiPercentage = (bmi) => {
    const val = parseFloat(bmi);
    if (isNaN(val)) return 0;
    const min = 15;
    const max = 40;
    const pct = ((val - min) / (max - min)) * 100;
    return Math.max(0, Math.min(100, pct));
  };

  // Helper to map ICC (0.6 - 1.2 range) to % for the SVG gauge
  const getIccPercentage = (icc) => {
    const val = parseFloat(icc);
    if (isNaN(val)) return 0;
    const min = 0.6;
    const max = 1.2;
    const pct = ((val - min) / (max - min)) * 100;
    return Math.max(0, Math.min(100, pct));
  };

  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', textAlign: 'left', margin: 0 }}>Evaluación Antropométrica</h1>
        <p style={{ color: 'hsl(var(--text-secondary))', fontSize: '0.95rem' }}>
          Calcula y compara los índices clínicos clave de masa corporal y riesgo cardiovascular con rangos epidemiológicos recomendados.
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(320px, 1fr) minmax(360px, 1.2fr)',
        gap: '24px',
        width: '100%',
        alignItems: 'start'
      }} className="antropometria-layout">
        
        {/* Left Column: Input Form */}
        <div className="card" style={{ padding: '24px', margin: 0, width: '100%', borderRadius: '20px' }}>
          <h2 style={{ fontSize: '1.2rem', textAlign: 'left', marginBottom: '16px', borderBottom: '1px solid rgba(30, 63, 32, 0.08)', paddingBottom: '8px' }}>
            Formulario de Entrada
          </h2>

          {error && <div className="error-msg" style={{ marginBottom: '16px' }}>{error}</div>}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label htmlFor="pesoKg">Peso (kg)</label>
                <input 
                  type="number" 
                  step="0.01"
                  id="pesoKg"
                  value={pesoKg}
                  onChange={(e) => setPesoKg(e.target.value)}
                  placeholder="ej. 70.0"
                  disabled={loading}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label htmlFor="estaturaM">Estatura (m)</label>
                <input 
                  type="number" 
                  step="0.01"
                  id="estaturaM"
                  value={estaturaM}
                  onChange={(e) => setEstaturaM(e.target.value)}
                  placeholder="ej. 1.75"
                  disabled={loading}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label htmlFor="cinturaCm">Cintura (cm)</label>
                <input 
                  type="number" 
                  step="0.01"
                  id="cinturaCm"
                  value={cinturaCm}
                  onChange={(e) => setCinturaCm(e.target.value)}
                  placeholder="ej. 85.0"
                  disabled={loading}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label htmlFor="caderaCm">Cadera (cm)</label>
                <input 
                  type="number" 
                  step="0.01"
                  id="caderaCm"
                  value={caderaCm}
                  onChange={(e) => setCaderaCm(e.target.value)}
                  placeholder="ej. 95.0"
                  disabled={loading}
                  required
                />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor="sexoBiologico">Sexo Biológico</label>
              <select 
                id="sexoBiologico"
                value={sexoBiologico}
                onChange={(e) => setSexoBiologico(e.target.value)}
                disabled={loading}
                required
              >
                <option value="Masculino">Masculino</option>
                <option value="Femenino">Femenino</option>
              </select>
            </div>

            <button type="submit" className="btn" disabled={loading} style={{ marginTop: '8px' }}>
              {loading ? <div className="spinner"></div> : 'Calcular Indicadores síncronamente'}
            </button>
          </form>
        </div>

        {/* Right Column: Visual Charts & Analytics */}
        <div className="card" style={{ padding: '24px', margin: 0, width: '100%', borderRadius: '20px', minHeight: '380px', display: 'flex', flexDirection: 'column', justifyContent: results ? 'flex-start' : 'center' }}>
          {!results ? (
            <div style={{ textAlign: 'center', color: 'hsl(var(--text-secondary))', padding: '40px 20px' }}>
              <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📊</div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'hsl(var(--primary))', marginBottom: '8px' }}>
                Esperando Datos de Entrada
              </h3>
              <p style={{ fontSize: '0.88rem', maxWidth: '320px', margin: '0 auto', color: 'hsl(var(--text-muted))' }}>
                Completa y envía el formulario de evaluación a la izquierda para procesar y ver las gráficas estadísticas comparativas de nivel clínico.
              </p>
            </div>
          ) : (
            <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
              <h2 style={{ fontSize: '1.2rem', textAlign: 'left', marginBottom: '20px', borderBottom: '1px solid rgba(30, 63, 32, 0.08)', paddingBottom: '8px' }}>
                Diagnóstico y Gráficas de Referencia
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                
                {/* 1. IMC STATISTICAL CHART */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'hsl(var(--text-secondary))' }}>
                      Índice de Masa Corporal (IMC)
                    </span>
                    <span style={{ 
                      fontSize: '0.8rem', 
                      fontWeight: 700, 
                      padding: '3px 10px', 
                      borderRadius: '12px',
                      background: getImcColor(results.imc_clasificacion) + '15',
                      color: getImcColor(results.imc_clasificacion),
                      border: `1px solid ${getImcColor(results.imc_clasificacion)}25`
                    }}>
                      {results.imc} - {results.imc_clasificacion}
                    </span>
                  </div>

                  {/* Horizontal Bar Chart Gauge */}
                  <div style={{ position: 'relative', height: '40px', marginTop: '16px' }}>
                    {/* Gauge Segments */}
                    <div style={{ display: 'flex', height: '12px', borderRadius: '6px', overflow: 'hidden', width: '100%', background: '#e5e7eb' }}>
                      <div style={{ width: '25%', background: '#f59e0b', title: 'Bajo peso (<18.5)' }} />
                      <div style={{ width: '30%', background: '#10b981', title: 'Normal (18.5 - 24.9)' }} />
                      <div style={{ width: '20%', background: '#f97316', title: 'Sobrepeso (25.0 - 29.9)' }} />
                      <div style={{ width: '25%', background: '#ef4444', title: 'Obesidad (>=30.0)' }} />
                    </div>

                    {/* Scale markers */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'hsl(var(--text-muted))', marginTop: '4px', padding: '0 2px' }}>
                      <span>15 (Bajo)</span>
                      <span>18.5</span>
                      <span>25.0</span>
                      <span>30.0</span>
                      <span>40+ (Alto)</span>
                    </div>

                    {/* Pointer Indicator */}
                    <div style={{
                      position: 'absolute',
                      top: '-6px',
                      left: `${getBmiPercentage(results.imc)}%`,
                      transform: 'translateX(-50%)',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      transition: 'left 0.5s ease-out'
                    }}>
                      {/* Triangle pointer */}
                      <div style={{
                        width: 0,
                        height: 0,
                        borderLeft: '6px solid transparent',
                        borderRight: '6px solid transparent',
                        borderBottom: `6px solid ${getImcColor(results.imc_clasificacion)}`
                      }} />
                      {/* Vertical line through bar */}
                      <div style={{
                        width: '2px',
                        height: '14px',
                        background: getImcColor(results.imc_clasificacion)
                      }} />
                      {/* Indicator text bubble */}
                      <div style={{
                        marginTop: '2px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        color: '#ffffff',
                        background: getImcColor(results.imc_clasificacion),
                        padding: '1px 6px',
                        borderRadius: '4px',
                        boxShadow: '0 2px 5px rgba(0,0,0,0.15)',
                        whiteSpace: 'nowrap'
                      }}>
                        Tu IMC: {results.imc}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 2. ICC CARDIOVASCULAR RISK CHART */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'hsl(var(--text-secondary))' }}>
                      Índice Cintura-Cadera (ICC)
                    </span>
                    <span style={{ 
                      fontSize: '0.8rem', 
                      fontWeight: 700, 
                      padding: '3px 10px', 
                      borderRadius: '12px',
                      background: getIccColor(results.icc_riesgo) + '15',
                      color: getIccColor(results.icc_riesgo),
                      border: `1px solid ${getIccColor(results.icc_riesgo)}25`
                    }}>
                      {results.icc} - Riesgo {results.icc_riesgo}
                    </span>
                  </div>

                  {/* Horizontal Bar Chart Gauge */}
                  <div style={{ position: 'relative', height: '40px', marginTop: '16px' }}>
                    {/* Gauge Segments */}
                    <div style={{ display: 'flex', height: '12px', borderRadius: '6px', overflow: 'hidden', width: '100%', background: '#e5e7eb' }}>
                      <div style={{ width: '50%', background: '#10b981', title: 'Riesgo Bajo' }} />
                      <div style={{ width: '25%', background: '#f59e0b', title: 'Riesgo Moderado' }} />
                      <div style={{ width: '25%', background: '#ef4444', title: 'Riesgo Alto' }} />
                    </div>

                    {/* Scale markers */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'hsl(var(--text-muted))', marginTop: '4px', padding: '0 2px' }}>
                      <span>0.60 (Bajo)</span>
                      <span>{sexoBiologico === 'Masculino' ? '0.90' : '0.80'}</span>
                      <span>{sexoBiologico === 'Masculino' ? '0.95' : '0.85'}</span>
                      <span>1.20 (Alto)</span>
                    </div>

                    {/* Pointer Indicator */}
                    <div style={{
                      position: 'absolute',
                      top: '-6px',
                      left: `${getIccPercentage(results.icc)}%`,
                      transform: 'translateX(-50%)',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      transition: 'left 0.5s ease-out'
                    }}>
                      {/* Triangle pointer */}
                      <div style={{
                        width: 0,
                        height: 0,
                        borderLeft: '6px solid transparent',
                        borderRight: '6px solid transparent',
                        borderBottom: `6px solid ${getIccColor(results.icc_riesgo)}`
                      }} />
                      {/* Vertical line through bar */}
                      <div style={{
                        width: '2px',
                        height: '14px',
                        background: getIccColor(results.icc_riesgo)
                      }} />
                      {/* Indicator text bubble */}
                      <div style={{
                        marginTop: '2px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        color: '#ffffff',
                        background: getIccColor(results.icc_riesgo),
                        padding: '1px 6px',
                        borderRadius: '4px',
                        boxShadow: '0 2px 5px rgba(0,0,0,0.15)',
                        whiteSpace: 'nowrap'
                      }}>
                        Tu ICC: {results.icc}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 3. EVALUATION SUMMARY BOX */}
                <div style={{ 
                  background: 'rgba(30, 63, 32, 0.02)',
                  border: '1px solid rgba(30, 63, 32, 0.08)',
                  borderRadius: '12px',
                  padding: '14px',
                  fontSize: '0.85rem',
                  lineHeight: '1.45'
                }}>
                  <p style={{ margin: 0, color: 'hsl(var(--text-primary))', marginBottom: '8px' }}>
                    <strong>Análisis Clínico:</strong> Distribución de grasa de tipo <strong>{results.distribucion_grasa}</strong>.
                  </p>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', color: 'hsl(var(--text-secondary))' }}>
                    <div>
                      • <strong>Recomendación IMC:</strong> El rango saludable recomendado por la OMS está entre <strong>18.5 y 24.9</strong>. 
                      {results.imc_clasificacion === 'Normal' 
                        ? ' Te encuentras en un peso saludable.' 
                        : results.imc_clasificacion === 'Bajo peso'
                        ? ' Se aconseja una valoración calórica para alcanzar un rango idóneo.'
                        : ' Se recomienda un plan hipocalórico estructurado y actividad física dirigida.'}
                    </div>
                    <div>
                      • <strong>Recomendación Cardiovascular (ICC):</strong> Para personas de sexo biológico {sexoBiologico.toLowerCase()}, el límite superior recomendado para riesgo bajo es de <strong>{sexoBiologico === 'Masculino' ? '0.90' : '0.80'}</strong>.
                      {results.icc_riesgo === 'Bajo'
                        ? ' Tu distribución de grasa representa un riesgo cardiovascular bajo.'
                        : ' Tu distribución de grasa central indica una mayor acumulación de grasa visceral. Se aconseja realizar controles clínicos metabólicos.'}
                    </div>
                  </div>
                </div>

              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
