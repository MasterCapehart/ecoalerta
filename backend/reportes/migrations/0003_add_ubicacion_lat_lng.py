# Migration to add ubicacion_lat and ubicacion_lng columns
# This migration depends on 0002_alter_reporte_ubicacion_lat_and_more
# and adds the columns if they don't exist

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reportes', '0002_alter_reporte_ubicacion_lat_and_more'),
    ]

    operations = [
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
    ]

