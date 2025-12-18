// Configuración de la API
// En producción, usar la URL del backend en Azure
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
const PRODUCTION_API_URL = 'https://ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net';
const DEVELOPMENT_API_URL = 'http://localhost:8000';

// Validar y limpiar la URL de la variable de entorno si existe
let envApiUrl = import.meta.env.VITE_API_URL;
if (envApiUrl) {
  // Limpiar cualquier carácter inválido y asegurar que termine sin barra
  envApiUrl = envApiUrl.trim().replace(/[=]+/g, '-').replace(/\/+$/, '');
}

export const API_URL = envApiUrl || (isProduction ? PRODUCTION_API_URL : DEVELOPMENT_API_URL);

// Endpoints completos (para compatibilidad con código existente)
export const API_ENDPOINTS = {
  LOGIN: `${API_URL}/api/auth/login/`,
  REPORTES: `${API_URL}/api/reportes/`,
  CATEGORIAS: `${API_URL}/api/categorias/`,
  ESTADISTICAS: `${API_URL}/api/reportes/estadisticas/`,
  HEATMAP: `${API_URL}/api/analytics/heatmap/`,
  PREDICCIONES: `${API_URL}/api/reportes/predicciones/`,
};

// Rutas relativas para usar con apiClient
export const API_ROUTES = {
  LOGIN: '/api/auth/login/',
  REPORTES: '/api/reportes/',
  CATEGORIAS: '/api/categorias/',
  ESTADISTICAS: '/api/reportes/estadisticas/',
  HEATMAP: '/api/analytics/heatmap/',
  PREDICCIONES: '/api/reportes/predicciones/',
  HEALTH: '/api/health/',
};

// Deployment trigger

// Trigger deployment
