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

  logout: async (username) => {
    const url = `${getBaseUrl()}/api/v1/auth/logout`;
    try {
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username }),
      });
    } catch {
    }
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
/**
   * Obtiene los eventos de auditoría de inicio de sesión (Solo Docentes)
   * @param {string} token Token JWT
   */
  getLoginAudit: async (token) => {
    const url = `${getBaseUrl()}/api/v1/admin/audit/login-events`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener auditoría de accesos');
    }
    return data;
  },
 
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
  },

  downloadPlanPdfById: async (token, planId) => {
    const url = `${getBaseUrl()}/api/v1/planes/${planId}/pdf`;
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Error al descargar PDF');
    }
    const blob = await response.blob();
    const filename = response.headers.get('content-disposition')?.match(/filename="(.+)"/)?.[1] || `plan_nutricional_${planId.slice(0, 8)}.pdf`;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  },

  /**
   * Genera un código temporal de emparejamiento para el ESP32.
   * @param {string} token JWT del estudiante/docente autenticado
   * @param {string} [studentId] Solo docentes: username del estudiante para quien se genera
   */
  createPairingCode: async (token, studentId) => {
    const url = `${getBaseUrl()}/api/v1/devices/pairing-code`;
    const body = studentId ? { student_id: studentId } : {};
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al generar el código de emparejamiento');
    }
    return data;
  },

  /**
   * Lista los usuarios del sistema (solo Docentes). Usado para el dropdown de estudiantes.
   * @param {string} token JWT
   */
  listUsers: async (token) => {
    const url = `${getBaseUrl()}/api/v1/admin/users`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al listar usuarios');
    }
    return data;
  },

  /**
   * Obtiene el historial de lecturas cardíacas de un dispositivo.
   * @param {string} token JWT
   * @param {string} deviceId ID del dispositivo
   * @param {number} limit Cantidad máxima de lecturas
   */
  getHeartReadings: async (token, deviceId, limit = 50) => {
    const url = `${getBaseUrl()}/api/v1/devices/readings/${deviceId}?limit=${limit}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener lecturas');
    }
    return data;
  },

  /**
   * Lista los dispositivos del estudiante autenticado.
   * @param {string} token JWT
   */
  getMyDevices: async (token) => {
    const url = `${getBaseUrl()}/api/v1/devices/my-devices`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener dispositivos');
    }
    return data;
  },

  /**
   * Lista todos los dispositivos registrados (solo Docentes).
   * @param {string} token JWT
   */
  listDevices: async (token) => {
    const url = `${getBaseUrl()}/api/v1/devices`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al listar dispositivos');
    }
    return data;
  },

  // ====== CATÁLOGO DE ALIMENTOS (RF9, RF12) ======

  getAlimentos: async (token, buscar = '', categoria = '', limite = 50, offset = 0) => {
    const params = new URLSearchParams();
    if (buscar) params.append('buscar', buscar);
    if (categoria) params.append('categoria', categoria);
    params.append('limite', limite);
    params.append('offset', offset);
    const url = `${getBaseUrl()}/api/v1/alimentos?${params}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al obtener alimentos');
    return data;
  },

  getCategoriasAlimentos: async (token) => {
    const url = `${getBaseUrl()}/api/v1/alimentos/categorias`;
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al obtener categorías');
    return data;
  },

  getAlimentoById: async (token, alimentoId) => {
    const url = `${getBaseUrl()}/api/v1/alimentos/${alimentoId}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al obtener alimento');
    return data;
  },

  // ====== PLANES ALIMENTICIOS (RF9, RF10, RNF2) ======

  crearPlanAlimenticio: async (token, planData) => {
    const url = `${getBaseUrl()}/api/v1/planes`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(planData),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al crear plan');
    return data;
  },

  getPlan: async (token, planId) => {
    const url = `${getBaseUrl()}/api/v1/planes/${planId}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al obtener plan');
    return data;
  },

  getPlanesPaciente: async (token, pacienteId) => {
    const url = `${getBaseUrl()}/api/v1/planes/paciente/${pacienteId}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al obtener planes del paciente');
    return data;
  },

  calcularPorcion: async (token, alimentoId, cantidadGramos) => {
    const url = `${getBaseUrl()}/api/v1/planes/calcular-porcion?alimento_id=${alimentoId}&cantidad_gramos=${cantidadGramos}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al calcular porción');
    return data;
  },

  // ====== SUGERENCIA DE PLAN (RF5, RF11, RF7) ======

  generarSugerencia: async (token, datosPaciente) => {
    const url = `${getBaseUrl()}/api/v1/sugerencia/generar`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(datosPaciente),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al generar sugerencia');
    return data;
  },

  aceptarSugerencia: async (token, sugerenciaId) => {
    const url = `${getBaseUrl()}/api/v1/sugerencia/${sugerenciaId}/aceptar`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al aceptar sugerencia');
    return data;
  },

  getHistorialSugerencias: async (token, pacienteId) => {
    const url = `${getBaseUrl()}/api/v1/sugerencia/historial/${pacienteId}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al obtener historial');
    return data;
  },

  // ====== AUDITORÍA AMPLIADA (RNF9) ======

  getAuditEvents: async (token, filtros = {}) => {
    const params = new URLSearchParams();
    if (filtros.event_type) params.append('event_type', filtros.event_type);
    if (filtros.usuario) params.append('usuario', filtros.usuario);
    if (filtros.fecha_desde) params.append('fecha_desde', filtros.fecha_desde);
    if (filtros.fecha_hasta) params.append('fecha_hasta', filtros.fecha_hasta);
    if (filtros.limite) params.append('limite', filtros.limite);
    const url = `${getBaseUrl()}/api/v1/admin/audit/all?${params}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al obtener eventos de auditoría');
    return data;
  },

  // ====== ADMIN: CREAR USUARIO (Seguridad) ======

  adminCreateUser: async (token, userData) => {
    const url = `${getBaseUrl()}/api/v1/admin/create-user`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(userData),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al crear usuario');
    return data;
  },
};
