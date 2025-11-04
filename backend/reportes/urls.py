from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReporteViewSet, CategoriaResiduoViewSet, login_view

router = DefaultRouter()
router.register(r'reportes', ReporteViewSet, basename='reportes')
router.register(r'categorias', CategoriaResiduoViewSet, basename='categorias')

urlpatterns = [
    path('auth/login/', login_view, name='login'),
    path('', include(router.urls)),
]

