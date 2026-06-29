import React from 'react';

export default function Sidebar({ username, role, userPayload, activeTab, onLogout, sidebarOpen, onToggle }) {
  const menuItems = [
    { key: 'inicio', hash: '#/dashboard/inicio', icon: '🏠', label: 'Inicio' },
    { key: 'antropometria', hash: '#/dashboard/antropometria', icon: '⚖️', label: 'Antropometría' },
    { key: 'plan', hash: '#/dashboard/plan-nutricional', icon: '🍎', label: 'Plan Nutricional' },
  ];

  if (role === 'Docentes') {
    menuItems.push({ key: 'usuarios', hash: '#/dashboard/usuarios', icon: '👥', label: 'Gestión de Usuarios' });
  }


  return (
    <div className={`sidebar ${sidebarOpen ? '' : 'sidebar-hidden'}`}>
      <div className="sidebar-header">
        <img src="/nutria-logo.png" alt="NutriA" className="sidebar-logo" />
        <span className="sidebar-title">Portal NutriA</span>
      </div>

      <div className="sidebar-credential">
        <div className="credential-avatar">
          {username.substring(0, 2).toUpperCase()}
        </div>
        <div className="credential-info">
          <p className="credential-name">
            {userPayload?.name?.split(' ')[0] || username}
          </p>
          <span className={`credential-badge ${role === 'Docentes' ? 'badge-teacher' : 'badge-student'}`}>
            {role}
          </span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <button
            key={item.key}
            onClick={() => { window.location.hash = item.hash; }}
            className={`sidebar-nav-item ${activeTab === item.key ? 'nav-item-active' : ''}`}
          >
            <span>{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <button onClick={onLogout} className="btn btn-secondary sidebar-logout">
        Cerrar Sesión
      </button>
    </div>
  );
}
