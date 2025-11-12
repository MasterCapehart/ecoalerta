#!/bin/bash
# NO usar set -e para que el script continúe incluso si hay errores
# Script de inicio definitivo para Azure App Service
echo "=== INICIANDO ECOALERTA BACKEND ==="

# Cambiar al directorio de la aplicación
cd /home/site/wwwroot || exit 1
echo "Directorio: $(pwd)"

# Intentar instalar GDAL/GEOS si no están disponibles (puede fallar si no hay permisos)
echo "Verificando GDAL/GEOS..."
if ! command -v gdalinfo &> /dev/null; then
    echo "⚠️ GDAL no encontrado, intentando instalar..."
    apt-get update -qq && apt-get install -y -qq \
        libpq-dev \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        python3-gdal \
        > /dev/null 2>&1 || echo "⚠️ No se pudieron instalar dependencias del sistema (continúa sin ellas)"
fi

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

# Configurar variables de entorno para GDAL si existen
if [ -f "/usr/lib/libgdal.so" ] || [ -f "/usr/lib/x86_64-linux-gnu/libgdal.so" ]; then
    export GDAL_LIBRARY_PATH=${GDAL_LIBRARY_PATH:-/usr/lib/x86_64-linux-gnu/libgdal.so}
    echo "✅ GDAL_LIBRARY_PATH configurado: $GDAL_LIBRARY_PATH"
fi
if [ -f "/usr/lib/libgeos_c.so" ] || [ -f "/usr/lib/x86_64-linux-gnu/libgeos_c.so" ]; then
    export GEOS_LIBRARY_PATH=${GEOS_LIBRARY_PATH:-/usr/lib/x86_64-linux-gnu/libgeos_c.so}
    echo "✅ GEOS_LIBRARY_PATH configurado: $GEOS_LIBRARY_PATH"
fi

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
