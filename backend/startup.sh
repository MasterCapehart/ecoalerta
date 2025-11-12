#!/bin/bash
# Script de inicio para Azure App Service
set -e

echo "=== INICIANDO ECOALERTA BACKEND ==="

# Cambiar al directorio de la aplicación
cd /home/site/wwwroot
echo "Directorio: $(pwd)"

# Instalar libpq-dev si no está disponible (para PostgreSQL)
if ! dpkg -l | grep -q libpq-dev; then
    echo "Instalando libpq-dev..."
    apt-get update -qq && apt-get install -y -qq libpq-dev > /dev/null 2>&1 || echo "⚠️ No se pudo instalar libpq-dev"
fi

# Crear o activar entorno virtual
if [ ! -d "antenv" ]; then
    echo "Creando entorno virtual..."
    python3.11 -m venv antenv
    source antenv/bin/activate
    pip install --upgrade pip --quiet
    echo "Instalando dependencias..."
    pip install -r requirements.txt --quiet
else
    echo "Activando entorno virtual existente..."
    source antenv/bin/activate
fi

echo "Python: $(which python)"
echo "Python version: $(python --version)"

# Verificar que Django está instalado
python -c "import django; print(f'Django {django.get_version()}')" || {
    echo "❌ ERROR: Django no está instalado"
    exit 1
}

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py migrate --noinput || {
    echo "⚠️ ERROR en migraciones"
    exit 1
}

# Recopilar archivos estáticos
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --clear || {
    echo "⚠️ ERROR en collectstatic"
    exit 1
}

# Verificar que la aplicación puede iniciar
echo "Verificando configuración de Django..."
python manage.py check --deploy || {
    echo "⚠️ ERROR en verificación de Django"
    exit 1
}

# Iniciar Gunicorn
echo "=== INICIANDO GUNICORN ==="
exec gunicorn ecoalerta.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output
