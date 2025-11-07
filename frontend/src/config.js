// Configuración de la API
// En producción, usar la URL del backend en Azure
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
const PRODUCTION_API_URL = 'https://ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net';
const DEVELOPMENT_API_URL = 'http://localhost:8000';

export const API_URL = import.meta.env.VITE_API_URL || (isProduction ? PRODUCTION_API_URL : DEVELOPMENT_API_URL);

export const API_ENDPOINTS = {
  LOGIN: `${API_URL}/api/auth/login/`,
  REPORTES: `${API_URL}/api/reportes/`,
  CATEGORIAS: `${API_URL}/api/categorias/`,
  ESTADISTICAS: `${API_URL}/api/reportes/estadisticas/`,
  HEATMAP: `${API_URL}/api/analytics/heatmap/`,
};

