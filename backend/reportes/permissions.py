"""
Permisos personalizados para la API de UrbanAlert
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


