#!/bin/bash

# Script de inicio para Azure App Service
# Este script se ejecuta después de que Oryx instala las dependencias

echo "🚀 Iniciando EcoAlerta Backend en Azure..."

# Cambiar al directorio de la aplicación
cd /home/site/wwwroot

# Activar el entorno virtual si existe (creado por Oryx)
if [ -d "antenv" ]; then
    source antenv/bin/activate
    echo "✅ Entorno virtual activado"
else
    echo "⚠️ No se encontró entorno virtual, usando Python del sistema"
fi

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
python manage.py migrate --noinput

# Recopilar archivos estáticos
echo "📦 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Iniciar Gunicorn (debe quedarse en ejecución)
echo "✅ Iniciando servidor Gunicorn..."
exec gunicorn ecoalerta.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120 --access-logfile - --error-logfile -

