#!/bin/bash
set -e

echo "=== Installing GDAL system libraries ==="
apt-get update -qq && apt-get install -y -qq libgdal-dev gdal-bin libgeos-dev libproj-dev

export GDAL_LIBRARY_PATH=$(find /usr -name "libgdal.so*" | head -1)
export GEOS_LIBRARY_PATH=$(find /usr -name "libgeos_c.so*" | head -1)
echo "GDAL: $GDAL_LIBRARY_PATH"
echo "GEOS: $GEOS_LIBRARY_PATH"

echo "=== Installing Python dependencies ==="
cd /home/site/wwwroot
pip install -r requirements.txt --quiet

echo "=== Resetting user passwords ==="
python manage.py shell -c "
from reportes.models import Usuario
for username, password in [('administrador','Admin1234!'),('inspector','Inspector1234!')]:
    try:
        u = Usuario.objects.get(username=username)
        u.set_password(password)
        u.save()
        print(f'Password reset OK: {username}')
    except Exception as e:
        print(f'Error: {e}')
" || true

echo "=== Starting Gunicorn from wwwroot ==="
export PYTHONPATH=/home/site/wwwroot
export PYTHONDONTWRITEBYTECODE=1
exec gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 --chdir /home/site/wwwroot ecoalerta.wsgi
