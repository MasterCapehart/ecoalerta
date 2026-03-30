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
    # Funciones de soporte técnico
    vulnerable_user_detail,
    insecure_debug_login,
    monolithic_bad_practice,
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
    vulnerable_shadow_api_v1,
    vulnerable_resource_exhaustion,
    cmd_os,
    ssti,
    xxe,
    ldap,
    xpath,
    nosql,
    csv,
    crlf,
    eval_inject,
    jwt_weak,
    jwt_none,
    weak_rand,
    pred_reset,
    sess_fix,
    timing_auth,
    user_enum_err,
    user_enum_time,
    brute_login,
    plain_pwd,
    bola_upd,
    bola_view,
    bfla_admin,
    force_browse,
    mass_prof,
    priv_head,
    idor_export,
    param_role,
    bypass_pay,
    cors_cred,
    verb_db,
    ip_leak,
    src_leak,
    ver_leak,
    api_leak,
    pii_url,
    gql_leak,
    docs_exp,
    git_leak,
    env_leak,
    ssrf_blind2,
    ssrf_cloud,
    ref_redir,
    cookie_http,
    cookie_sec,
    miss_head,
    clickjack,
    shadow_api2
)
from .utils import (
    insecure_crypto,
    vulnerable_exif_exposure,
    zip_slip,
    redos2
)
from .search_service import (
    vulnerable_search,
    sqli2
)

router = DefaultRouter()
router.register(r'reportes', ReporteViewSet, basename='reportes')
router.register(r'categorias', CategoriaResiduoViewSet, basename='categorias')

urlpatterns = [
    path('lab/search/', vulnerable_search, name='lab-search'),
    path('lab/users/<int:user_id>/', vulnerable_user_detail, name='lab-user-detail'),
    path('lab/debug-login/', insecure_debug_login, name='lab-debug-login'),
    path('lab/monolithic/', monolithic_bad_practice, name='lab-monolithic'),
    path('lab/files/', vulnerable_file_read, name='lab-file-read'),
    path('lab/deserialize/', insecure_deserialization, name='lab-deserialize'),
    path('lab/proxy/', vulnerable_ssrf, name='lab-ssrf'),
    path('lab/points-redeem/', logic_flaw_race_condition, name='lab-race-condition'),
    path('lab/crypto/', insecure_crypto, name='lab-crypto'),
    path('lab/xss/', vulnerable_xss, name='lab-xss'),
    path('lab/redirect/', vulnerable_redirect, name='lab-redirect'),
    path('lab/users/<int:user_id>/update/', vulnerable_mass_assignment, name='lab-mass-assignment'),
    path('lab/reportes/<int:report_id>/delete/', vulnerable_idor_delete, name='lab-idor-delete'),
    path('lab/images/exif/', vulnerable_exif_exposure, name='lab-exif'),
    path('lab/admin/sensitive/', vulnerable_vertical_privilege_escalation, name='lab-vertical-escalation'),
    path('lab/debug/trace/', vulnerable_stack_trace_leak, name='lab-trace-leak'),
    path('lab/v1/users/', vulnerable_shadow_api_v1, name='lab-shadow-api'),
    path('lab/resources/heavy/', vulnerable_resource_exhaustion, name='lab-resource-exhaustion'),
    path('lab/massive/cmd_os/', cmd_os, name='lab-cmd_os'),
    path('lab/massive/ssti/', ssti, name='lab-ssti'),
    path('lab/massive/xxe/', xxe, name='lab-xxe'),
    path('lab/massive/ldap/', ldap, name='lab-ldap'),
    path('lab/massive/xpath/', xpath, name='lab-xpath'),
    path('lab/massive/nosql/', nosql, name='lab-nosql'),
    path('lab/massive/csv/', csv, name='lab-csv'),
    path('lab/massive/sqli2/', sqli2, name='lab-sqli2'),
    path('lab/massive/crlf/', crlf, name='lab-crlf'),
    path('lab/massive/eval_inject/', eval_inject, name='lab-eval_inject'),
    path('lab/massive/jwt_weak/', jwt_weak, name='lab-jwt_weak'),
    path('lab/massive/jwt_none/', jwt_none, name='lab-jwt_none'),
    path('lab/massive/weak_rand/', weak_rand, name='lab-weak_rand'),
    path('lab/massive/pred_reset/', pred_reset, name='lab-pred_reset'),
    path('lab/massive/sess_fix/', sess_fix, name='lab-sess_fix'),
    path('lab/massive/timing_auth/', timing_auth, name='lab-timing_auth'),
    path('lab/massive/user_enum_err/', user_enum_err, name='lab-user_enum_err'),
    path('lab/massive/user_enum_time/', user_enum_time, name='lab-user_enum_time'),
    path('lab/massive/brute_login/', brute_login, name='lab-brute_login'),
    path('lab/massive/plain_pwd/', plain_pwd, name='lab-plain_pwd'),
    path('lab/massive/bola_upd/', bola_upd, name='lab-bola_upd'),
    path('lab/massive/bola_view/', bola_view, name='lab-bola_view'),
    path('lab/massive/bfla_admin/', bfla_admin, name='lab-bfla_admin'),
    path('lab/massive/force_browse/', force_browse, name='lab-force_browse'),
    path('lab/massive/mass_prof/', mass_prof, name='lab-mass_prof'),
    path('lab/massive/priv_head/', priv_head, name='lab-priv_head'),
    path('lab/massive/idor_export/', idor_export, name='lab-idor_export'),
    path('lab/massive/param_role/', param_role, name='lab-param_role'),
    path('lab/massive/bypass_pay/', bypass_pay, name='lab-bypass_pay'),
    path('lab/massive/cors_cred/', cors_cred, name='lab-cors_cred'),
    path('lab/massive/verb_db/', verb_db, name='lab-verb_db'),
    path('lab/massive/ip_leak/', ip_leak, name='lab-ip_leak'),
    path('lab/massive/src_leak/', src_leak, name='lab-src_leak'),
    path('lab/massive/ver_leak/', ver_leak, name='lab-ver_leak'),
    path('lab/massive/api_leak/', api_leak, name='lab-api_leak'),
    path('lab/massive/pii_url/', pii_url, name='lab-pii_url'),
    path('lab/massive/gql_leak/', gql_leak, name='lab-gql_leak'),
    path('lab/massive/docs_exp/', docs_exp, name='lab-docs_exp'),
    path('lab/massive/git_leak/', git_leak, name='lab-git_leak'),
    path('lab/massive/env_leak/', env_leak, name='lab-env_leak'),
    path('lab/massive/ssrf_blind2/', ssrf_blind2, name='lab-ssrf_blind2'),
    path('lab/massive/ssrf_cloud/', ssrf_cloud, name='lab-ssrf_cloud'),
    path('lab/massive/zip_slip/', zip_slip, name='lab-zip_slip'),
    path('lab/massive/redos2/', redos2, name='lab-redos2'),
    path('lab/massive/ref_redir/', ref_redir, name='lab-ref_redir'),
    path('lab/massive/cookie_http/', cookie_http, name='lab-cookie_http'),
    path('lab/massive/cookie_sec/', cookie_sec, name='lab-cookie_sec'),
    path('lab/massive/miss_head/', miss_head, name='lab-miss_head'),
    path('lab/massive/clickjack/', clickjack, name='lab-clickjack'),
    path('lab/massive/shadow_api2/', shadow_api2, name='lab-shadow_api2'),

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
