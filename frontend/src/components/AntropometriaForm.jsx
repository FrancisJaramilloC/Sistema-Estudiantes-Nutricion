import React, { useState } from 'react';
import { apiService } from '../services/api';

export default function AntropometriaForm({ token }) {
  // Form fields
  const [pesoKg, setPesoKg] = useState('');
  const [estaturaM, setEstaturaM] = useState('');
  const [cinturaCm, setCinturaCm] = useState('');
  const [caderaCm, setCaderaCm] = useState('');
  const [sexoBiologico, setSexoBiologico] = useState('Masculino');
  const [edad, setEdad] = useState('');
  const [factorActividad, setFactorActividad] = useState('1.2');
  const [eta, setEta] = useState('10'); // Efecto Termogénico (default 10%)

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
    const edadAnios = parseInt(edad, 10);
    const factAct = parseFloat(factorActividad);
    const etaVal = parseFloat(eta);

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
    if (isNaN(edadAnios) || edadAnios <= 0 || edadAnios > 120) {
      setError('Por favor, ingresa una edad válida en años (1 - 120).');
      return;
    }
    if (isNaN(etaVal) || etaVal < 1 || etaVal > 10) {
      setError('El efecto termogénico de los alimentos debe estar entre 1% y 10%.');
      return;
    }

    setLoading(true);
    try {
      const data = await apiService.calculateClinical(token, {
        peso_kg: peso,
        estatura_m: estatura,
        perimetro_cintura_cm: cintura,
        perimetro_cadera_cm: cadera,
        sexo_biologico: sexoBiologico,
        edad: edadAnios,
        factor_actividad: factAct,
        efecto_termogenico: etaVal
      });
      setResults(data);
    } catch (err) {
      setError(err.message || 'Error al procesar el cálculo antropométrico y metabólico.');
    } finally {
      setLoading(false);
    }
  };

  const getImcColor = (classification) => {
    switch (classification) {
      case 'Normal': return 'var(--success, #16a34a)';
      case 'Bajo peso': return '#fbbf24';
      case 'Sobrepeso': return '#ea580c';
      case 'Obesidad': return '#dc2626';
      default: return '#78716c';
    }
  };

  const getIccColor = (risk) => {
    switch (risk) {
      case 'Bajo': return 'var(--success, #16a34a)';
      case 'Moderado': return '#fbbf24';
      case 'Alto': return '#dc2626';
      default: return '#78716c';
    }
  };

  // Helper to map values for percentage bars (cap at 100)
  const getPercentage = (value, max) => {
    const pct = (value / max) * 100;
    return Math.max(0, Math.min(100, pct));
  };

  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', textAlign: 'left', margin: 0 }}>Evaluación Antropométrica y Metabólica</h1>
        <p style={{ color: 'hsl(var(--text-secondary))', fontSize: '0.95rem' }}>
          Calcula y compara los índices de masa corporal (IMC), riesgo cardiovascular (ICC), Tasa Metabólica Basal (TMB) y necesidades energéticas totales (GET).
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(320px, 1fr) minmax(360px, 1.3fr)',
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

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label htmlFor="edad">Edad (años)</label>
                <input 
                  type="number" 
                  id="edad"
                  value={edad}
                  onChange={(e) => setEdad(e.target.value)}
                  placeholder="ej. 25"
                  disabled={loading}
                  required
                />
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
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor="factorActividad">Factor de Actividad Física</label>
              <select 
                id="factorActividad"
                value={factorActividad}
                onChange={(e) => setFactorActividad(e.target.value)}
                disabled={loading}
                required
              >
                <option value="1.2">1.2 - Sedentario (Trabajo de oficina, sin ejercicio)</option>
                <option value="1.375">1.375 - Actividad Ligera (Ejercicio suave 1-3 veces/sem)</option>
                <option value="1.55">1.55 - Actividad Moderada (Ejercicio 3-5 veces/sem)</option>
                <option value="1.725">1.725 - Actividad Intensa (Ejercicio fuerte 6-7 veces/sem)</option>
                <option value="1.9">1.9 - Actividad Muy Intensa (Atletas, trabajo físico exigente)</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label htmlFor="eta">Efecto Termogénico de los Alimentos (ETA)</label>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'hsl(var(--primary))' }}>{eta}%</span>
              </div>
              <input 
                type="range" 
                min="1" 
                max="10" 
                step="1"
                id="eta"
                value={eta}
                onChange={(e) => setEta(e.target.value)}
                disabled={loading}
                style={{ width: '100%', accentColor: 'hsl(var(--primary))' }}
                required
              />
              <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))' }}>Rango recomendado de la OMS: 1% a 10% del gasto activo.</span>
            </div>

            <button type="submit" className="btn" disabled={loading} style={{ marginTop: '8px' }}>
              {loading ? <div className="spinner"></div> : 'Calcular Indicadores'}
            </button>
          </form>
        </div>

        {/* Right Column: Visual Charts & Analytics */}
        <div className="card" style={{ padding: '24px', margin: 0, width: '100%', borderRadius: '20px', minHeight: '380px', display: 'flex', flexDirection: 'column', justifyContent: results ? 'flex-start' : 'center' }}>
          {!results ? (
            <div style={{ textAlign: 'center', color: 'hsl(var(--text-secondary))', padding: '40px 20px' }}>
              <div style={{ fontSize: '3.5rem', marginBottom: '16px' }}>📊</div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'hsl(var(--primary))', marginBottom: '8px' }}>
                Esperando Datos de Entrada
              </h3>
              <p style={{ fontSize: '0.9rem', maxWidth: '340px', margin: '0 auto', color: 'hsl(var(--text-muted))', lineHeight: '1.4' }}>
                Completa y envía el formulario de evaluación a la izquierda para generar los gráficos comparativos de niveles metabólicos e índices corporales.
              </p>
            </div>
          ) : (
            <div style={{ animation: 'fadeIn 0.3s ease-out', display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <h2 style={{ fontSize: '1.2rem', textAlign: 'left', marginBottom: 0, borderBottom: '1px solid rgba(30, 63, 32, 0.08)', paddingBottom: '8px' }}>
                Gráfico Comparativo de Niveles
              </h2>

              {/* 1. IMC COMPARATIVE BARS */}
              <div>
                <h3 style={{ fontSize: '0.9rem', fontWeight: 600, margin: '0 0 10px 0', color: 'hsl(var(--text-primary))' }}>
                  Índice de Masa Corporal (IMC)
                </h3>
                
                {/* User Bar */}
                <div style={{ marginBottom: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'hsl(var(--text-secondary))', marginBottom: '3px' }}>
                    <span>Tu IMC ({results.imc_clasificacion})</span>
                    <span style={{ fontWeight: 700, color: getImcColor(results.imc_clasificacion) }}>{results.imc}</span>
                  </div>
                  <div style={{ background: 'rgba(0,0,0,0.05)', borderRadius: '6px', height: '16px', overflow: 'hidden' }}>
                    <div style={{ 
                      background: getImcColor(results.imc_clasificacion), 
                      height: '100%', 
                      width: `${getPercentage(results.imc, 40)}%`, 
                      transition: 'width 0.8s ease-out' 
                    }} />
                  </div>
                </div>

                {/* Reference Bar */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'hsl(var(--text-secondary))', marginBottom: '3px' }}>
                    <span>Ideal Recomendado (OMS)</span>
                    <span style={{ fontWeight: 600, color: 'var(--success, #16a34a)' }}>18.5 - 24.9</span>
                  </div>
                  <div style={{ background: 'rgba(0,0,0,0.05)', borderRadius: '6px', height: '16px', overflow: 'hidden' }}>
                    <div style={{ 
                      background: 'var(--success, #16a34a)', 
                      height: '100%', 
                      width: `${getPercentage(21.7, 40)}%` 
                    }} />
                  </div>
                </div>
              </div>

              {/* 2. ICC COMPARATIVE BARS */}
              <div>
                <h3 style={{ fontSize: '0.9rem', fontWeight: 600, margin: '0 0 10px 0', color: 'hsl(var(--text-primary))' }}>
                  Índice Cintura-Cadera (ICC) y Riesgo
                </h3>
                
                {/* User Bar */}
                <div style={{ marginBottom: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'hsl(var(--text-secondary))', marginBottom: '3px' }}>
                    <span>Tu ICC (Riesgo {results.icc_riesgo})</span>
                    <span style={{ fontWeight: 700, color: getIccColor(results.icc_riesgo) }}>{results.icc}</span>
                  </div>
                  <div style={{ background: 'rgba(0,0,0,0.05)', borderRadius: '6px', height: '16px', overflow: 'hidden' }}>
                    <div style={{ 
                      background: getIccColor(results.icc_riesgo), 
                      height: '100%', 
                      width: `${getPercentage(results.icc, 1.2)}%`, 
                      transition: 'width 0.8s ease-out' 
                    }} />
                  </div>
                </div>

                {/* Reference Bar */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'hsl(var(--text-secondary))', marginBottom: '3px' }}>
                    <span>Límite Saludable Recomendado</span>
                    <span style={{ fontWeight: 600, color: 'var(--success, #16a34a)' }}>{sexoBiologico === 'Masculino' ? '≤ 0.90' : '≤ 0.80'}</span>
                  </div>
                  <div style={{ background: 'rgba(0,0,0,0.05)', borderRadius: '6px', height: '16px', overflow: 'hidden' }}>
                    <div style={{ 
                      background: 'var(--success, #16a34a)', 
                      height: '100%', 
                      width: `${getPercentage(sexoBiologico === 'Masculino' ? 0.90 : 0.80, 1.2)}%` 
                    }} />
                  </div>
                </div>
              </div>

              {/* 3. TMB & GET COMPARISON CHART */}
              <div>
                <h3 style={{ fontSize: '0.9rem', fontWeight: 600, margin: '0 0 10px 0', color: 'hsl(var(--text-primary))' }}>
                  Necesidades Energéticas Diarias (kcal)
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  
                  {/* Mifflin-St Jeor Column */}
                  <div style={{ background: 'rgba(30, 63, 32, 0.02)', padding: '12px', borderRadius: '12px', border: '1px solid rgba(30, 63, 32, 0.06)' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'hsl(var(--primary))', marginBottom: '8px', textAlign: 'center' }}>
                      Fórmula Mifflin-St Jeor
                    </div>
                    
                    {/* TMB */}
                    <div style={{ marginBottom: '6px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'hsl(var(--text-secondary))', marginBottom: '2px' }}>
                        <span>TMB (Basal):</span>
                        <span style={{ fontWeight: 600 }}>{results.tmb_mifflin} kcal</span>
                      </div>
                      <div style={{ background: 'rgba(0,0,0,0.05)', borderRadius: '4px', height: '10px', overflow: 'hidden' }}>
                        <div style={{ background: '#3b82f6', height: '100%', width: `${getPercentage(results.tmb_mifflin, 3500)}%` }} />
                      </div>
                    </div>

                    {/* GET */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'hsl(var(--text-secondary))', marginBottom: '2px' }}>
                        <span>GET (Total):</span>
                        <span style={{ fontWeight: 700, color: 'hsl(var(--primary))' }}>{results.gasto_total_mifflin} kcal</span>
                      </div>
                      <div style={{ background: 'rgba(0,0,0,0.05)', borderRadius: '4px', height: '10px', overflow: 'hidden' }}>
                        <div style={{ background: 'var(--success, #16a34a)', height: '100%', width: `${getPercentage(results.gasto_total_mifflin, 3500)}%` }} />
                      </div>
                    </div>
                  </div>

                  {/* Harris-Benedict Column */}
                  <div style={{ background: 'rgba(30, 63, 32, 0.02)', padding: '12px', borderRadius: '12px', border: '1px solid rgba(30, 63, 32, 0.06)' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'hsl(var(--primary))', marginBottom: '8px', textAlign: 'center' }}>
                      Fórmula Harris-Benedict
                    </div>
                    
                    {/* TMB */}
                    <div style={{ marginBottom: '6px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'hsl(var(--text-secondary))', marginBottom: '2px' }}>
                        <span>TMB (Basal):</span>
                        <span style={{ fontWeight: 600 }}>{results.tmb_harris} kcal</span>
                      </div>
                      <div style={{ background: 'rgba(0,0,0,0.05)', borderRadius: '4px', height: '10px', overflow: 'hidden' }}>
                        <div style={{ background: '#3b82f6', height: '100%', width: `${getPercentage(results.tmb_harris, 3500)}%` }} />
                      </div>
                    </div>

                    {/* GET */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'hsl(var(--text-secondary))', marginBottom: '2px' }}>
                        <span>GET (Total):</span>
                        <span style={{ fontWeight: 700, color: 'hsl(var(--primary))' }}>{results.gasto_total_harris} kcal</span>
                      </div>
                      <div style={{ background: 'rgba(0,0,0,0.05)', borderRadius: '4px', height: '10px', overflow: 'hidden' }}>
                        <div style={{ background: 'var(--success, #16a34a)', height: '100%', width: `${getPercentage(results.gasto_total_harris, 3500)}%` }} />
                      </div>
                    </div>
                  </div>

                </div>
              </div>

              {/* Info Banner */}
              <div style={{ 
                background: 'rgba(30, 63, 32, 0.02)', 
                border: '1px solid rgba(30, 63, 32, 0.06)', 
                borderRadius: '12px', 
                padding: '12px',
                fontSize: '0.82rem',
                color: 'hsl(var(--text-secondary))',
                lineHeight: '1.4'
              }}>
                ℹ️ <strong>Tasa Metabólica Basal (TMB):</strong> Las calorías mínimas que tu cuerpo requiere para sobrevivir en reposo. 
                <br />
                <strong>Gasto Energético Total (GET):</strong> Es el requerimiento diario incluyendo tu factor de actividad física ({factorActividad}) más el efecto termogénico de alimentos ({eta}%).
              </div>

            </div>
          )}
        </div>

      </div>
    </div>
  );
}
