#!/bin/bash
# Script de build para Azure App Service
# NO instalar GDAL/GEOS - no se usan PostGIS

echo "🔧 Instalando solo libpq-dev para PostgreSQL..."

# Instalar solo libpq-dev para PostgreSQL (sin GDAL/GEOS)
if command -v sudo &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq libpq-dev > /dev/null 2>&1 || {
        apt-get update -qq
        apt-get install -y -qq libpq-dev > /dev/null 2>&1 || echo "⚠️ No se pudo instalar libpq-dev"
    }
else
    apt-get update -qq
    apt-get install -y -qq libpq-dev > /dev/null 2>&1 || echo "⚠️ No se pudo instalar libpq-dev"
fi

echo "✅ libpq-dev instalado"

# Oryx continuará con la instalación de dependencias de Python automáticamente

