from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .ia_views import (
    ia_clasificar_reporte, ia_detectar_duplicado, ia_generar_respuesta_ciudadano,
    ia_indexar_reportes, ia_buscar_similares
)
from .ia_chat import ia_chat_admin, ia_resumen_departamento
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from .views import (
    ReporteViewSet,
    CategoriaResiduoViewSet,
    login_view,
    heatmap_view,
    health_check,
    refresh_token_view,
    asignar_automaticamente,
    ruta_optimizada,
    historial_reporte,
    tags_list,
    estadisticas_avanzadas,
    exportar_pdf,
    exportar_excel,
    exportar_ia_csv,
    analizar_ia_avanzada,
    comentarios_publicos,
    seguimiento_publico,
    actualizar_prioridades,
    estadisticas_inspector,
    actualizar_ubicacion_inspector,
    obtener_notificaciones,
    marcar_notificacion_leida,
    busquedas_guardadas,
    admin_usuarios,
    admin_estadisticas,
    analytics_ejecutivo,
    validar_reporte,
    comentarios_pendientes_moderacion,
    moderar_comentario,
    reportes_sla_riesgo,
    reportes_sla_excedidos,
    estadisticas_sla,
    calcular_sla_reporte,
    generar_reporte_gerencial,
    completar_tour,
    predicciones_espaciales,
    mis_estadisticas,
    capas_urbanas_list,
    departamentos_list,
    subcategorias_por_capa,
    municipio_config,
)

router = DefaultRouter()
router.register(r'reportes', ReporteViewSet, basename='reportes')
router.register(r'categorias', CategoriaResiduoViewSet, basename='categorias')

urlpatterns = [
    # IA endpoints (Ollama / qwen3:8b + RAG)
    path('ia/clasificar/', ia_clasificar_reporte, name='ia-clasificar'),
    path('ia/duplicado/', ia_detectar_duplicado, name='ia-duplicado'),
    path('ia/respuesta-ciudadano/', ia_generar_respuesta_ciudadano, name='ia-respuesta-ciudadano'),
    path('ia/chat-admin/', ia_chat_admin, name='ia-chat-admin'),
    path('ia/resumen-departamento/', ia_resumen_departamento, name='ia-resumen-departamento'),
    # RAG endpoints
    path('ia/indexar/', ia_indexar_reportes, name='ia-indexar'),
    path('ia/buscar/', ia_buscar_similares, name='ia-buscar'),

    # Capas urbanas, subcategorías y departamentos
    path('capas/', capas_urbanas_list, name='capas-list'),
    path('departamentos/', departamentos_list, name='departamentos-list'),
    path('capas/<int:capa_id>/subcategorias/', subcategorias_por_capa, name='subcategorias-por-capa'),

    # Autenticación
    path('auth/login/', login_view, name='login'),
    path('auth/refresh/', refresh_token_view, name='refresh-token'),
    path('reportes/mis-estadisticas/', mis_estadisticas, name='mis-estadisticas'),

    # Health check
    path('health/', health_check, name='health-check'),

    # Analytics
    path('analytics/heatmap/', heatmap_view, name='heatmap'),
    path('analytics/avanzadas/', estadisticas_avanzadas, name='estadisticas-avanzadas'),
    path('analytics/exportar-pdf/', exportar_pdf, name='exportar-pdf'),
    path('analytics/exportar-excel/', exportar_excel, name='exportar-excel'),
    path('analytics/exportar-datos-ia/', exportar_ia_csv, name='exportar-ia-csv'),
    path('reportes/<int:reporte_id>/analizar-ia-avanzada/', analizar_ia_avanzada, name='analizar_ia_avanzada'),
    path('analytics/gerencial/', generar_reporte_gerencial, name='generar-reporte-gerencial'),
    path('analytics/predicciones-espaciales/', predicciones_espaciales, name='predicciones-espaciales'),

    # Asignación y rutas
    path('asignacion/automatica/', asignar_automaticamente, name='asignar-automatica'),
    path('asignacion/ruta/<int:inspector_id>/', ruta_optimizada, name='ruta-optimizada'),
    path('asignacion/ruta/', ruta_optimizada, name='ruta-optimizada-actual'),

    # Historial
    path('reportes/<int:reporte_id>/historial/', historial_reporte, name='historial-reporte'),

    # Tags
    path('tags/', tags_list, name='tags-list'),

    # Prioridades
    path('prioridades/actualizar/', actualizar_prioridades, name='actualizar-prioridades'),

    # Estadísticas de inspector
    path('inspectores/<int:inspector_id>/estadisticas/', estadisticas_inspector, name='estadisticas-inspector'),
    path('inspectores/estadisticas/', estadisticas_inspector, name='estadisticas-inspector-actual'),

    # Comentarios públicos
    path('reportes/<int:reporte_id>/comentarios/', comentarios_publicos, name='comentarios-publicos'),

    # Seguimiento público
    path('seguimiento/<str:codigo_seguimiento>/', seguimiento_publico, name='seguimiento-publico'),

    # Ubicación inspector
    path('inspectores/ubicacion/', actualizar_ubicacion_inspector, name='actualizar-ubicacion'),

    # Notificaciones
    path('notificaciones/', obtener_notificaciones, name='obtener-notificaciones'),
    path('notificaciones/<int:notificacion_id>/marcar-leida/', marcar_notificacion_leida, name='marcar-notificacion-leida'),

    # Búsquedas guardadas
    path('busquedas-guardadas/', busquedas_guardadas, name='busquedas-guardadas'),
    path('busquedas-guardadas/<int:busqueda_id>/', busquedas_guardadas, name='busqueda-guardada-detail'),

    # Administración
    path('admin/usuarios/completar-tour/', completar_tour, name='completar-tour'),
    path('admin/usuarios/', admin_usuarios, name='admin-usuarios'),
    path('admin/usuarios/<int:usuario_id>/', admin_usuarios, name='admin-usuario-detail'),
    path('admin/estadisticas/', admin_estadisticas, name='admin-estadisticas'),
    path('analytics/ejecutivo/', analytics_ejecutivo, name='analytics-ejecutivo'),

    # Validación de reportes
    path('reportes/<int:reporte_id>/validar/', validar_reporte, name='validar-reporte'),

    # Moderación de comentarios
    path('comentarios/pendientes/', comentarios_pendientes_moderacion, name='comentarios-pendientes'),
    path('comentarios/<int:comentario_id>/moderar/', moderar_comentario, name='moderar-comentario'),

    # SLA
    path('sla/riesgo/', reportes_sla_riesgo, name='sla-riesgo'),
    path('sla/excedidos/', reportes_sla_excedidos, name='sla-excedidos'),
    path('sla/estadisticas/', estadisticas_sla, name='sla-estadisticas'),
    path('reportes/<int:reporte_id>/calcular-sla/', calcular_sla_reporte, name='calcular-sla'),

    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Configuración dinámica del municipio
    path('municipio/', municipio_config, name='municipio-config'),

    # Router URLs
    path('', include(router.urls)),
]
