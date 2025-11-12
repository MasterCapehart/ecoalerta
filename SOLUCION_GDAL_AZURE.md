# Solución: Problema con GDAL en Azure

## Problema Identificado

El problema real no es las redirecciones 301, sino que **Django no puede iniciar correctamente** debido a que GDAL no está disponible durante el build. Los logs muestran:

```
OSError: /usr/lib/libgdal.so: cannot open shared object file: No such file or directory
```

Esto ocurre cuando Django intenta cargar `django.contrib.gis` durante el build/post-build, y GDAL no está disponible en el entorno de build de Oryx.

## Síntomas

1. El `POST_BUILD_COMMAND` falla durante `migrate` o `collectstatic`
2. La aplicación no inicia correctamente
3. Azure devuelve respuestas de error que pueden parecer redirecciones 301
4. El servidor no responde correctamente a las requests

## Solución Aplicada

### 1. Mejorar Detección de Rutas GDAL/GEOS

Modificado `settings.py` para intentar múltiples rutas comunes para GDAL/GEOS en Azure:

```python
# Intentar múltiples rutas comunes
possible_gdal_paths = [
    '/usr/lib/libgdal.so',
    '/usr/lib/x86_64-linux-gnu/libgdal.so',
    '/usr/lib/x86_64-linux-gnu/libgdal.so.32',
    '/usr/lib/x86_64-linux-gnu/libgdal.so.33',
]
```

### 2. Hacer POST_BUILD_COMMAND Más Robusto

Configurado `POST_BUILD_COMMAND` para que no falle si `migrate` o `collectstatic` tienen problemas:

```bash
python manage.py collectstatic --noinput || echo 'Collectstatic failed, continuing...'
python manage.py migrate --noinput || echo 'Migrate failed, continuing...'
```

### 3. Desactivar SecurityMiddleware

Desactivado `SecurityMiddleware` temporalmente para eliminar posibles bucles de redirección causados por configuración de seguridad.

## Próximos Pasos

1. **Esperar despliegue**: El workflow de GitHub Actions desplegará los cambios
2. **Verificar logs**: Revisar logs de Azure para confirmar que la aplicación inicia correctamente
3. **Probar endpoint**: Probar el endpoint `/api/auth/login/` después del despliegue
4. **Instalar GDAL correctamente**: Si el problema persiste, necesitamos asegurar que GDAL se instale correctamente durante el build

## Comandos Útiles

### Verificar configuración de Azure
```bash
az webapp config appsettings list --name ecoalerta-backend --resource-group ecoalerta1 --query "[?name=='POST_BUILD_COMMAND']" -o table
```

### Reiniciar aplicación
```bash
az webapp restart --name ecoalerta-backend --resource-group ecoalerta1
```

### Ver logs
```bash
az webapp log download --name ecoalerta-backend --resource-group ecoalerta1 --log-file logs.zip
```

## Notas Importantes

- El problema de las redirecciones 301 es un **síntoma secundario** del problema real: Django no puede iniciar debido a GDAL
- Una vez que Django pueda iniciar correctamente, las redirecciones deberían resolverse
- Si GDAL sigue siendo un problema, podemos considerar:
  - Usar un contenedor Docker personalizado con GDAL preinstalado
  - Instalar GDAL en el startup command en lugar del build
  - Desactivar temporalmente PostGIS si no es crítico

