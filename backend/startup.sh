#!/bin/bash
set -e

# Script de inicio para Azure App Service
# Este script se ejecuta después de que Oryx instala las dependencias

echo "🚀 Iniciando EcoAlerta Backend en Azure..."

# Instalar GDAL y dependencias del sistema (requerido para Django GIS)
echo "📦 Instalando dependencias del sistema (GDAL, GEOS, Proj)..."
if apt-get update -qq && apt-get install -y -qq \
    libgdal-dev \
    gdal-bin \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    python3-gdal \
    > /dev/null 2>&1; then
    echo "✅ Dependencias del sistema instaladas"
else
    echo "⚠️ No se pudieron instalar dependencias del sistema (puede requerir permisos root)"
    echo "Intentando continuar..."
fi

# Cambiar al directorio de la aplicación
cd /home/site/wwwroot

# Activar el entorno virtual si existe (creado por Oryx)
if [ -d "antenv" ]; then
    source antenv/bin/activate
    echo "✅ Entorno virtual activado"
else
    echo "⚠️ No se encontró entorno virtual, usando Python del sistema"
fi

# Configurar variables de entorno para GDAL/GEOS
export GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
export GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
python manage.py migrate --noinput

# Recopilar archivos estáticos
echo "📦 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Iniciar Gunicorn (debe quedarse en ejecución)
echo "✅ Iniciando servidor Gunicorn..."
exec gunicorn ecoalerta.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120 --access-logfile - --error-logfile -

