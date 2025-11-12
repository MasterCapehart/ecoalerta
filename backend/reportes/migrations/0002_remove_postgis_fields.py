# Generated manually - Migración para eliminar campos PostGIS y usar campos estándar
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reportes', '0001_initial'),
    ]

    operations = [
        # Agregar nuevos campos primero
        migrations.AddField(
            model_name='reporte',
            name='ubicacion_lat',
            field=models.FloatField(blank=True, db_index=True, null=True, verbose_name='Latitud'),
        ),
        migrations.AddField(
            model_name='reporte',
            name='ubicacion_lng',
            field=models.FloatField(blank=True, db_index=True, null=True, verbose_name='Longitud'),
        ),
        # Eliminar el campo PointField si existe (puede fallar si no existe, pero continuará)
        migrations.RemoveField(
            model_name='reporte',
            name='ubicacion',
        ),
    ]

