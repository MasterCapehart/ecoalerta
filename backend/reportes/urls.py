from django.urls import path, include
from rest_framework.routers import DefaultRouter
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
    # --- Funciones de laboratorio de seguridad ---
    vulnerable_user_detail,
    insecure_debug_login,
    vulnerable_file_read,
    insecure_deserialization,
    vulnerable_ssrf,
    logic_flaw_race_condition,
    vulnerable_xss,
    vulnerable_redirect,
    vulnerable_mass_assignment,
    vulnerable_idor_delete,
    vulnerable_vertical_privilege_escalation,
    vulnerable_stack_trace_leak,
    cmd_os,
    ssti,
    jwt_weak,
    jwt_none,
    pred_reset,
    sess_fix,
    brute_login,
    bola_view,
    bfla_admin,
    force_browse,
    mass_prof,
    priv_head,
)
from .utils import (
    insecure_crypto,
    vulnerable_exif_exposure,
)
from .search_service import (
    vulnerable_search,
    sqli2
)

router = DefaultRouter()
router.register(r'reportes', ReporteViewSet, basename='reportes')
router.register(r'categorias', CategoriaResiduoViewSet, basename='categorias')

urlpatterns = [
    # --- Laboratorio de Seguridad ---
    # Vulnerabilidades activas: 31 (21 requeridas + 10 adicionales)

    # #8 SQLi + #12 Sensitive Data Logging
    path('lab/search/', vulnerable_search, name='lab-search'),
    # #15 IDOR con exposición de credenciales + #21 Password Hash Exposure
    path('lab/users/<int:user_id>/', vulnerable_user_detail, name='lab-user-detail'),
    # #12 Registro inseguro de credenciales
    path('lab/debug-login/', insecure_debug_login, name='lab-debug-login'),
    # Adicional C - Path Traversal / LFI
    path('lab/files/', vulnerable_file_read, name='lab-file-read'),
    # #10 Deserialización insegura Pickle RCE
    path('lab/deserialize/', insecure_deserialization, name='lab-deserialize'),
    # Adicional E - SSRF
    path('lab/proxy/', vulnerable_ssrf, name='lab-ssrf'),
    # Adicional J - Race Condition
    path('lab/points-redeem/', logic_flaw_race_condition, name='lab-race-condition'),
    # #3 Criptografía insegura / SECRET_KEY hardcoded
    path('lab/crypto/', insecure_crypto, name='lab-crypto'),
    # Adicional A - XSS Reflejado
    path('lab/xss/', vulnerable_xss, name='lab-xss'),
    # Adicional B - Open Redirect
    path('lab/redirect/', vulnerable_redirect, name='lab-redirect'),
    # #18 Mass Assignment
    path('lab/users/<int:user_id>/update/', vulnerable_mass_assignment, name='lab-mass-assignment'),
    # #16 IDOR Delete
    path('lab/reportes/<int:report_id>/delete/', vulnerable_idor_delete, name='lab-idor-delete'),
    # #5 Fuga de PII via EXIF
    path('lab/images/exif/', vulnerable_exif_exposure, name='lab-exif'),
    # #20 Escalada vertical de privilegios
    path('lab/admin/sensitive/', vulnerable_vertical_privilege_escalation, name='lab-vertical-escalation'),
    # Adicional D - Stack Trace Leak
    path('lab/debug/trace/', vulnerable_stack_trace_leak, name='lab-trace-leak'),
    # #9 OS Command Injection
    path('lab/massive/cmd_os/', cmd_os, name='lab-cmd_os'),
    # #11 SSTI
    path('lab/massive/ssti/', ssti, name='lab-ssti'),
    # #7 SQL Ineficiente / SQLi secundaria
    path('lab/massive/sqli2/', sqli2, name='lab-sqli2'),
    # #13 JWT Secret débil hardcoded
    path('lab/massive/jwt_weak/', jwt_weak, name='lab-jwt_weak'),
    # Adicional G - JWT None Algorithm
    path('lab/massive/jwt_none/', jwt_none, name='lab-jwt_none'),
    # #14 Token de reset predecible
    path('lab/massive/pred_reset/', pred_reset, name='lab-pred_reset'),
    # Adicional I - Session Fixation
    path('lab/massive/sess_fix/', sess_fix, name='lab-sess_fix'),
    # #1 EA-SEC-01 Fuerza Bruta / Sin rate limiting
    path('lab/massive/brute_login/', brute_login, name='lab-brute_login'),
    # #4 IDOR Rutas de Inspectores (BOLA View)
    path('lab/massive/bola_view/', bola_view, name='lab-bola_view'),
    # #27 BFLA Admin Bypass
    path('lab/massive/bfla_admin/', bfla_admin, name='lab-bfla_admin'),
    # #17 Forced Browsing
    path('lab/massive/force_browse/', force_browse, name='lab-force_browse'),
    # #6 Mass Assignment en perfiles
    path('lab/massive/mass_prof/', mass_prof, name='lab-mass_prof'),
    # #19 Privilege Escalation via Header
    path('lab/massive/priv_head/', priv_head, name='lab-priv_head'),

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
    
    # Router URLs
    path('', include(router.urls)),
]
