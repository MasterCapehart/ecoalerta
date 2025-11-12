#!/bin/bash
# Script de build para Azure App Service
# Este script instala dependencias del sistema necesarias para Django GIS
# IMPORTANTE: Este script se ejecuta ANTES de que Oryx instale dependencias de Python

set -e

echo "🔧 Instalando dependencias del sistema para Django GIS..."

# Instalar dependencias del sistema requeridas para Django GIS
# Usar sudo si está disponible, de lo contrario intentar sin sudo
if command -v sudo &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        libpq-dev \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        python3-gdal \
        > /dev/null 2>&1 || {
        echo "⚠️ Error instalando con sudo, intentando sin sudo..."
        apt-get update -qq
        apt-get install -y -qq \
            libpq-dev \
            gdal-bin \
            libgdal-dev \
            libgeos-dev \
            libproj-dev \
            python3-gdal \
            > /dev/null 2>&1 || echo "⚠️ No se pudieron instalar dependencias del sistema"
    }
else
    apt-get update -qq
    apt-get install -y -qq \
        libpq-dev \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        python3-gdal \
        > /dev/null 2>&1 || echo "⚠️ No se pudieron instalar dependencias del sistema"
fi

echo "✅ Dependencias del sistema instaladas (o intentado)"

# Verificar que GDAL está disponible
if command -v gdalinfo &> /dev/null; then
    echo "✅ GDAL instalado correctamente"
    gdalinfo --version
else
    echo "⚠️ GDAL no está disponible, Django puede tener problemas"
fi

# Oryx continuará con la instalación de dependencias de Python automáticamente

