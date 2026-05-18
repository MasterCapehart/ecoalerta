#!/bin/bash
echo "=== Installing GDAL system libraries ==="
apt-get update -qq && apt-get install -y -qq libgdal-dev gdal-bin libgeos-dev libproj-dev

export GDAL_LIBRARY_PATH=$(find /usr -name "libgdal.so*" | head -1)
export GEOS_LIBRARY_PATH=$(find /usr -name "libgeos_c.so*" | head -1)

echo "GDAL: $GDAL_LIBRARY_PATH"
echo "GEOS: $GEOS_LIBRARY_PATH"

echo "=== Starting Gunicorn ==="
cd /home/site/wwwroot
gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 ecoalerta.wsgi
