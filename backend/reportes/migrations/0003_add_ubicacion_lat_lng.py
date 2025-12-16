# Migration to add ubicacion_lat and ubicacion_lng columns
# This migration depends on 0002_alter_reporte_ubicacion_lat_and_more
# and adds the columns if they don't exist

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reportes', '0002_alter_reporte_ubicacion_lat_and_more'),
    ]

    operations = [
        # Los campos ya están presentes en 0001_initial; mantenemos esta migración
        # como no-op para preservar la historia y evitar errores de duplicado.
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
    ]

