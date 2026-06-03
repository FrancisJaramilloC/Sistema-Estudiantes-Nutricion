const getBaseUrl = () => {
  const hostname = window.location.hostname;
  // Si estamos en localhost o IP local, usa el puerto 8000 de la misma máquina
  return `http://${hostname}:8000`;
};

export const apiService = {
  /**
   * Registra un nuevo usuario en Cognito
   * @param {string} username 
   * @param {string} email 
   * @param {string} password 
   * @param {string} role "Estudiantes" o "Docentes"
   */
  register: async (username, email, password, role) => {
    const url = `${getBaseUrl()}/auth/register`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, email, password, role }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error en el registro');
    }
    return data;
  },

  /**
   * Inicia sesión de un usuario y obtiene el token JWT
   * @param {string} username 
   * @param {string} password 
   */
  login: async (username, password) => {
    const url = `${getBaseUrl()}/auth/login`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error en el inicio de sesión');
    }
    return data;
  },

  /**
   * Obtiene la lista de tareas del panel de administrador (Solo Docentes)
   * @param {string} token Token JWT
   */
  getAdminTasks: async (token) => {
    const url = `${getBaseUrl()}/admin/tasks`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener auditoría');
    }
    return data;
  },

  /**
   * Solicita el cálculo de un plan nutricional
   * @param {string} token 
   * @param {object} planData 
   */
  createPlan: async (token, planData) => {
    const url = `${getBaseUrl()}/plan`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(planData),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al solicitar el plan');
    }
    return data;
  }
};
