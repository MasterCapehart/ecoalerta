#!/bin/bash
set -e

echo "=== Installing GDAL system libraries ==="
apt-get update -qq && apt-get install -y -qq libgdal-dev gdal-bin libgeos-dev libproj-dev

export GDAL_LIBRARY_PATH=$(find /usr -name "libgdal.so*" | head -1)
export GEOS_LIBRARY_PATH=$(find /usr -name "libgeos_c.so*" | head -1)
echo "GDAL: $GDAL_LIBRARY_PATH"
echo "GEOS: $GEOS_LIBRARY_PATH"

WWWROOT=/home/site/wwwroot

echo "=== Patching serializers.py with lat/lng fallback ==="
python3 -c "
import os, glob

# Buscar todos los serializers.py del proyecto activo
paths = glob.glob('/tmp/*/reportes/serializers.py') + \
        glob.glob('/tmp/zipdeploy/*/reportes/serializers.py') + \
        ['/home/site/wwwroot/reportes/serializers.py']

for path in paths:
    if os.path.exists(path):
        c = open(path).read()
        if 'ubicacion_lat' not in c:
            c = c.replace(
                'return obj.ubicacion.y if obj.ubicacion else None',
                'return obj.ubicacion.y if obj.ubicacion else obj.ubicacion_lat'
            )
            c = c.replace(
                'return obj.ubicacion.x if obj.ubicacion else None',
                'return obj.ubicacion.x if obj.ubicacion else obj.ubicacion_lng'
            )
            open(path, 'w').write(c)
            print(f'Patched: {path}')
        else:
            print(f'Already patched: {path}')
"

echo "=== Resetting user passwords ==="
cd $WWWROOT
python manage.py shell -c "
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
exec gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 ecoalerta.wsgi
