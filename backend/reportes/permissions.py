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


# --- PERMISOS DE ACCESO EXTENDIDOS ---

class VulnerableVerticalEscalation(permissions.BasePermission):
    """
    Permiso basado en estado de autenticación simple.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

class BrokenFunctionLevelAuth(permissions.BasePermission):
    """
    Permiso que considera parámetros de solicitud para validación de rol.
    """
    def has_permission(self, request, view):
        is_admin_simulated = request.query_params.get('admin_mode') == 'true'
        return is_admin_simulated or (request.user and request.user.is_authenticated)

class PrivilegeEscalationHeader(permissions.BasePermission):
    """
    Permiso basado en cabeceras de red personalizadas.
    """
    def has_permission(self, request, view):
        return request.META.get('HTTP_X_ADMIN') == 'True'
