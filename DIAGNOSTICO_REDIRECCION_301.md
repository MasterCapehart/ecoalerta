# Diagnóstico: Redirección 301 Persistente

## Problema

El endpoint `/api/auth/login/` está devolviendo una redirección 301 a la misma URL, creando un bucle de redirección. El middleware `PreventRedirectsMiddleware` no está interceptando la redirección, lo que sugiere que:

1. El código no se ha desplegado correctamente en Azure
2. La redirección está ocurriendo antes de que Django la procese (a nivel de Azure o Gunicorn)
3. Hay alguna configuración en Azure que está causando la redirección

## Estado Actual

### Configuración Django
- ✅ `SECURE_SSL_REDIRECT = False`
- ✅ `APPEND_SLASH = False`
- ✅ `PREPEND_WWW = False`
- ✅ `SecurityMiddleware` desactivado temporalmente
- ✅ `CommonMiddleware` desactivado temporalmente
- ✅ `PreventRedirectsMiddleware` configurado al final de la cadena de middleware

### Configuración Azure
- ✅ `SECURE_SSL_REDIRECT = False` (variable de entorno)
- ✅ `APPEND_SLASH = False` (variable de entorno)
- ❓ `httpsOnly` = null (no está configurado explícitamente)

### Comportamiento Observado
- El endpoint devuelve `HTTP/1.1 301 Moved Permanently`
- Location header: `https://ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net/api/auth/login/` (misma URL)
- Server: `gunicorn` (Django está respondiendo)
- El middleware no está interceptando la redirección

## Posibles Causas

### 1. Código no Desplegado Correctamente
**Síntoma**: El middleware no intercepta la redirección
**Solución**: 
- Verificar que el workflow de GitHub Actions se haya ejecutado correctamente
- Verificar que el código desplegado tenga el middleware actualizado
- Reiniciar la aplicación en Azure

### 2. Redirección a Nivel de Azure App Service
**Síntoma**: La redirección ocurre antes de que Django la procese
**Solución**:
- Verificar configuración de "HTTPS Only" en Azure Portal
- Verificar configuración de "Always On" en Azure Portal
- Verificar configuración de "Application Settings" en Azure Portal

### 3. Redirección por Gunicorn
**Síntoma**: Gunicorn está redirigiendo antes de pasar la request a Django
**Solución**:
- Verificar configuración de Gunicorn en `startup.sh`
- Verificar que Gunicorn no tenga configuración de redirección

### 4. Redirección por WhiteNoise
**Síntoma**: WhiteNoise está redirigiendo requests a archivos estáticos
**Solución**:
- Verificar que las URLs de API no coincidan con rutas de archivos estáticos
- Verificar configuración de WhiteNoise

### 5. Redirección por CORS
**Síntoma**: CORS está causando redirecciones
**Solución**:
- Verificar configuración de CORS
- Verificar que los headers CORS estén configurados correctamente

## Acciones Recomendadas

### 1. Verificar Despliegue
```bash
# Verificar que el workflow se haya ejecutado
# Revisar logs de GitHub Actions

# Reiniciar la aplicación
az webapp restart --name ecoalerta-backend --resource-group ecoalerta1
```

### 2. Verificar Logs de Azure
```bash
# Ver logs en tiempo real
az webapp log tail --name ecoalerta-backend --resource-group ecoalerta1

# Ver logs de aplicación
az webapp log download --name ecoalerta-backend --resource-group ecoalerta1 --log-file app-logs.zip
```

### 3. Verificar Configuración de Azure
```bash
# Ver configuración de HTTPS Only
az webapp config show --name ecoalerta-backend --resource-group ecoalerta1 --query "{httpsOnly: httpsOnly}"

# Desactivar HTTPS Only si está activado
az webapp update --name ecoalerta-backend --resource-group ecoalerta1 --https-only false

# Ver configuración de Always On
az webapp config show --name ecoalerta-backend --resource-group ecoalerta1 --query "{alwaysOn: alwaysOn}"
```

### 4. Probar Endpoint Directamente
```bash
# Probar con curl
curl -v -X POST https://ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  --max-redirs 0

# Probar con método GET
curl -I https://ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net/api/auth/login/
```

### 5. Verificar que el Middleware se Está Ejecutando
- Revisar logs de aplicación en Azure Portal
- Buscar mensajes de log del middleware
- Verificar que el middleware esté en la cadena de middleware

## Próximos Pasos

1. **Esperar despliegue**: Esperar a que el workflow de GitHub Actions complete el despliegue
2. **Reiniciar aplicación**: Reiniciar la aplicación en Azure después del despliegue
3. **Verificar logs**: Revisar logs de aplicación para ver si el middleware se está ejecutando
4. **Probar endpoint**: Probar el endpoint después del reinicio
5. **Verificar configuración**: Verificar configuración de Azure si el problema persiste

## Notas Importantes

- El middleware `PreventRedirectsMiddleware` debe estar al **FINAL** de la cadena de middleware para interceptar redirecciones después de que otros middlewares las generen
- El middleware solo intercepta redirecciones en endpoints que comienzan con `/api/`
- Si el middleware no está interceptando la redirección, puede ser que:
  - El código no se haya desplegado correctamente
  - La redirección esté ocurriendo antes de que Django la procese
  - Hay algún problema con la configuración de Azure

