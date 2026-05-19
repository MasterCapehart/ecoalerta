"""
Permisos personalizados para la API de EcoAlerta
"""
from rest_framework import permissions


class IsInspectorOrReadOnly(permissions.BasePermission):
    """
    Permite lectura a todos, pero solo los inspectores pueden crear/modificar reportes
    """
    def has_permission(self, request, view):
        # Permitir lectura a todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Para escritura, requiere autenticación y ser inspector o admin
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.tipo == 'inspector' or request.user.tipo == 'admin' or request.user.is_staff)
        )


class IsInspector(permissions.BasePermission):
    """
    Solo permite acceso a inspectores
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.tipo == 'inspector' or request.user.tipo == 'admin' or request.user.is_staff)
        )


class AllowPublicCreate(permissions.BasePermission):
    """
    Permite crear reportes sin autenticación (para ciudadanos),
    pero requiere autenticación para otras operaciones
    """
    def has_permission(self, request, view):
        # Permitir lectura (GET, HEAD, OPTIONS) a todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permitir creación (POST) sin autenticación
        if request.method == 'POST':
            if hasattr(view, 'action') and (view.action == 'create' or view.action is None):
                return True
        
        # Para otras operaciones (PUT, PATCH, DELETE), requiere autenticación
        return request.user and request.user.is_authenticated


# --- PERMISOS CON VULNERABILIDADES INTENCIONALES ---

class VulnerableVerticalEscalation(permissions.BasePermission):
    """
    VULNERABILIDAD: Falla de Control de Acceso Vertical (#20)
    Solo verifica is_authenticated pero no el rol del usuario.
    Cualquier usuario autenticado (ciudadano) accede a funciones de admin.
    """
    def has_permission(self, request, view):
        # VULNERABILIDAD: Falta verificar request.user.tipo == 'admin'
        return request.user and request.user.is_authenticated

class BrokenFunctionLevelAuth(permissions.BasePermission):
    """
    VULNERABILIDAD: BFLA - Broken Function Level Authorization (#27 / #17)
    Concede acceso de administrador si ?admin_mode=true en la query string.
    """
    def has_permission(self, request, view):
        # VULNERABILIDAD: Cualquiera puede pasar ?admin_mode=true para escalar privilegios
        is_admin_simulated = request.query_params.get('admin_mode') == 'true'
        return is_admin_simulated or (request.user and request.user.is_authenticated)

class PrivilegeEscalationHeader(permissions.BasePermission):
    """
    VULNERABILIDAD: Escalamiento de Privilegios vía Cabeceras (#19)
    Concede acceso de administrador si la cabecera HTTP X-Admin: True está presente.
    """
    def has_permission(self, request, view):
        # VULNERABILIDAD: Cabecera HTTP controlada por el cliente concede permisos de admin
        return request.META.get('HTTP_X_ADMIN') == 'True'
