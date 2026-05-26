#!/bin/bash
set -e

echo "=== Installing GDAL system libraries ==="
apt-get update -qq && apt-get install -y -qq libgdal-dev gdal-bin libgeos-dev libproj-dev

export GDAL_LIBRARY_PATH=$(find /usr -name "libgdal.so*" | head -1)
export GEOS_LIBRARY_PATH=$(find /usr -name "libgeos_c.so*" | head -1)
echo "GDAL: $GDAL_LIBRARY_PATH"
echo "GEOS: $GEOS_LIBRARY_PATH"

WWWROOT=/home/site/wwwroot
PYTHON=$WWWROOT/antenv/bin/python

echo "=== Resetting user passwords ==="
$PYTHON $WWWROOT/manage.py shell -c "
from reportes.models import Usuario
for username, password in [('administrador','Admin1234!'),('inspector','Inspector1234!')]:
    try:
        u = Usuario.objects.get(username=username)
        u.set_password(password)
        u.save()
        print(f'Password reset OK: {username}')
    except Exception as e:
        print(f'Error {username}: {e}')
" || true

echo "=== Starting Gunicorn ==="
exec $WWWROOT/antenv/bin/gunicorn \
  --bind=0.0.0.0:8000 \
  --timeout 600 \
  --workers 2 \
  --chdir $WWWROOT \
  ecoalerta.wsgi
