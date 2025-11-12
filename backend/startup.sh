#!/bin/bash
set -e

# Script de inicio definitivo para Azure App Service
echo "=== INICIANDO ECOALERTA BACKEND ==="

# Cambiar al directorio de la aplicación
cd /home/site/wwwroot
echo "Directorio: $(pwd)"

# Crear o activar entorno virtual
if [ ! -d "antenv" ]; then
    echo "Creando entorno virtual..."
    python3.11 -m venv antenv
    source antenv/bin/activate
    echo "Actualizando pip..."
    pip install --upgrade pip --quiet
    echo "Instalando dependencias..."
    pip install -r requirements.txt --quiet
else
    echo "Activando entorno virtual existente..."
    source antenv/bin/activate
fi

echo "Python: $(which python)"
echo "Gunicorn: $(which gunicorn)"

# Ejecutar migraciones (con manejo de errores para GDAL)
echo "Ejecutando migraciones..."
python manage.py migrate --noinput 2>&1 || echo "⚠️ Error en migraciones (posiblemente GDAL), continuando..."

# Recopilar archivos estáticos (con manejo de errores para GDAL)
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput 2>&1 || echo "⚠️ Error en collectstatic (posiblemente GDAL), continuando..."

# Iniciar Gunicorn (DEBE quedarse corriendo)
echo "=== INICIANDO GUNICORN ==="
exec gunicorn ecoalerta.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output
