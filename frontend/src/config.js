// Configuración de la API
// En producción, usar la URL del backend en Azure
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
const PRODUCTION_API_URL = 'https://urbanalert-backend.azurewebsites.net';
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
  REPORTES_BULK_UPDATE: '/api/reportes/bulk_update/',
  CATEGORIAS: '/api/categorias/',
  ESTADISTICAS: '/api/reportes/estadisticas/',
  HEATMAP: '/api/analytics/heatmap/',
  PREDICCIONES: '/api/reportes/predicciones/',
  HEALTH: '/api/health/',
  // Nuevas rutas
  ASIGNACION_AUTOMATICA: '/api/asignacion/automatica/',
  RUTA_OPTIMIZADA: '/api/asignacion/ruta/',
  HISTORIAL: '/api/reportes/',
  TAGS: '/api/tags/',
  ESTADISTICAS_AVANZADAS: '/api/analytics/avanzadas/',
  ANALYTICS_EJECUTIVO: '/api/analytics/ejecutivo/',
  EXPORTAR_PDF: '/api/analytics/exportar-pdf/',
  EXPORTAR_EXCEL: '/api/analytics/exportar-excel/',
  ACTUALIZAR_PRIORIDADES: '/api/prioridades/actualizar/',
  ESTADISTICAS_INSPECTOR: '/api/inspectores/estadisticas/',
  COMENTARIOS_PUBLICOS: '/api/reportes/',
  SEGUIMIENTO_PUBLICO: '/api/seguimiento/',
  // Nuevas rutas para las 5 funcionalidades
  ACTUALIZAR_UBICACION: '/api/inspectores/ubicacion/',
  NOTIFICACIONES: '/api/notificaciones/',
  MARCAR_NOTIFICACION_LEIDA: '/api/notificaciones/',
  BUSQUEDAS_GUARDADAS: '/api/busquedas-guardadas/',
  ADMIN_USUARIOS: '/api/admin/usuarios/',
  ADMIN_ESTADISTICAS: '/api/admin/estadisticas/',
  // Validación de reportes
  VALIDAR_REPORTE: '/api/reportes/',
  // Moderación de comentarios
  COMENTARIOS_PENDIENTES: '/api/comentarios/pendientes/',
  MODERAR_COMENTARIO: '/api/comentarios/',
  // SLA
  SLA_RIESGO: '/api/sla/riesgo/',
  SLA_EXCEDIDOS: '/api/sla/excedidos/',
  SLA_ESTADISTICAS: '/api/sla/estadisticas/',
  CALCULAR_SLA: '/api/reportes/',
  EXPORTAR_IA_CSV: '/api/analytics/exportar-datos-ia/',
  ANALIZAR_IA_AVANZADA: (id) => `/api/reportes/${id}/analizar-ia-avanzada/`,
};

// Deployment trigger - $(date +%Y%m%d-%H%M%S)

// Trigger deployment
