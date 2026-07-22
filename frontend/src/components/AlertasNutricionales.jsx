import React, { useMemo } from 'react';

const RANGOS_CALORICOS = {
  'Normal': { min: 1800, max: 2500 },
  'Sobrepeso': { min: 1500, max: 2000 },
  'Obesidad': { min: 1200, max: 1800 },
  'Bajo peso': { min: 2000, max: 3000 },
  'Bajo Peso': { min: 2000, max: 3000 },
};

const ALERT_STYLES = {
  danger: {
    borderColor: '#dc2626',
    background: 'rgba(220, 38, 38, 0.04)',
    iconColor: '#dc2626',
    badge: { background: '#fef2f2', color: '#991b1b' },
  },
  warning: {
    borderColor: '#f59e0b',
    background: 'rgba(245, 158, 11, 0.04)',
    iconColor: '#f59e0b',
    badge: { background: '#fffbeb', color: '#92400e' },
  },
  info: {
    borderColor: '#3b82f6',
    background: 'rgba(59, 130, 246, 0.04)',
    iconColor: '#3b82f6',
    badge: { background: '#eff6ff', color: '#1d4ed8' },
  },
};

export default function AlertasNutricionales({ totales, imcClasificacion }) {
  const alertas = useMemo(() => {
    if (!totales) return [];

    const resultados = [];
    const rangos = RANGOS_CALORICOS[imcClasificacion] || RANGOS_CALORICOS['Normal'];

    if (totales.energia_kcal > rangos.max) {
      const exceso = Math.round(totales.energia_kcal - rangos.max);
      resultados.push({
        severidad: totales.energia_kcal > rangos.max * 1.15 ? 'danger' : 'warning',
        titulo: 'Exceso Calórico',
        mensaje: `El plan aporta ${totales.energia_kcal} kcal, superando el rango recomendado (${rangos.min}-${rangos.max} kcal) en ${exceso} kcal para un perfil "${imcClasificacion}".`,
      });
    } else if (totales.energia_kcal < rangos.min) {
      const deficit = Math.round(rangos.min - totales.energia_kcal);
      resultados.push({
        severidad: totales.energia_kcal < rangos.min * 0.8 ? 'danger' : 'warning',
        titulo: 'Déficit Calórico',
        mensaje: `El plan aporta ${totales.energia_kcal} kcal, por debajo del rango recomendado (${rangos.min}-${rangos.max} kcal) en ${deficit} kcal para un perfil "${imcClasificacion}".`,
      });
    }

    if (totales.sodio_mg > 2300) {
      resultados.push({
        severidad: totales.sodio_mg > 3000 ? 'danger' : 'warning',
        titulo: 'Exceso de Sodio',
        mensaje: `El plan contiene ${Math.round(totales.sodio_mg)} mg de sodio, superando el límite máximo diario de 2300 mg recomendado por la OMS.`,
      });
    }

    if (totales.fibra_g < 25) {
      const faltante = Math.round(25 - totales.fibra_g);
      resultados.push({
        severidad: totales.fibra_g < 15 ? 'danger' : 'warning',
        titulo: 'Fibra Insuficiente',
        mensaje: `El plan aporta ${Math.round(totales.fibra_g)}g de fibra, por debajo del mínimo recomendado de 25g/día. Faltan ${faltante}g.`,
      });
    }

    if (totales.aga_g && totales.aga_g > (totales.energia_kcal * 0.1 / 9)) {
      const limiteGrasaSat = Math.round(totales.energia_kcal * 0.1 / 9 * 10) / 10;
      resultados.push({
        severidad: totales.aga_g > limiteGrasaSat * 1.5 ? 'danger' : 'warning',
        titulo: 'Grasa Saturada Elevada',
        mensaje: `El plan contiene ${Math.round(totales.aga_g)}g de grasa saturada. El límite recomendado es ≤${limiteGrasaSat}g (10% de las calorías totales).`,
      });
    }

    if (totales.proteina_g < 50 && (imcClasificacion === 'Normal' || !imcClasificacion)) {
      resultados.push({
        severidad: 'info',
        titulo: 'Proteína Baja para Paciente Activo',
        mensaje: `El plan aporta ${Math.round(totales.proteina_g)}g de proteína. Si el paciente es físicamente activo, se recomienda al menos 1.2-1.6 g/kg/día.`,
      });
    }

    return resultados;
  }, [totales, imcClasificacion]);

  if (!totales || alertas.length === 0) {
    return (
      <div className="card" style={{ padding: '20px', borderLeft: '4px solid #16a34a' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '1.5rem' }}>✅</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#16a34a', marginBottom: '2px' }}>
              Sin alertas nutricionales
            </div>
            <div style={{ fontSize: '0.82rem', color: 'hsl(var(--text-secondary))' }}>
              Los totales del plan se encuentran dentro de los rangos aceptables.
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: '20px' }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '14px', color: 'hsl(var(--text-primary))' }}>
        Alertas Nutricionales ({alertas.length})
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {alertas.map((alerta, idx) => {
          const estilo = ALERT_STYLES[alerta.severidad] || ALERT_STYLES.info;
          const icono = alerta.severidad === 'danger' ? '🔴' : alerta.severidad === 'warning' ? '🟡' : '🔵';
          return (
            <div
              key={idx}
              style={{
                borderLeft: `4px solid ${estilo.borderColor}`,
                background: estilo.background,
                borderRadius: '8px',
                padding: '12px 16px',
                display: 'flex',
                gap: '12px',
                alignItems: 'flex-start',
              }}
            >
              <span style={{ fontSize: '1.2rem', flexShrink: 0, marginTop: '2px' }}>{icono}</span>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.88rem', color: 'hsl(var(--text-primary))' }}>
                    {alerta.titulo}
                  </span>
                  <span style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    display: 'inline-block',
                    ...estilo.badge,
                    padding: 0,
                    background: estilo.borderColor,
                  }} />
                </div>
                <div style={{ fontSize: '0.82rem', color: 'hsl(var(--text-secondary))', lineHeight: 1.4 }}>
                  {alerta.mensaje}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
