import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import AlertasNutricionales from './AlertasNutricionales';

const COMIDAS = ['Desayuno', 'Almuerzo', 'Cena', 'Colación'];

const TIPOS_PLAN = [
  'Balanceado',
  'Hiperproteico',
  'Cetogénico',
  'Vegano',
  'Hipocalórico',
  'Enfermedad Renal',
];

const NUTRIENTES_DETALLE = [
  { key: 'energia_kcal', label: 'Energía', unit: 'kcal' },
  { key: 'proteina_g', label: 'Proteína', unit: 'g' },
  { key: 'grasa_total_g', label: 'Grasa Total', unit: 'g' },
  { key: 'carbohidratos_g', label: 'Carbohidratos', unit: 'g' },
  { key: 'fibra_g', label: 'Fibra', unit: 'g' },
  { key: 'calcio_mg', label: 'Calcio', unit: 'mg' },
  { key: 'hierro_mg', label: 'Hierro', unit: 'mg' },
  { key: 'sodio_mg', label: 'Sodio', unit: 'mg' },
  { key: 'potasio_mg', label: 'Potasio', unit: 'mg' },
  { key: 'vitamina_c_mg', label: 'Vitamina C', unit: 'mg' },
];

export default function PlanAlimenticio({ token }) {
  const [pacienteId, setPacienteId] = useState('');
  const [tipoPlan, setTipoPlan] = useState('Balanceado');
  const [alimentosPlan, setAlimentosPlan] = useState([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [lastPlanId, setLastPlanId] = useState(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  const [catalogoAlimentos, setCatalogoAlimentos] = useState([]);
  const [busquedaCatalogo, setBusquedaCatalogo] = useState('');
  const [catalogoLoading, setCatalogoLoading] = useState(false);
  const [categorias, setCategorias] = useState([]);
  const [categoriaFiltro, setCategoriaFiltro] = useState('');
  const [paginaCatalogo, setPaginaCatalogo] = useState(0);
  const [alimentoSeleccionado, setAlimentoSeleccionado] = useState(null);
  const limiteCatalogo = 15;

  const [nuevoAlimento, setNuevoAlimento] = useState('');
  const [nuevoGramos, setNuevoGramos] = useState('100');
  const [nuevaComida, setNuevaComida] = useState('Desayuno');

  const [recomendados, setRecomendados] = useState(null);

  useEffect(() => {
    if (token) loadCategorias();
  }, [token]);

  useEffect(() => {
    if (busquedaCatalogo.trim().length >= 2 || categoriaFiltro) {
      const timer = setTimeout(() => buscarCatalogo(), 300);
      return () => clearTimeout(timer);
    }
  }, [busquedaCatalogo, categoriaFiltro, paginaCatalogo, token]);

  const loadCategorias = async () => {
    try {
      const data = await apiService.getCategoriasAlimentos(token);
      setCategorias(data.categorias || []);
    } catch (err) {
      console.error('Error al cargar categorías:', err);
    }
  };

  const buscarCatalogo = async () => {
    setCatalogoLoading(true);
    try {
      const data = await apiService.getAlimentos(token, busquedaCatalogo, categoriaFiltro, limiteCatalogo, paginaCatalogo * limiteCatalogo);
      setCatalogoAlimentos(data.alimentos || []);
    } catch (err) {
      console.error('Error buscando alimentos:', err);
    } finally {
      setCatalogoLoading(false);
    }
  };

  const handleSeleccionarCatalogo = async (alimento) => {
    try {
      const detalle = await apiService.getAlimentoById(token, alimento.id || alimento.alimento_id);
      setAlimentoSeleccionado(detalle || alimento);
    } catch {
      setAlimentoSeleccionado(alimento);
    }
  };

  const calcularNutrientesPorGramos = useCallback((alimento, gramos) => {
    const factor = gramos / 100;
    return {
      energia_kcal: Math.round((alimento.energia_kcal || 0) * factor * 10) / 10,
      proteina_g: Math.round((alimento.proteina_g || 0) * factor * 10) / 10,
      grasa_total_g: Math.round((alimento.grasa_total_g || 0) * factor * 10) / 10,
      carbohidratos_g: Math.round((alimento.carbohidratos_g || 0) * factor * 10) / 10,
      fibra_g: Math.round((alimento.fibra_g || 0) * factor * 10) / 10,
      sodio_mg: Math.round((alimento.sodio_mg || 0) * factor * 10) / 10,
      calcio_mg: Math.round((alimento.calcio_mg || 0) * factor * 10) / 10,
      hierro_mg: Math.round((alimento.hierro_mg || 0) * factor * 10) / 10,
      aga_g: Math.round((alimento.aga_g || 0) * factor * 10) / 10,
    };
  }, []);

  const agregarAlimentoDesdeCatalogo = (alimentoCatalogo) => {
    const gramos = parseInt(nuevoGramos) || 100;
    const nutrientes = calcularNutrientesPorGramos(alimentoCatalogo, gramos);
    setAlimentosPlan([...alimentosPlan, {
      alimento_id: alimentoCatalogo.id || alimentoCatalogo.alimento_id,
      nombre: alimentoCatalogo.nombre,
      gramos,
      comida: nuevaComida,
      nutrientes,
      datos_base: alimentoCatalogo,
    }]);
  };

  const agregarManual = () => {
    if (!nuevoAlimento.trim()) return;
    const gramos = parseInt(nuevoGramos) || 100;
    setAlimentosPlan([...alimentosPlan, {
      alimento_id: null,
      nombre: nuevoAlimento.trim(),
      gramos,
      comida: nuevaComida,
      nutrientes: null,
      datos_base: null,
    }]);
    setNuevoAlimento('');
  };

  const eliminarAlimento = (index) => {
    setAlimentosPlan(alimentosPlan.filter((_, i) => i !== index));
  };

  const estaEnPlan = (alimentoCatalogo) => {
    const id = alimentoCatalogo.id || alimentoCatalogo.alimento_id;
    return alimentosPlan.some((a) => a.alimento_id === id);
  };

  const quitarDelCatalogo = (alimentoCatalogo) => {
    const id = alimentoCatalogo.id || alimentoCatalogo.alimento_id;
    setAlimentosPlan(alimentosPlan.filter((a) => a.alimento_id !== id));
  };

  const actualizarGramos = (index, nuevosGramos) => {
    const copia = [...alimentosPlan];
    copia[index].gramos = parseInt(nuevosGramos) || 0;
    if (copia[index].datos_base) {
      copia[index].nutrientes = calcularNutrientesPorGramos(copia[index].datos_base, copia[index].gramos);
    }
    setAlimentosPlan(copia);
  };

  const actualizarComida = (index, nuevaComida) => {
    const copia = [...alimentosPlan];
    copia[index].comida = nuevaComida;
    setAlimentosPlan(copia);
  };

  const calcularTotales = (items) => {
    const totales = { energia_kcal: 0, proteina_g: 0, grasa_total_g: 0, carbohidratos_g: 0, fibra_g: 0, sodio_mg: 0, calcio_mg: 0, hierro_mg: 0, aga_g: 0 };
    items.forEach((item) => {
      if (item.nutrientes) {
        Object.keys(totales).forEach((key) => {
          totales[key] += item.nutrientes[key] || 0;
        });
      }
    });
    Object.keys(totales).forEach((key) => {
      totales[key] = Math.round(totales[key] * 10) / 10;
    });
    return totales;
  };

  const totalesPorComida = {};
  COMIDAS.forEach((comida) => {
    totalesPorComida[comida] = calcularTotales(alimentosPlan.filter((a) => a.comida === comida));
  });
  const totalesDiarios = calcularTotales(alimentosPlan);

  const handleGuardar = async () => {
    if (!pacienteId.trim()) { setError('Debe ingresar el ID del paciente.'); return; }
    if (alimentosPlan.length === 0) { setError('Debe agregar al menos un alimento al plan.'); return; }
    setSaving(true);
    setError('');
    setSuccessMsg('');
    setLastPlanId(null);
    try {
      const planData = {
        paciente_id: pacienteId,
        tipo_plan: tipoPlan,
        alimentos: alimentosPlan.map((a) => ({
          alimento_id: a.alimento_id,
          nombre: a.nombre,
          cantidad_gramos: a.gramos,
          comida: a.comida,
        })),
      };
      const result = await apiService.crearPlanAlimenticio(token, planData);
      setLastPlanId(result.plan_id);
      setSuccessMsg('Plan alimenticio guardado exitosamente. Ya puedes descargar el PDF.');
    } catch (err) {
      setError(err.message || 'Error al guardar el plan.');
    } finally {
      setSaving(false);
    }
  };

  const handleDescargarPdf = async () => {
    if (!lastPlanId) return;
    setDownloadingPdf(true);
    try {
      await apiService.downloadPlanPdfById(token, lastPlanId);
    } catch (err) {
      setError(err.message || 'Error al descargar el PDF.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const getBarColor = (pct) => {
    if (pct >= 80 && pct <= 120) return '#16a34a';
    if (pct >= 60 && pct <= 140) return '#f59e0b';
    return '#dc2626';
  };

  const renderNutrientBar = (label, value, max, unit) => {
    const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
    const color = getBarColor((value / max) * 100);
    return (
      <div style={{ marginBottom: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '2px' }}>
          <span style={{ color: 'hsl(var(--text-secondary))' }}>{label}</span>
          <span style={{ fontWeight: 600, color: 'hsl(var(--text-primary))' }}>{value} {unit}</span>
        </div>
        <div className="tmb-bar">
          <div className="tmb-bar-fill" style={{ width: `${pct}%`, background: color, transition: 'width 0.5s ease-out, background 0.3s ease' }} />
        </div>
      </div>
    );
  };

  return (
    <div className="dashboard-content">
      <div className="content-header">
        <h1>Plan Alimenticio y Catálogo</h1>
        <p>Explora el catálogo nutricional, selecciona alimentos y construye planes personalizados con cálculo en tiempo real.</p>
      </div>

      <div className="antropometria-grid">
        <div className="card anthrop-card">
          <h2>Configuración del Plan</h2>

          {error && <div className="error-msg">{error}</div>}
          {successMsg && <div className="success-msg">{successMsg}</div>}

          <div className="inline-fields">
            <div className="form-group">
              <label>ID del Paciente</label>
              <input
                type="text"
                value={pacienteId}
                onChange={(e) => setPacienteId(e.target.value)}
                placeholder="ej. PAC-983"
                disabled={saving}
              />
            </div>
            <div className="form-group">
              <label>Tipo de Plan</label>
              <select value={tipoPlan} onChange={(e) => setTipoPlan(e.target.value)} disabled={saving}>
                {TIPOS_PLAN.map((tp) => (
                  <option key={tp} value={tp}>{tp}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="food-builder">
            <span className="food-builder-title">Agregar Alimento al Plan</span>

            <div className="inline-fields" style={{ marginBottom: '8px' }}>
              <div className="form-group" style={{ flex: 2 }}>
                <label>Buscar en Catálogo</label>
                <input
                  type="text"
                  value={busquedaCatalogo}
                  onChange={(e) => { setBusquedaCatalogo(e.target.value); setPaginaCatalogo(0); }}
                  placeholder="Buscar alimento por nombre..."
                  disabled={saving}
                />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Categoría</label>
                <select
                  value={categoriaFiltro}
                  onChange={(e) => { setCategoriaFiltro(e.target.value); setPaginaCatalogo(0); }}
                  disabled={saving}
                >
                  <option value="">Todas</option>
                  {categorias.map((cat, idx) => (
                    <option key={idx} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
            </div>

            {(busquedaCatalogo.trim().length >= 2 || categoriaFiltro) && (
              <div style={{ marginTop: '4px' }}>
                {catalogoLoading ? (
                  <div style={{ fontSize: '0.78rem', color: 'hsl(var(--text-muted))', padding: '8px 0' }}>Buscando alimentos...</div>
                ) : catalogoAlimentos.length === 0 ? (
                  <div style={{ fontSize: '0.78rem', color: 'hsl(var(--text-muted))', padding: '8px 0' }}>Sin resultados. Intenta con otros filtros.</div>
                ) : (
                  <>
                    <div style={{ overflowX: 'auto', border: '1px solid hsl(var(--card-border))', borderRadius: '10px', background: '#fff' }}>
                      <table className="food-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                          <tr style={{ borderBottom: '2px solid hsl(var(--card-border))', textAlign: 'left' }}>
                            <th style={{ padding: '8px 8px', fontSize: '0.75rem' }}>Nombre</th>
                            <th style={{ padding: '8px 8px', fontSize: '0.75rem' }}>Categoría</th>
                            <th style={{ padding: '8px 8px', textAlign: 'right', fontSize: '0.75rem' }}>Kcal</th>
                            <th style={{ padding: '8px 8px', textAlign: 'right', fontSize: '0.75rem' }}>Prot.</th>
                            <th style={{ padding: '8px 8px', textAlign: 'center', fontSize: '0.75rem' }}></th>
                          </tr>
                        </thead>
                        <tbody>
                          {catalogoAlimentos.map((al, idx) => (
                            <tr
                              key={al.id || al.alimento_id || idx}
                              style={{
                                borderBottom: idx < catalogoAlimentos.length - 1 ? '1px solid rgba(0,0,0,0.04)' : 'none',
                                cursor: 'pointer',
                                background: alimentoSeleccionado && (alimentoSeleccionado.id || alimentoSeleccionado.alimento_id) === (al.id || al.alimento_id)
                                  ? 'rgba(30,63,32,0.04)' : 'transparent'
                              }}
                              onClick={() => handleSeleccionarCatalogo(al)}
                              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(30,63,32,0.03)'}
                              onMouseLeave={(e) => {
                                if (!(alimentoSeleccionado && (alimentoSeleccionado.id || alimentoSeleccionado.alimento_id) === (al.id || al.alimento_id))) {
                                  e.currentTarget.style.background = 'transparent';
                                }
                              }}
                            >
                              <td style={{ padding: '8px', fontWeight: 600, fontSize: '0.8rem' }}>{al.nombre}</td>
                              <td style={{ padding: '8px', fontSize: '0.75rem' }}>
                                <span className="food-meal-badge meal-almuerzo">{al.categoria}</span>
                              </td>
                              <td style={{ padding: '8px', textAlign: 'right', fontSize: '0.8rem' }}>{al.energia_kcal ?? '—'}</td>
                              <td style={{ padding: '8px', textAlign: 'right', fontSize: '0.8rem' }}>{al.proteina_g ?? '—'}</td>
                              <td style={{ padding: '8px', textAlign: 'center' }}>
                                {estaEnPlan(al) ? (
                                  <button
                                    type="button"
                                    className="btn btn-secondary"
                                    onClick={(e) => { e.stopPropagation(); quitarDelCatalogo(al); }}
                                    disabled={saving}
                                    style={{ width: 'auto', margin: 0, padding: '3px 10px', fontSize: '0.75rem', background: 'rgba(220,38,38,0.08)', color: '#dc2626', borderColor: 'rgba(220,38,38,0.2)' }}
                                  >
                                    − Quitar
                                  </button>
                                ) : (
                                  <button
                                    type="button"
                                    className="btn btn-secondary"
                                    onClick={(e) => { e.stopPropagation(); agregarAlimentoDesdeCatalogo(al); }}
                                    disabled={saving}
                                    style={{ width: 'auto', margin: 0, padding: '3px 10px', fontSize: '0.75rem' }}
                                  >
                                    + Agregar
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                      <button
                        className="btn btn-secondary"
                        onClick={() => setPaginaCatalogo(Math.max(0, paginaCatalogo - 1))}
                        disabled={paginaCatalogo === 0 || catalogoLoading}
                        style={{ width: 'auto', margin: 0, padding: '4px 12px', fontSize: '0.75rem' }}
                      >
                        ← Anterior
                      </button>
                      <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))' }}>
                        Página {paginaCatalogo + 1}
                      </span>
                      <button
                        className="btn btn-secondary"
                        onClick={() => setPaginaCatalogo(paginaCatalogo + 1)}
                        disabled={catalogoAlimentos.length < limiteCatalogo || catalogoLoading}
                        style={{ width: 'auto', margin: 0, padding: '4px 12px', fontSize: '0.75rem' }}
                      >
                        Siguiente →
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}

            {alimentoSeleccionado && (
              <div style={{
                marginTop: '12px',
                padding: '14px',
                background: 'rgba(30,63,32,0.02)',
                border: '1px solid rgba(30,63,32,0.08)',
                borderRadius: '12px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <strong style={{ fontSize: '0.88rem' }}>{alimentoSeleccionado.nombre}</strong>
                  <button
                    className="btn btn-secondary"
                    onClick={() => setAlimentoSeleccionado(null)}
                    style={{ width: 'auto', margin: 0, padding: '2px 10px', fontSize: '0.72rem' }}
                  >
                    Cerrar
                  </button>
                </div>
                <p style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))', marginBottom: '10px' }}>
                  Valores por cada <strong>100g</strong>. {alimentoSeleccionado.categoria && <>Categoría: <span className="food-meal-badge meal-almuerzo">{alimentoSeleccionado.categoria}</span></>}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: '8px', marginBottom: '12px' }}>
                  {NUTRIENTES_DETALLE.map((n) => (
                    <div key={n.key} style={{
                      background: '#fff',
                      border: '1px solid rgba(30,63,32,0.06)',
                      borderRadius: '8px',
                      padding: '10px',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '0.65rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', marginBottom: '4px' }}>{n.label}</div>
                      <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'hsl(var(--primary))' }}>{alimentoSeleccionado[n.key] ?? '—'}</div>
                      <div style={{ fontSize: '0.65rem', color: 'hsl(var(--text-muted))' }}>{n.unit}</div>
                    </div>
                  ))}
                </div>
                <button
                  className="btn"
                  onClick={() => { agregarAlimentoDesdeCatalogo(alimentoSeleccionado); }}
                  disabled={saving}
                  style={{ width: '100%', margin: 0 }}
                >
                  Agregar al Plan ({nuevoGramos}g)
                </button>
              </div>
            )}

            <div className="food-input-row" style={{ gridTemplateColumns: '1fr 0.5fr 0.8fr auto', marginTop: '12px' }}>
              <input
                type="text"
                value={nuevoAlimento}
                onChange={(e) => setNuevoAlimento(e.target.value)}
                placeholder="Nombre del alimento (manual)"
                disabled={saving}
              />
              <input
                type="number"
                value={nuevoGramos}
                onChange={(e) => setNuevoGramos(e.target.value)}
                placeholder="Gramos"
                min="1"
                disabled={saving}
              />
              <select value={nuevaComida} onChange={(e) => setNuevaComida(e.target.value)} disabled={saving}>
                {COMIDAS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <button type="button" onClick={agregarManual} className="btn btn-secondary" disabled={saving || !nuevoAlimento.trim()}>+</button>
            </div>
          </div>

          {alimentosPlan.length > 0 && (
            <div style={{ marginTop: '8px' }}>
              <span className="food-builder-title">Alimentos en el Plan ({alimentosPlan.length})</span>
              <table className="food-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid hsl(var(--card-border))', textAlign: 'left' }}>
                    <th style={{ padding: '8px 6px' }}>Alimento</th>
                    <th style={{ padding: '8px 6px', textAlign: 'center' }}>Gramos</th>
                    <th style={{ padding: '8px 6px' }}>Comida</th>
                    <th style={{ padding: '8px 6px', textAlign: 'right' }}>Kcal</th>
                    <th style={{ padding: '8px 6px', textAlign: 'right' }}>Prot.</th>
                    <th style={{ padding: '8px 6px', textAlign: 'right' }}>Grasa</th>
                    <th style={{ padding: '8px 6px', textAlign: 'right' }}>Carbs</th>
                    <th style={{ padding: '8px 6px' }}></th>
                  </tr>
                </thead>
                <tbody>
                  {alimentosPlan.map((item, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(0,0,0,0.03)' }}>
                      <td style={{ padding: '8px 6px', fontWeight: 600, fontSize: '0.8rem' }}>{item.nombre}</td>
                      <td style={{ padding: '8px 6px', textAlign: 'center' }}>
                        <input
                          type="number"
                          value={item.gramos}
                          onChange={(e) => actualizarGramos(idx, e.target.value)}
                          style={{ width: '60px', padding: '4px 6px', fontSize: '0.78rem', textAlign: 'center', borderRadius: '8px', border: '1px solid hsl(var(--card-border))' }}
                          min="1"
                          disabled={saving}
                        />
                      </td>
                      <td style={{ padding: '8px 6px' }}>
                        <select
                          value={item.comida}
                          onChange={(e) => actualizarComida(idx, e.target.value)}
                          style={{ padding: '4px 6px', fontSize: '0.75rem', borderRadius: '8px', border: '1px solid hsl(var(--card-border))', background: '#fff' }}
                          disabled={saving}
                        >
                          {COMIDAS.map((c) => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </td>
                      <td style={{ padding: '8px 6px', textAlign: 'right', fontSize: '0.78rem' }}>{item.nutrientes ? item.nutrientes.energia_kcal : '—'}</td>
                      <td style={{ padding: '8px 6px', textAlign: 'right', fontSize: '0.78rem' }}>{item.nutrientes ? item.nutrientes.proteina_g : '—'}</td>
                      <td style={{ padding: '8px 6px', textAlign: 'right', fontSize: '0.78rem' }}>{item.nutrientes ? item.nutrientes.grasa_total_g : '—'}</td>
                      <td style={{ padding: '8px 6px', textAlign: 'right', fontSize: '0.78rem' }}>{item.nutrientes ? item.nutrientes.carbohidratos_g : '—'}</td>
                      <td style={{ padding: '8px 6px' }}>
                        <button type="button" onClick={() => eliminarAlimento(idx)} className="remove-btn" disabled={saving}>✕</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="form-actions" style={{ marginTop: '16px', display: 'flex', gap: '10px' }}>
            <button className="btn" onClick={handleGuardar} disabled={saving || alimentosPlan.length === 0}>
              {saving ? <div className="spinner"></div> : 'Guardar Plan'}
            </button>
            {lastPlanId && (
              <button
                className="btn"
                onClick={handleDescargarPdf}
                disabled={downloadingPdf}
                style={{ background: 'hsl(var(--primary))', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                {downloadingPdf ? <div className="spinner"></div> : '📄'} Descargar PDF
              </button>
            )}
          </div>
        </div>

        <div className="card anthrop-results">
          <h2>Resumen Nutricional</h2>

          {alimentosPlan.length === 0 ? (
            <div className="results-empty">
              <span className="results-empty-icon">📊</span>
              <h3>Sin alimentos agregados</h3>
              <p>Busca en el catálogo o agrega alimentos manualmente para ver el cálculo nutricional en tiempo real.</p>
            </div>
          ) : (
            <div className="results-content">
              <div className="result-section">
                <h3>Totales Diarios</h3>
                {renderNutrientBar('Energía', totalesDiarios.energia_kcal, 3000, 'kcal')}
                {renderNutrientBar('Proteína', totalesDiarios.proteina_g, 200, 'g')}
                {renderNutrientBar('Grasa', totalesDiarios.grasa_total_g, 100, 'g')}
                {renderNutrientBar('Carbohidratos', totalesDiarios.carbohidratos_g, 400, 'g')}
                {renderNutrientBar('Fibra', totalesDiarios.fibra_g, 40, 'g')}
                {renderNutrientBar('Sodio', totalesDiarios.sodio_mg, 2300, 'mg')}
              </div>

              <AlertasNutricionales totales={totalesDiarios} />

              {COMIDAS.map((comida) => {
                const totales = totalesPorComida[comida];
                const count = alimentosPlan.filter((a) => a.comida === comida).length;
                if (count === 0) return null;
                return (
                  <div key={comida} className="meal-section">
                    <span className="meal-title">{comida} ({count} alimentos)</span>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '6px', fontSize: '0.78rem', marginTop: '4px' }}>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ color: 'hsl(var(--text-muted))', fontSize: '0.68rem' }}>Kcal</div>
                        <div style={{ fontWeight: 700, color: 'hsl(var(--text-primary))' }}>{totales.energia_kcal}</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ color: 'hsl(var(--text-muted))', fontSize: '0.68rem' }}>Prot.</div>
                        <div style={{ fontWeight: 700, color: 'hsl(var(--text-primary))' }}>{totales.proteina_g}g</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ color: 'hsl(var(--text-muted))', fontSize: '0.68rem' }}>Grasa</div>
                        <div style={{ fontWeight: 700, color: 'hsl(var(--text-primary))' }}>{totales.grasa_total_g}g</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ color: 'hsl(var(--text-muted))', fontSize: '0.68rem' }}>Carbs</div>
                        <div style={{ fontWeight: 700, color: 'hsl(var(--text-primary))' }}>{totales.carbohidratos_g}g</div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {recomendados && (
                <div className="result-section" style={{ marginTop: '12px' }}>
                  <h3>Comparación con Recomendados</h3>
                  <table className="food-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid hsl(var(--card-border))' }}>
                        <th style={{ padding: '8px 6px' }}>Nutriente</th>
                        <th style={{ padding: '8px 6px', textAlign: 'right' }}>Plan</th>
                        <th style={{ padding: '8px 6px', textAlign: 'right' }}>Recomendado</th>
                        <th style={{ padding: '8px 6px', textAlign: 'right' }}>Diferencia</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { label: 'Energía (kcal)', plan: totalesDiarios.energia_kcal, rec: recomendados.energia_kcal || 0 },
                        { label: 'Proteína (g)', plan: totalesDiarios.proteina_g, rec: recomendados.proteina_g || 0 },
                        { label: 'Grasa (g)', plan: totalesDiarios.grasa_total_g, rec: recomendados.grasa_total_g || 0 },
                        { label: 'Carbohidratos (g)', plan: totalesDiarios.carbohidratos_g, rec: recomendados.carbohidratos_g || 0 },
                        { label: 'Fibra (g)', plan: totalesDiarios.fibra_g, rec: recomendados.fibra_g || 0 },
                      ].map((row) => {
                        const diff = Math.round((row.plan - row.rec) * 10) / 10;
                        const diffColor = Math.abs(diff) <= row.rec * 0.1 ? '#16a34a' : Math.abs(diff) <= row.rec * 0.25 ? '#ea580c' : '#dc2626';
                        return (
                          <tr key={row.label} style={{ borderBottom: '1px solid rgba(0,0,0,0.03)' }}>
                            <td style={{ padding: '8px 6px', fontWeight: 600 }}>{row.label}</td>
                            <td style={{ padding: '8px 6px', textAlign: 'right' }}>{row.plan}</td>
                            <td style={{ padding: '8px 6px', textAlign: 'right' }}>{row.rec}</td>
                            <td style={{ padding: '8px 6px', textAlign: 'right', fontWeight: 700, color: diffColor }}>
                              {diff > 0 ? '+' : ''}{diff}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
