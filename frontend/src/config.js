// Configuración de la API
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  LOGIN: `${API_URL}/api/auth/login/`,
  REPORTES: `${API_URL}/api/reportes/`,
  CATEGORIAS: `${API_URL}/api/categorias/`,
  ESTADISTICAS: `${API_URL}/api/reportes/estadisticas/`,
};

