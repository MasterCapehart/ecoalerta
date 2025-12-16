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

# Instalar dependencias del sistema
echo "Instalando dependencias del sistema..."
apt-get update -qq 2>&1 | head -5

# Instalar libpq-dev para PostgreSQL
if ! dpkg -l | grep -q "^ii.*libpq-dev"; then
    echo "Instalando libpq-dev..."
    apt-get install -y -qq libpq-dev 2>&1 | head -5 || echo "⚠️ No se pudo instalar libpq-dev (continuando)"
fi

# NO instalar GDAL/GEOS - ya no usamos django.contrib.gis
# echo "Instalando GDAL/GEOS (por si acaso Django intenta usarlos)..."
# apt-get install -y -qq gdal-bin libgdal-dev libgeos-dev libproj-dev 2>&1 | head -5 || echo "⚠️ No se pudo instalar GDAL/GEOS (continuando)"

# Crear o activar entorno virtual
# Verificar si el entorno virtual existe Y es válido
if [ ! -d "antenv" ] || [ ! -f "antenv/bin/activate" ]; then
    # Si existe pero está corrupto, eliminarlo
    if [ -d "antenv" ]; then
        echo "⚠️ Entorno virtual corrupto, eliminándolo..."
        rm -rf antenv
    fi
    echo "Creando entorno virtual..."
    python3.11 -m venv antenv || {
        echo "❌ ERROR: No se pudo crear entorno virtual"
        exit 1
    }
    source antenv/bin/activate || {
        echo "❌ ERROR: No se pudo activar entorno virtual recién creado"
        exit 1
    }
    pip install --upgrade pip --quiet 2>&1 | tail -3
    echo "Instalando dependencias..."
    pip install -r requirements.txt 2>&1 | tail -10 || {
        echo "⚠️ ERROR instalando dependencias"
        exit 1
    }
else
    echo "Activando entorno virtual existente..."
    source antenv/bin/activate || {
        echo "⚠️ No se pudo activar entorno virtual existente, recreándolo..."
        rm -rf antenv
        python3.11 -m venv antenv || {
            echo "❌ ERROR: No se pudo recrear entorno virtual"
            exit 1
        }
        source antenv/bin/activate || {
            echo "❌ ERROR: No se pudo activar entorno virtual recién recreado"
            exit 1
        }
        pip install --upgrade pip --quiet 2>&1 | tail -3
        echo "Instalando dependencias en entorno virtual recreado..."
        pip install -r requirements.txt 2>&1 | tail -10 || {
            echo "⚠️ ERROR instalando dependencias"
            exit 1
        }
    }
    # Forzar actualización de dependencias para asegurar que todas estén instaladas
    echo "Actualizando dependencias..."
    pip install --upgrade pip --quiet 2>&1 | tail -3
    pip install -r requirements.txt --upgrade 2>&1 | tail -10 || {
        echo "⚠️ ADVERTENCIA: Error al actualizar dependencias (continuando)"
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

# Verificar que la aplicación puede cargar (con manejo de errores para GDAL)
echo "Verificando que Django puede cargar settings..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecoalerta.settings')
try:
    import django
    django.setup()
    from django.conf import settings
    print(f'✅ Django OK - Apps instaladas: {len(settings.INSTALLED_APPS)}')
except Exception as e:
    print(f'⚠️ ADVERTENCIA al cargar Django: {e}')
    # Continuar de todas formas
" 2>&1 || {
    echo "⚠️ ADVERTENCIA: Problema al verificar Django (continuando)"
}

# Ejecutar migraciones (continuar aunque falle)
echo "Ejecutando migraciones..."
python manage.py migrate --noinput 2>&1 | tail -10 || {
    echo "⚠️ ADVERTENCIA: Error en migraciones (continuando)"
}

to_lower() {
    echo "$1" | tr '[:upper:]' '[:lower:]'
}

ENABLE_PREDICTIONS=$(to_lower "${ENABLE_LOCAL_PREDICTIONS:-false}")
TRAIN_PREDICTIONS=$(to_lower "${TRAIN_PREDICTIONS_ON_START:-false}")
MIN_SAMPLES=${TRAIN_PREDICTIONS_MIN_SAMPLES:-30}

if [ "$ENABLE_PREDICTIONS" = "true" ] || [ "$ENABLE_PREDICTIONS" = "1" ]; then
    echo "✅ Predicciones habilitadas (ENABLE_LOCAL_PREDICTIONS=$ENABLE_LOCAL_PREDICTIONS)"
    if [ "$TRAIN_PREDICTIONS" = "true" ] || [ "$TRAIN_PREDICTIONS" = "1" ]; then
        echo "Entrenando modelo local antes de iniciar (min muestras: $MIN_SAMPLES)..."
        python manage.py train_prediction_model --min-samples "$MIN_SAMPLES" 2>&1 | tail -20 || {
            echo "⚠️ ADVERTENCIA: No se pudo entrenar el modelo (se usará heurística si es necesario)"
        }
    else
        echo "Omitiendo entrenamiento automático (TRAIN_PREDICTIONS_ON_START desactivado)"
    fi
else
    echo "Predicciones deshabilitadas (ENABLE_LOCAL_PREDICTIONS=$ENABLE_LOCAL_PREDICTIONS)"
fi

# Crear carpeta media si no existe (para almacenar imágenes de reportes)
echo "Creando carpeta media si no existe..."
mkdir -p media/reportes || {
    echo "⚠️ ADVERTENCIA: No se pudo crear carpeta media (continuando)"
}
echo "Carpeta media creada/verificada"

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
# Azure App Service usa la variable de entorno PORT
PORT="${PORT:-8000}"
echo "Usando puerto: $PORT"
echo "Comando: gunicorn ecoalerta.wsgi:application --bind 0.0.0.0:$PORT --workers 2"
exec gunicorn ecoalerta.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug \
    --capture-output \
    --enable-stdio-inheritance
