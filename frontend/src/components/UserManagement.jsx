import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

export default function UserManagement({ token, currentUsername }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [showSensitiveData, setShowSensitiveData] = useState(false);

  // Estados para ordenar y filtrar
  const [sortField, setSortField] = useState(null);
  const [sortDirection, setSortDirection] = useState(null); // 'asc', 'desc' o null
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    username: '',
    nombre: '',
    email: '',
    cedula: '',
    fecha_nacimiento: '',
    role: ''
  });

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    setSuccessMessage('');
    try {
      const data = await apiService.getAdminUsers(token);
      setUsers(data || []);
    } catch (err) {
      setError(err.message || 'Error al cargar los usuarios.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      loadUsers();
    }
  }, [token]);

  const handleToggleRole = async (username, currentRole) => {
    const newRole = currentRole === 'Docentes' ? 'Estudiantes' : 'Docentes';
    setError('');
    setSuccessMessage('');
    try {
      const res = await apiService.updateAdminUserRole(token, username, newRole);
      setSuccessMessage(res.message || `Rol de ${username} cambiado a ${newRole} con éxito.`);
      loadUsers();
    } catch (err) {
      setError(err.message || 'Error al actualizar el rol.');
    }
  };

  const handleDeleteUser = async (username) => {
    if (!window.confirm(`¿Estás seguro de que deseas eliminar permanentemente al usuario "${username}"?`)) {
      return;
    }
    setError('');
    setSuccessMessage('');
    try {
      const res = await apiService.deleteAdminUser(token, username);
      setSuccessMessage(res.message || `Usuario ${username} eliminado con éxito.`);
      loadUsers();
    } catch (err) {
      setError(err.message || 'Error al eliminar el usuario.');
    }
  };

  // Lógica de Ordenación
  const handleSort = (field) => {
    let direction = 'asc';
    if (sortField === field) {
      if (sortDirection === 'asc') {
        direction = 'desc';
      } else if (sortDirection === 'desc') {
        direction = null;
      }
    }
    setSortField(direction ? field : null);
    setSortDirection(direction);
  };

  // Lógica de Filtrado
  const handleFilterChange = (field, value) => {
    setFilters((prev) => ({
      ...prev,
      [field]: value
    }));
  };

  const clearFilters = () => {
    setFilters({
      username: '',
      nombre: '',
      email: '',
      cedula: '',
      fecha_nacimiento: '',
      role: ''
    });
  };

  const getProcessedUsers = () => {
    let result = [...users];

    // 1. Filtrar
    Object.keys(filters).forEach((key) => {
      const filterValue = filters[key].toLowerCase().trim();
      if (filterValue) {
        result = result.filter((user) => {
          const userVal = String(user[key] || '').toLowerCase();
          return userVal.includes(filterValue);
        });
      }
    });

    // 2. Ordenar
    if (sortField && sortDirection) {
      result.sort((a, b) => {
        const valA = String(a[sortField] || '').toLowerCase();
        const valB = String(b[sortField] || '').toLowerCase();
        if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
        if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return result;
  };

  const maskText = (text, type) => {
    if (!text) return 'N/A';
    if (showSensitiveData) return text;
    switch (type) {
      case 'name':
        return text.split(' ').map(part => {
          if (part.length <= 2) return part;
          return part[0] + '•'.repeat(part.length - 2) + part[part.length - 1];
        }).join(' ');
      case 'cedula':
        if (text.length <= 6) return '••••••';
        return text.substring(0, 3) + '•'.repeat(text.length - 6) + text.substring(text.length - 3);
      case 'birthdate':
        return text.replace(/-(\d{2})-(\d{2})$/, '-••-••');
      case 'email':
        const parts = text.split('@');
        if (parts.length < 2) return text;
        const user = parts[0];
        const domain = parts[1];
        if (user.length <= 2) return '••@' + domain;
        return user.substring(0, 2) + '•'.repeat(user.length - 2) + '@' + domain;
      default:
        return '••••••••';
    }
  };

  const renderSortIndicator = (field) => {
    if (sortField !== field) return <span style={{ color: 'hsl(var(--text-muted))', marginLeft: '6px', fontSize: '0.8rem' }}>⇅</span>;
    if (sortDirection === 'asc') return <span style={{ color: 'hsl(var(--primary))', marginLeft: '6px', fontSize: '0.8rem', fontWeight: 'bold' }}>▲</span>;
    return <span style={{ color: 'hsl(var(--primary))', marginLeft: '6px', fontSize: '0.8rem', fontWeight: 'bold' }}>▼</span>;
  };

  const processedUsers = getProcessedUsers();

  return (
    <div className="dashboard-content">
      <div className="content-header" style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Gestión de Usuarios</h1>
          <p>Módulo administrativo para la gestión de docentes, estudiantes y control de accesos.</p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button onClick={() => setShowFilters(!showFilters)} className="toggle-data-btn" style={{ borderColor: showFilters ? 'hsl(var(--primary))' : '' }}>
            {showFilters ? 'Ocultar Filtros' : 'Filtrar y Buscar'}
          </button>
          <button onClick={() => setShowSensitiveData(!showSensitiveData)} className="toggle-data-btn">
            {showSensitiveData ? 'Ocultar Datos' : 'Mostrar Datos'}
          </button>
          <button onClick={loadUsers} className="toggle-data-btn" disabled={loading}>
            {loading ? 'Cargando...' : 'Refrescar'}
          </button>
        </div>
      </div>

      {error && <div className="error-msg">{error}</div>}
      {successMessage && <div className="success-msg">{successMessage}</div>}

      <div className="card" style={{ padding: '24px', overflowX: 'auto' }}>
        {loading ? (
          <div className="spinner-container">
            <div className="spinner" style={{ borderColor: 'rgba(30,63,32,0.1)', borderTopColor: 'hsl(var(--primary))' }}></div>
          </div>
        ) : users.length === 0 ? (
          <p className="empty-state">No se encontraron usuarios en el sistema.</p>
        ) : (
          <table className="food-table" style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid hsl(var(--card-border))', textAlign: 'left' }}>
                <th onClick={() => handleSort('username')} style={{ padding: '12px 8px', cursor: 'pointer', userSelect: 'none' }}>
                  Usuario {renderSortIndicator('username')}
                </th>
                <th onClick={() => handleSort('nombre')} style={{ padding: '12px 8px', cursor: 'pointer', userSelect: 'none' }}>
                  Nombre Completo {renderSortIndicator('nombre')}
                </th>
                <th onClick={() => handleSort('email')} style={{ padding: '12px 8px', cursor: 'pointer', userSelect: 'none' }}>
                  Correo Electrónico {renderSortIndicator('email')}
                </th>
                <th onClick={() => handleSort('cedula')} style={{ padding: '12px 8px', cursor: 'pointer', userSelect: 'none' }}>
                  Cédula {renderSortIndicator('cedula')}
                </th>
                <th onClick={() => handleSort('fecha_nacimiento')} style={{ padding: '12px 8px', cursor: 'pointer', userSelect: 'none' }}>
                  F. Nacimiento {renderSortIndicator('fecha_nacimiento')}
                </th>
                <th onClick={() => handleSort('role')} style={{ padding: '12px 8px', cursor: 'pointer', userSelect: 'none' }}>
                  Rol / Grupo {renderSortIndicator('role')}
                </th>
                <th style={{ padding: '12px 8px', textAlign: 'center', userSelect: 'none' }}>Acciones</th>
              </tr>

              {/* Fila de Filtros */}
              {showFilters && (
                <tr style={{ background: 'rgba(120, 110, 90, 0.03)', borderBottom: '1px solid hsl(var(--card-border))' }}>
                  <td style={{ padding: '6px 8px' }}>
                    <input
                      type="text"
                      placeholder="Filtrar..."
                      value={filters.username}
                      onChange={(e) => handleFilterChange('username', e.target.value)}
                      style={{ padding: '6px 10px', fontSize: '0.8rem', borderRadius: '8px', border: '1px solid hsl(var(--card-border))' }}
                    />
                  </td>
                  <td style={{ padding: '6px 8px' }}>
                    <input
                      type="text"
                      placeholder="Filtrar..."
                      value={filters.nombre}
                      onChange={(e) => handleFilterChange('nombre', e.target.value)}
                      style={{ padding: '6px 10px', fontSize: '0.8rem', borderRadius: '8px', border: '1px solid hsl(var(--card-border))' }}
                    />
                  </td>
                  <td style={{ padding: '6px 8px' }}>
                    <input
                      type="text"
                      placeholder="Filtrar..."
                      value={filters.email}
                      onChange={(e) => handleFilterChange('email', e.target.value)}
                      style={{ padding: '6px 10px', fontSize: '0.8rem', borderRadius: '8px', border: '1px solid hsl(var(--card-border))' }}
                    />
                  </td>
                  <td style={{ padding: '6px 8px' }}>
                    <input
                      type="text"
                      placeholder="Filtrar..."
                      value={filters.cedula}
                      onChange={(e) => handleFilterChange('cedula', e.target.value)}
                      style={{ padding: '6px 10px', fontSize: '0.8rem', borderRadius: '8px', border: '1px solid hsl(var(--card-border))' }}
                    />
                  </td>
                  <td style={{ padding: '6px 8px' }}>
                    <input
                      type="text"
                      placeholder="Filtrar..."
                      value={filters.fecha_nacimiento}
                      onChange={(e) => handleFilterChange('fecha_nacimiento', e.target.value)}
                      style={{ padding: '6px 10px', fontSize: '0.8rem', borderRadius: '8px', border: '1px solid hsl(var(--card-border))' }}
                    />
                  </td>
                  <td style={{ padding: '6px 8px' }}>
                    <select
                      value={filters.role}
                      onChange={(e) => handleFilterChange('role', e.target.value)}
                      style={{ padding: '6px 10px', fontSize: '0.8rem', borderRadius: '8px', border: '1px solid hsl(var(--card-border))', height: 'auto', background: '#fff' }}
                    >
                      <option value="">Todos</option>
                      <option value="Docentes">Docentes</option>
                      <option value="Estudiantes">Estudiantes</option>
                    </select>
                  </td>
                  <td style={{ padding: '6px 8px', textAlign: 'center' }}>
                    <button
                      onClick={clearFilters}
                      className="btn btn-secondary"
                      style={{ width: 'auto', margin: 0, padding: '4px 10px', fontSize: '0.75rem' }}
                    >
                      Limpiar
                    </button>
                  </td>
                </tr>
              )}
            </thead>
            <tbody>
              {processedUsers.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '24px', color: 'hsl(var(--text-muted))' }}>
                    Ningún usuario coincide con los filtros aplicados.
                  </td>
                </tr>
              ) : (
                processedUsers.map((user) => {
                  const isSelf = user.username === currentUsername;
                  return (
                    <tr key={user.username} style={{ borderBottom: '1px solid hsl(var(--card-border))' }}>
                      <td style={{ padding: '14px 8px', fontWeight: 600 }}>
                        {user.username} {isSelf && <span style={{ fontSize: '0.75rem', color: 'hsl(var(--text-muted))' }}>(Tú)</span>}
                      </td>
                      <td style={{ padding: '14px 8px' }}>{maskText(user.nombre, 'name')}</td>
                      <td style={{ padding: '14px 8px' }}>{maskText(user.email, 'email')}</td>
                      <td style={{ padding: '14px 8px' }}>{maskText(user.cedula, 'cedula')}</td>
                      <td style={{ padding: '14px 8px' }}>{maskText(user.fecha_nacimiento, 'birthdate')}</td>
                      <td style={{ padding: '14px 8px' }}>
                        <span className={`credential-badge ${user.role === 'Docentes' ? 'badge-teacher' : 'badge-student'}`}>
                          {user.role}
                        </span>
                      </td>
                      <td style={{ padding: '14px 8px', display: 'flex', gap: '8px', justifyContent: 'center' }}>
                        <button
                          onClick={() => handleToggleRole(user.username, user.role)}
                          disabled={isSelf}
                          className="btn btn-secondary"
                          style={{
                            width: 'auto',
                            margin: 0,
                            padding: '6px 12px',
                            fontSize: '0.8rem',
                            cursor: isSelf ? 'not-allowed' : 'pointer'
                          }}
                          title={isSelf ? 'No puedes cambiar tu propio rol' : `Cambiar rol a ${user.role === 'Docentes' ? 'Estudiantes' : 'Docentes'}`}
                        >
                          Cambiar Rol
                        </button>
                        <button
                          onClick={() => handleDeleteUser(user.username)}
                          disabled={isSelf}
                          className="btn"
                          style={{
                            width: 'auto',
                            margin: 0,
                            padding: '6px 12px',
                            fontSize: '0.8rem',
                            backgroundColor: isSelf ? 'hsl(var(--text-muted))' : '#ef4444',
                            color: '#fff',
                            cursor: isSelf ? 'not-allowed' : 'pointer'
                          }}
                          title={isSelf ? 'No puedes eliminarte a ti mismo' : 'Eliminar usuario'}
                        >
                          Eliminar
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
