#!/bin/bash
# Script de inicio para Azure App Service
# NO usar set -e para manejar errores graciosamente

echo "=== INICIANDO ECOALERTA BACKEND ==="
echo "Timestamp: $(date)"

# Cambiar al directorio de la aplicación
cd /home/site/wwwroot || {
    echo "❌ ERROR: No se pudo cambiar al directorio /home/site/wwwroot"
    exit 1
}
echo "Directorio: $(pwd)"
echo "Contenido: $(ls -la | head -10)"

# Instalar libpq-dev si no está disponible (para PostgreSQL)
echo "Verificando libpq-dev..."
if ! dpkg -l | grep -q "^ii.*libpq-dev"; then
    echo "Instalando libpq-dev..."
    apt-get update -qq 2>&1 | head -5
    apt-get install -y -qq libpq-dev 2>&1 | head -5 || echo "⚠️ No se pudo instalar libpq-dev (continuando)"
fi

# Crear o activar entorno virtual
if [ ! -d "antenv" ]; then
    echo "Creando entorno virtual..."
    python3.11 -m venv antenv || {
        echo "❌ ERROR: No se pudo crear entorno virtual"
        exit 1
    }
    source antenv/bin/activate
    pip install --upgrade pip --quiet 2>&1 | tail -3
    echo "Instalando dependencias..."
    pip install -r requirements.txt 2>&1 | tail -10 || {
        echo "⚠️ ERROR instalando dependencias"
        exit 1
    }
else
    echo "Activando entorno virtual existente..."
    source antenv/bin/activate || {
        echo "❌ ERROR: No se pudo activar entorno virtual"
        exit 1
    }
fi

echo "Python: $(which python)"
echo "Python version: $(python --version 2>&1)"

# Verificar que Django está instalado
echo "Verificando Django..."
python -c "import django; print(f'Django {django.get_version()}')" 2>&1 || {
    echo "❌ ERROR: Django no está instalado"
    pip list | grep -i django
    exit 1
}

# Verificar que la aplicación puede cargar
echo "Verificando que Django puede cargar settings..."
python -c "import django; django.setup(); from django.conf import settings; print(f'Apps instaladas: {len(settings.INSTALLED_APPS)}')" 2>&1 || {
    echo "⚠️ ERROR: Django no puede cargar settings"
    python manage.py check 2>&1 | head -20
    # Continuar de todas formas
}

# Ejecutar migraciones (continuar aunque falle)
echo "Ejecutando migraciones..."
python manage.py migrate --noinput 2>&1 | tail -10 || {
    echo "⚠️ ADVERTENCIA: Error en migraciones (continuando)"
}

# Recopilar archivos estáticos (continuar aunque falle)
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput 2>&1 | tail -10 || {
    echo "⚠️ ADVERTENCIA: Error en collectstatic (continuando)"
}

# Verificar configuración básica (no --deploy porque requiere más config)
echo "Verificando configuración de Django..."
python manage.py check 2>&1 | tail -10 || {
    echo "⚠️ ADVERTENCIA: Problemas en verificación (continuando)"
}

# Iniciar Gunicorn (DEBE funcionar)
echo "=== INICIANDO GUNICORN ==="
echo "Comando: gunicorn ecoalerta.wsgi:application --bind 0.0.0.0:8000 --workers 2"
exec gunicorn ecoalerta.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug \
    --capture-output \
    --enable-stdio-inheritance
