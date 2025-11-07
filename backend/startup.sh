#!/bin/bash

# Script de inicio para Azure App Service
# Este script se ejecuta automáticamente cuando se inicia la aplicación

echo "🚀 Iniciando EcoAlerta Backend en Azure..."

# Ejecutar migraciones
python manage.py migrate --noinput

# Recopilar archivos estáticos
python manage.py collectstatic --noinput

# Iniciar Gunicorn
echo "✅ Iniciando servidor Gunicorn..."
exec gunicorn ecoalerta.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120 --access-logfile - --error-logfile -

