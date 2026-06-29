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
  register: async (username, email, password, role, nombre, cedula, fecha_nacimiento) => {
    const url = `${getBaseUrl()}/api/v1/auth/register`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, email, password, role, nombre, cedula, fecha_nacimiento }),
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
    const url = `${getBaseUrl()}/api/v1/auth/login`;
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
    const url = `${getBaseUrl()}/api/v1/admin/tasks`;
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
   * Obtiene la lista de usuarios (Solo Docentes)
   * @param {string} token 
   */
  getAdminUsers: async (token) => {
    const url = `${getBaseUrl()}/api/v1/admin/users`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener lista de usuarios');
    }
    return data;
  },

  /**
   * Elimina un usuario por su username (Solo Docentes)
   * @param {string} token 
   * @param {string} username 
   */
  deleteAdminUser: async (token, username) => {
    const url = `${getBaseUrl()}/api/v1/admin/users/${username}`;
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al eliminar usuario');
    }
    return data;
  },

  /**
   * Actualiza el rol de un usuario (Solo Docentes)
   * @param {string} token 
   * @param {string} username 
   * @param {string} role "Docentes" o "Estudiantes"
   */
  updateAdminUserRole: async (token, username, role) => {
    const url = `${getBaseUrl()}/api/v1/admin/users/${username}/role`;
    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ role }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al actualizar el rol del usuario');
    }
    return data;
  },


  /**
   * Solicita el cálculo de un plan nutricional
   * @param {string} token 
   * @param {object} planData 
   */
  createPlan: async (token, planData) => {
    const url = `${getBaseUrl()}/api/v1/plan`;
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
  },

  /**
   * Envía los datos antropométricos del paciente para el cálculo síncrono.
   * @param {string} token 
   * @param {object} clinicalData 
   */
  calculateClinical: async (token, clinicalData) => {
    const url = `${getBaseUrl()}/api/v1/clinical/calculate`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(clinicalData),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al realizar el cálculo antropométrico');
    }
    return data;
  },

  /**
   * Obtiene el estado actual de una tarea de plan nutricional por su ID
   * @param {string} token 
   * @param {string} taskId 
   */
  getTaskStatus: async (token, taskId) => {
    const url = `${getBaseUrl()}/api/v1/tasks/${taskId}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener estado de la tarea');
    }
    return data;
  },

  /**
   * Descarga el PDF del plan nutricional.
   * @param {string} token
   * @param {string} taskId
   */
  forgotPassword: async (email) => {
    const url = `${getBaseUrl()}/api/v1/auth/forgot-password`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al solicitar recuperación de contraseña');
    }
    return data;
  },

  resetPassword: async (username, resetToken, newPassword) => {
    const url = `${getBaseUrl()}/api/v1/auth/reset-password`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, reset_token: resetToken, new_password: newPassword }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al restablecer la contraseña');
    }
    return data;
  },

  downloadPlanPdf: async (token, taskId) => {
    const url = `${getBaseUrl()}/api/v1/plan/${taskId}/pdf`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Error al descargar PDF');
    }
    const blob = await response.blob();
    const filename = response.headers.get('content-disposition')?.match(/filename="(.+)"/)?.[1] || `plan_nutricional_${taskId.slice(0, 8)}.pdf`;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  }
};
