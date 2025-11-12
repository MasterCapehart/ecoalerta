#!/bin/bash
# NO usar set -e para que el script continúe incluso si hay errores
# Script de inicio definitivo para Azure App Service
echo "=== INICIANDO ECOALERTA BACKEND ==="

# Cambiar al directorio de la aplicación
cd /home/site/wwwroot || exit 1
echo "Directorio: $(pwd)"

# NO instalar GDAL/GEOS - no se usan PostGIS
# Eliminado para evitar errores

# Crear o activar entorno virtual
if [ ! -d "antenv" ]; then
    echo "Creando entorno virtual..."
    python3.11 -m venv antenv
    source antenv/bin/activate
    echo "Actualizando pip..."
    pip install --upgrade pip --quiet || true
    echo "Instalando dependencias..."
    pip install -r requirements.txt --quiet || echo "⚠️ Error instalando dependencias"
else
    echo "Activando entorno virtual existente..."
    source antenv/bin/activate || exit 1
fi

echo "Python: $(which python)"
echo "Gunicorn: $(which gunicorn)"

# NO configurar GDAL/GEOS - no se usan

# Ejecutar migraciones (con manejo de errores)
echo "Ejecutando migraciones..."
python manage.py migrate --noinput 2>&1 || {
    echo "⚠️ Error en migraciones, intentando continuar..."
    # Si las migraciones fallan, al menos intentar iniciar el servidor
}

# Recopilar archivos estáticos (con manejo de errores)
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput 2>&1 || {
    echo "⚠️ Error en collectstatic, continuando sin archivos estáticos..."
}

# Iniciar Gunicorn (DEBE quedarse corriendo)
echo "=== INICIANDO GUNICORN ==="
exec gunicorn ecoalerta.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    --preload
