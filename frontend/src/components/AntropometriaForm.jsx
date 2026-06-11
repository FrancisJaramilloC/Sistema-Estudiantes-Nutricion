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
    const startTime = performance.now();

    try {
      const data = await apiService.calculateClinical(token, {
        peso_kg: peso,
        estatura_m: estatura,
        perimetro_cintura_cm: cintura,
        perimetro_cadera_cm: cadera,
        sexo_biologico: sexoBiologico
      });

      const endTime = performance.now();
      const renderingTime = endTime - startTime;
      console.log(`Cálculo y renderizado completado en: ${renderingTime.toFixed(2)} ms`);

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
      default: return 'hsl(var(--text-primary))';
    }
  };

  const getIccColor = (risk) => {
    switch (risk) {
      case 'Bajo': return '#16a34a';
      case 'Moderado': return '#fbbf24';
      case 'Alto': return '#dc2626';
      default: return 'hsl(var(--text-primary))';
    }
  };

  return (
    <div style={{ marginBottom: '30px' }}>
      <h2 style={{ fontSize: '1.2rem', textAlign: 'left', marginBottom: '16px', color: 'hsl(var(--text-primary))' }}>
        Motor de Cálculo Antropométrico
      </h2>
      
      {error && <div className="error-msg">{error}</div>}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="pesoKg">Peso (kg)</label>
            <input 
              type="number" 
              step="0.01"
              id="pesoKg"
              value={pesoKg}
              onChange={(e) => setPesoKg(e.target.value)}
              placeholder="ej. 70.00"
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
              placeholder="ej. 100.00"
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
              placeholder="ej. 90.00"
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

        <button type="submit" className="btn" disabled={loading}>
          {loading ? <div className="spinner"></div> : 'Calcular Indicadores síncronamente'}
        </button>
      </form>

      {/* Resultados con Animación de Transición y Estilo Premium */}
      {results && (
        <div style={{ 
          marginTop: '24px',
          background: 'rgba(30, 63, 32, 0.03)', 
          border: '1px solid rgba(30, 63, 32, 0.15)', 
          borderRadius: '16px', 
          padding: '20px',
          animation: 'fadeIn 0.3s ease-out'
        }}>
          <h3 style={{ 
            fontSize: '1rem', 
            fontWeight: 600, 
            color: 'hsl(var(--primary))', 
            marginBottom: '14px',
            borderBottom: '1px solid rgba(30, 63, 32, 0.08)',
            paddingBottom: '6px'
          }}>
            Resultados del Diagnóstico Antropométrico
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            
            {/* IMC Result */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <p style={{ fontSize: '0.8rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', margin: 0 }}>
                  Índice de Masa Corporal (IMC)
                </p>
                <p style={{ fontSize: '1.4rem', fontWeight: 700, margin: '2px 0 0 0' }}>{results.imc}</p>
              </div>
              <span style={{ 
                fontSize: '0.85rem', 
                fontWeight: 600, 
                padding: '4px 12px', 
                borderRadius: '20px',
                background: getImcColor(results.imc_clasificacion) + '15',
                color: getImcColor(results.imc_clasificacion),
                border: `1px solid ${getImcColor(results.imc_clasificacion)}30`
              }}>
                {results.imc_clasificacion}
              </span>
            </div>

            {/* ICC Result */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
              <div>
                <p style={{ fontSize: '0.8rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', margin: 0 }}>
                  Índice Cintura-Cadera (ICC)
                </p>
                <p style={{ fontSize: '1.4rem', fontWeight: 700, margin: '2px 0 0 0' }}>{results.icc}</p>
              </div>
              <span style={{ 
                fontSize: '0.85rem', 
                fontWeight: 600, 
                padding: '4px 12px', 
                borderRadius: '20px',
                background: getIccColor(results.icc_riesgo) + '15',
                color: getIccColor(results.icc_riesgo),
                border: `1px solid ${getIccColor(results.icc_riesgo)}30`
              }}>
                Riesgo {results.icc_riesgo}
              </span>
            </div>

            {/* Fat Distribution */}
            <div style={{ 
              marginTop: '8px', 
              paddingTop: '10px', 
              borderTop: '1px solid rgba(30, 63, 32, 0.08)',
              fontSize: '0.85rem' 
            }}>
              <span style={{ color: 'hsl(var(--text-secondary))' }}>Distribución de Grasa: </span>
              <strong style={{ color: 'hsl(var(--text-primary))' }}>{results.distribucion_grasa}</strong>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
