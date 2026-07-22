import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

export default function CatalogoAlimentos({ token }) {
  const [alimentos, setAlimentos] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [busqueda, setBusqueda] = useState('');
  const [categoriaFiltro, setCategoriaFiltro] = useState('');
  const [pagina, setPagina] = useState(0);
  const limite = 15;

  const [alimentoSeleccionado, setAlimentoSeleccionado] = useState(null);
  const [detalleLoading, setDetalleLoading] = useState(false);

  useEffect(() => {
    if (token) loadCategorias();
  }, [token]);

  useEffect(() => {
    if (token) loadAlimentos();
  }, [token, busqueda, categoriaFiltro, pagina]);

  const loadCategorias = async () => {
    try {
      const data = await apiService.getCategoriasAlimentos(token);
      setCategorias(data.categorias || []);
    } catch (err) {
      console.error('Error al cargar categorías:', err);
    }
  };

  const loadAlimentos = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await apiService.getAlimentos(token, busqueda, categoriaFiltro, limite, pagina * limite);
      setAlimentos(data.alimentos || []);
    } catch (err) {
      setError(err.message || 'Error al cargar el catálogo de alimentos.');
    } finally {
      setLoading(false);
    }
  };

  const handleSeleccionar = async (alimento) => {
    setDetalleLoading(true);
    try {
      const detalle = await apiService.getAlimentoById(token, alimento.id || alimento.alimento_id);
      setAlimentoSeleccionado(detalle || alimento);
    } catch (err) {
      setAlimentoSeleccionado(alimento);
    } finally {
      setDetalleLoading(false);
    }
  };

  const handleBusquedaChange = (e) => {
    setBusqueda(e.target.value);
    setPagina(0);
  };

  const handleCategoriaChange = (e) => {
    setCategoriaFiltro(e.target.value);
    setPagina(0);
  };

  const nutrientas = [
    { key: 'energia_kcal', label: 'Energía', unit: 'kcal' },
    { key: 'proteina_g', label: 'Proteína', unit: 'g' },
    { key: 'grasa_total_g', label: 'Grasa', unit: 'g' },
    { key: 'carbohidratos_g', label: 'Carbohidratos', unit: 'g' },
    { key: 'fibra_g', label: 'Fibra', unit: 'g' },
    { key: 'calcio_mg', label: 'Calcio', unit: 'mg' },
    { key: 'hierro_mg', label: 'Hierro', unit: 'mg' },
    { key: 'sodio_mg', label: 'Sodio', unit: 'mg' },
    { key: 'potasio_mg', label: 'Potasio', unit: 'mg' },
    { key: 'vitamina_c_mg', label: 'Vitamina C', unit: 'mg' },
  ];

  return (
    <div className="dashboard-content">
      <div className="content-header">
        <h1>Catálogo de Alimentos</h1>
        <p>Explora la base de datos nutricional. Busca por nombre, filtra por categoría y consulta la información detallada por cada 100g.</p>
      </div>

      <div className="antropometria-grid">
        <div className="card anthrop-card">
          <h2>Filtros de Búsqueda</h2>

          <div className="form-group">
            <label>Buscar por Nombre</label>
            <input
              type="text"
              value={busqueda}
              onChange={handleBusquedaChange}
              placeholder="Ej. pollo, arroz, manzana..."
            />
          </div>

          <div className="form-group">
            <label>Categoría</label>
            <select value={categoriaFiltro} onChange={handleCategoriaChange}>
              <option value="">Todas las categorías</option>
              {categorias.map((cat, idx) => (
                <option key={idx} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <button className="btn" onClick={() => { setPagina(0); loadAlimentos(); }} disabled={loading}>
              {loading ? <div className="spinner"></div> : 'Buscar'}
            </button>
            <button className="btn btn-secondary" onClick={() => { setBusqueda(''); setCategoriaFiltro(''); setPagina(0); }} disabled={loading}>
              Limpiar
            </button>
          </div>

          {error && <div className="error-msg" style={{ marginTop: '12px' }}>{error}</div>}

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
            <button
              className="btn btn-secondary"
              onClick={() => setPagina(Math.max(0, pagina - 1))}
              disabled={pagina === 0 || loading}
              style={{ width: 'auto', margin: 0, padding: '6px 14px', fontSize: '0.8rem' }}
            >
              ← Anterior
            </button>
            <span style={{ fontSize: '0.8rem', color: 'hsl(var(--text-muted))' }}>
              Página {pagina + 1}
            </span>
            <button
              className="btn btn-secondary"
              onClick={() => setPagina(pagina + 1)}
              disabled={alimentos.length < limite || loading}
              style={{ width: 'auto', margin: 0, padding: '6px 14px', fontSize: '0.8rem' }}
            >
              Siguiente →
            </button>
          </div>
        </div>

        <div className="card anthrop-results">
          <h2>Resultados del Catálogo</h2>

          {loading ? (
            <div className="spinner-container">
              <div className="spinner" style={{ borderColor: 'rgba(30,63,32,0.1)', borderTopColor: 'hsl(var(--primary))' }}></div>
            </div>
          ) : alimentos.length === 0 ? (
            <div className="results-empty">
              <span className="results-empty-icon">🍽️</span>
              <h3>Sin resultados</h3>
              <p>Intenta ajustar los filtros de búsqueda para encontrar alimentos.</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="food-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid hsl(var(--card-border))', textAlign: 'left' }}>
                    <th style={{ padding: '10px 8px' }}>Nombre</th>
                    <th style={{ padding: '10px 8px' }}>Categoría</th>
                    <th style={{ padding: '10px 8px', textAlign: 'right' }}>Energía</th>
                    <th style={{ padding: '10px 8px', textAlign: 'right' }}>Proteína</th>
                    <th style={{ padding: '10px 8px', textAlign: 'right' }}>Grasa</th>
                    <th style={{ padding: '10px 8px', textAlign: 'right' }}>Carbohidratos</th>
                    <th style={{ padding: '10px 8px' }}></th>
                  </tr>
                </thead>
                <tbody>
                  {alimentos.map((al, idx) => (
                    <tr
                      key={al.id || al.alimento_id || idx}
                      style={{
                        borderBottom: '1px solid rgba(0,0,0,0.03)',
                        cursor: 'pointer',
                        background: alimentoSeleccionado && (alimentoSeleccionado.id || alimentoSeleccionado.alimento_id) === (al.id || al.alimento_id)
                          ? 'rgba(30,63,32,0.04)' : 'transparent'
                      }}
                      onClick={() => handleSeleccionar(al)}
                    >
                      <td style={{ padding: '10px 8px', fontWeight: 600, fontSize: '0.82rem' }}>{al.nombre}</td>
                      <td style={{ padding: '10px 8px', fontSize: '0.78rem' }}>
                        <span className="food-meal-badge meal-almuerzo">{al.categoria}</span>
                      </td>
                      <td style={{ padding: '10px 8px', textAlign: 'right', fontSize: '0.82rem' }}>{al.energia_kcal ?? '—'}</td>
                      <td style={{ padding: '10px 8px', textAlign: 'right', fontSize: '0.82rem' }}>{al.proteina_g ?? '—'}</td>
                      <td style={{ padding: '10px 8px', textAlign: 'right', fontSize: '0.82rem' }}>{al.grasa_total_g ?? '—'}</td>
                      <td style={{ padding: '10px 8px', textAlign: 'right', fontSize: '0.82rem' }}>{al.carbohidratos_g ?? '—'}</td>
                      <td style={{ padding: '10px 8px', textAlign: 'center', fontSize: '0.82rem', color: 'hsl(var(--primary))', fontWeight: 600 }}>→</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {alimentoSeleccionado && (
        <div className="card" style={{ marginTop: '24px', padding: '28px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(30,63,32,0.08)', paddingBottom: '8px', marginBottom: '16px' }}>
            <h2 style={{ margin: 0, textAlign: 'left', fontSize: '1.2rem' }}>
              Información Nutricional Detallada — {alimentoSeleccionado.nombre}
            </h2>
            <button
              className="btn btn-secondary"
              onClick={() => setAlimentoSeleccionado(null)}
              style={{ width: 'auto', margin: 0, padding: '4px 12px', fontSize: '0.78rem' }}
            >
              Cerrar
            </button>
          </div>

          <p style={{ fontSize: '0.85rem', marginBottom: '16px', color: 'hsl(var(--text-muted))' }}>
            Valores por cada <strong>100g</strong> de porción edible. {alimentoSeleccionado.categoria && <>Categoría: <span className="food-meal-badge meal-almuerzo">{alimentoSeleccionado.categoria}</span></>}
          </p>

          {detalleLoading ? (
            <div className="spinner-container">
              <div className="spinner" style={{ borderColor: 'rgba(30,63,32,0.1)', borderTopColor: 'hsl(var(--primary))' }}></div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
              {nutrientas.map((n) => (
                <div key={n.key} style={{
                  background: 'rgba(30,63,32,0.02)',
                  border: '1px solid rgba(30,63,32,0.06)',
                  borderRadius: '12px',
                  padding: '14px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '0.72rem', color: 'hsl(var(--text-muted))', textTransform: 'uppercase', marginBottom: '6px' }}>
                    {n.label}
                  </div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'hsl(var(--primary))' }}>
                    {alimentoSeleccionado[n.key] ?? '—'}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'hsl(var(--text-muted))' }}>{n.unit}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
