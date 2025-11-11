# Solución Definitiva para Error 301 en Azure

## Problema
Las requests a `/api/auth/login/` están devolviendo código 301 (redirección permanente) en Azure App Service.

## Cambios Realizados en el Código

### 1. Middleware Personalizado
Se creó `backend/ecoalerta/middleware.py` con dos middlewares:
- `DisableCSRFForAPI`: Desactiva CSRF para endpoints API
- `PreventRedirectsMiddleware`: Detecta y previene redirecciones no deseadas en API

### 2. Configuración de Settings
- Reactivados SecurityMiddleware y CommonMiddleware
- Configurado `APPEND_SLASH = True`
- Configurados headers de proxy para Azure
- Desactivado `SECURE_SSL_REDIRECT = False`
- Configurado `PREPEND_WWW = False`

## Verificación en Azure Portal

### PASO 1: Verificar Configuración de HTTPS
1. Ve a Azure Portal → App Service → `ecoalerta-backend`
2. Ve a **Configuration** → **General settings**
3. Busca **"HTTPS Only"**
4. **DESACTÍVALO temporalmente** (cámbialo a OFF)
5. Haz clic en **Save**
6. Espera a que se reinicie la aplicación

### PASO 2: Verificar Variables de Entorno
1. Ve a **Configuration** → **Application settings**
2. Verifica que **NO exista** la variable `SECURE_SSL_REDIRECT`
3. Si existe, elimínala o cámbiala a `False`
4. Verifica que `ALLOWED_HOSTS` incluya tu dominio de Azure
5. Haz clic en **Save**

### PASO 3: Verificar Startup Command
1. Ve a **Configuration** → **General settings**
2. Busca **"Startup Command"**
3. Verifica que esté configurado correctamente (debe incluir el comando inline)
4. Si está vacío, cópialo desde `backend/azure-app-service.yml`

### PASO 4: Verificar Path Mappings
1. Ve a **Configuration** → **Path mappings**
2. Verifica que **NO haya reglas de redirección** configuradas
3. Si hay alguna, elimínala temporalmente

## Comandos Azure CLI (Alternativa)

Si prefieres usar la línea de comandos:

```bash
# 1. Desactivar HTTPS Only
az webapp update \
  --name ecoalerta-backend \
  --resource-group ecoalerta1 \
  --https-only false

# 2. Verificar variables de entorno
az webapp config appsettings list \
  --name ecoalerta-backend \
  --resource-group ecoalerta1 \
  --query "[?name=='SECURE_SSL_REDIRECT']"

# 3. Eliminar SECURE_SSL_REDIRECT si existe
az webapp config appsettings delete \
  --name ecoalerta-backend \
  --resource-group ecoalerta1 \
  --setting-names SECURE_SSL_REDIRECT

# 4. Verificar configuración general
az webapp config show \
  --name ecoalerta-backend \
  --resource-group ecoalerta1 \
  --query "{alwaysOn: alwaysOn, httpsOnly: httpsOnly}"
```

## Desplegar los Cambios

### Opción 1: GitHub Actions (Recomendado)
1. Haz commit de los cambios:
```bash
git add backend/ecoalerta/middleware.py backend/ecoalerta/settings.py
git commit -m "Fix: Agregar middleware para prevenir redirecciones 301 en API"
git push origin main
```

2. Espera a que GitHub Actions despliegue los cambios

### Opción 2: Despliegue Manual
1. Ve a Azure Portal → App Service → **Deployment Center**
2. Haz clic en **Sync** para forzar un nuevo despliegue
3. O usa Azure CLI:
```bash
az webapp restart \
  --name ecoalerta-backend \
  --resource-group ecoalerta1
```

## Verificar que Funciona

### 1. Verificar Logs
1. Ve a **Log stream** en Azure Portal
2. Busca que el servidor se haya reiniciado correctamente
3. Verifica que no haya errores relacionados con redirecciones

### 2. Probar el Endpoint
Usa curl o Postman para probar:
```bash
curl -X POST https://ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

Deberías recibir una respuesta JSON (no un 301).

### 3. Probar desde el Frontend
1. Abre el frontend en el navegador
2. Intenta hacer login
3. Verifica que no aparezca el error "Error al conectar con el servidor"

## Si el Problema Persiste

### 1. Verificar Application Insights
1. Ve a **Application Insights** en Azure Portal
2. Revisa las métricas de respuesta
3. Busca códigos de estado 301 o 302
4. Verifica el tiempo de respuesta

### 2. Verificar Network Tab en el Navegador
1. Abre las herramientas de desarrollador (F12)
2. Ve a la pestaña **Network**
3. Intenta hacer login
4. Verifica qué está pasando con la request:
   - ¿A qué URL se está haciendo la request?
   - ¿Qué headers tiene la request?
   - ¿Qué respuesta está recibiendo?

### 3. Verificar Frontend
1. Verifica que el frontend esté usando la URL correcta del backend
2. Verifica que la URL sea HTTPS (no HTTP)
3. Verifica que no haya problemas con CORS

## Notas Importantes

- Los cambios en `settings.py` y `middleware.py` requieren que el backend se reinicie
- Desactivar "HTTPS Only" es temporal - una vez que funcione, puedes reactivarlo
- El middleware `PreventRedirectsMiddleware` convertirá las redirecciones 301 en errores 500 para ayudarte a diagnosticar el problema
- Si ves errores 500 después de estos cambios, revisa los logs para ver qué está causando la redirección

## Próximos Pasos

1. ✅ Desplegar los cambios al backend
2. ✅ Desactivar "HTTPS Only" en Azure Portal
3. ✅ Verificar que no haya variables de entorno conflictivas
4. ✅ Probar el endpoint desde curl/Postman
5. ✅ Probar desde el frontend
6. ✅ Si funciona, reactivar "HTTPS Only" y verificar que siga funcionando

