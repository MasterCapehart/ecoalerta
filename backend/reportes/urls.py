from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReporteViewSet, CategoriaResiduoViewSet, login_view, heatmap_view, db_status_view

router = DefaultRouter()
router.register(r'reportes', ReporteViewSet, basename='reportes')
router.register(r'categorias', CategoriaResiduoViewSet, basename='categorias')

urlpatterns = [
    path('auth/login/', login_view, name='login'),
    path('analytics/heatmap/', heatmap_view, name='heatmap'),
    path('diagnostic/db-status/', db_status_view, name='db_status'),
    path('', include(router.urls)),
]

