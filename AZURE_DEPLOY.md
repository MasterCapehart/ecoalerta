# 🚀 Guía de Despliegue en Azure con CI/CD

Esta guía te ayudará a desplegar EcoAlerta en Azure con despliegue automático mediante GitHub Actions.

## 📋 Prerequisitos

1. **Cuenta de Azure** con suscripción activa
2. **Repositorio en GitHub** con el código del proyecto
3. **Azure CLI** instalado (opcional, pero recomendado)
4. **PostgreSQL en Azure** (ya configurado según tu `settings.py`)

## 🔧 Paso 1: Crear Recursos en Azure

### 1.1 Crear Azure App Service para el Backend (Django)

```bash
# Iniciar sesión en Azure
az login

# Crear grupo de recursos
az group create --name ecoalerta-rg --location eastus

# Crear App Service Plan
az appservice plan create \
  --name ecoalerta-plan \
  --resource-group ecoalerta-rg \
  --sku B1 \
  --is-linux

# Crear Web App para el backend
az webapp create \
  --name ecoalerta-backend \
  --resource-group ecoalerta-rg \
  --plan ecoalerta-plan \
  --runtime "PYTHON:3.11"

# Configurar variables de entorno
az webapp config appsettings set \
  --name ecoalerta-backend \
  --resource-group ecoalerta-rg \
  --settings \
    DB_NAME="tu_db_name" \
    DB_USER="tu_db_user" \
    DB_PASSWORD="tu_db_password" \
    DB_HOST="tu_db_host.postgres.database.azure.com" \
    DB_PORT="5432" \
    SECRET_KEY="tu-secret-key-muy-segura" \
    DEBUG="False" \
    ALLOWED_HOSTS="ecoalerta-backend.azurewebsites.net,tu-dominio.com" \
    AZURE_FRONTEND_URL="https://tu-frontend-url.azurestaticapps.net"

# Habilitar siempre activo (opcional, evita cold starts)
az webapp config set \
  --name ecoalerta-backend \
  --resource-group ecoalerta-rg \
  --always-on true

# Configurar el script de inicio
az webapp config set \
  --name ecoalerta-backend \
  --resource-group ecoalerta-rg \
  --startup-file "bash startup.sh"
```

### 1.2 Crear Azure Static Web Apps para el Frontend (React)

```bash
# Crear Static Web App
az staticwebapp create \
  --name ecoalerta-frontend \
  --resource-group ecoalerta-rg \
  --location "East US 2" \
  --sku Free

# Obtener el token de despliegue
az staticwebapp secrets list \
  --name ecoalerta-frontend \
  --resource-group ecoalerta-rg \
  --query "properties.apiKey" \
  --output tsv
```

**Alternativa usando Azure Portal:**

1. Ve a [Azure Portal](https://portal.azure.com)
2. Crea un nuevo recurso "Static Web Apps"
3. Conecta tu repositorio de GitHub
4. Configura:
   - **App location**: `/frontend`
   - **Output location**: `dist`
   - **Build presets**: Custom

## 🔐 Paso 2: Configurar Secrets en GitHub

Ve a tu repositorio en GitHub → Settings → Secrets and variables → Actions

Agrega los siguientes secrets:

### Para el Backend:
- `AZURE_WEBAPP_PUBLISH_PROFILE`: Obtén el perfil de publicación desde Azure Portal:
  1. Ve a tu App Service → Overview → Get publish profile
  2. Copia todo el contenido del archivo `.PublishSettings`
  3. Pégalo como secret

- `AZURE_DB_NAME`: Nombre de tu base de datos PostgreSQL
- `AZURE_DB_USER`: Usuario de la base de datos
- `AZURE_DB_PASSWORD`: Contraseña de la base de datos
- `AZURE_DB_HOST`: Host de la base de datos (ej: `ecoalerta.postgres.database.azure.com`)
- `AZURE_DB_PORT`: Puerto (generalmente `5432`)
- `DJANGO_SECRET_KEY`: Una clave secreta segura para Django
- `ALLOWED_HOSTS`: Dominios permitidos separados por comas
- `VITE_API_URL`: URL del backend en Azure (ej: `https://ecoalerta-backend.azurewebsites.net`)

### Para el Frontend:
- `AZURE_STATIC_WEB_APPS_API_TOKEN`: Token de despliegue de Static Web Apps
  - Obtén este token desde Azure Portal → Static Web App → Manage deployment token

## 📝 Paso 3: Configurar el Workflow de GitHub Actions

Los workflows ya están creados en `.github/workflows/`. Solo necesitas:

1. **Hacer push de los cambios a GitHub**
2. **Verificar que los workflows se ejecuten correctamente**

Los workflows se activarán automáticamente cuando:
- Hagas push a la rama `main`
- Modifiques archivos en `backend/` o `frontend/`
- O manualmente desde la pestaña "Actions" en GitHub

## 🔄 Paso 4: Verificar el Despliegue

### Backend:
1. Ve a `https://ecoalerta-backend.azurewebsites.net/admin`
2. Deberías ver la página de login de Django

### Frontend:
1. Ve a la URL de tu Static Web App (ej: `https://ecoalerta-frontend.azurestaticapps.net`)
2. Deberías ver tu aplicación React

## 🛠️ Solución de Problemas

### Error: "Module not found" en el backend
- Verifica que todas las dependencias estén en `requirements.txt`
- Revisa los logs en Azure Portal → App Service → Log stream

### Error: CORS en el frontend
- Verifica que `AZURE_FRONTEND_URL` esté configurado en el backend
- Asegúrate de que la URL del frontend esté en `CORS_ALLOWED_ORIGINS`

### Error: Base de datos no conecta
- Verifica las credenciales en las variables de entorno
- Asegúrate de que el firewall de Azure PostgreSQL permita conexiones desde App Service
- En Azure Portal → PostgreSQL → Connection security, agrega la IP del App Service

### Error: Archivos estáticos no se cargan
- Verifica que `collectstatic` se ejecute durante el despliegue
- Revisa que WhiteNoise esté configurado correctamente

### Ver logs del backend:
```bash
az webapp log tail \
  --name ecoalerta-backend \
  --resource-group ecoalerta-rg
```

O desde Azure Portal → App Service → Log stream

## 📊 Monitoreo

### Ver métricas:
- Azure Portal → App Service → Metrics
- Azure Portal → Static Web App → Metrics

### Configurar alertas:
- Azure Portal → App Service → Alerts
- Configura alertas para errores, tiempo de respuesta, etc.

## 🔄 Actualizaciones Automáticas

Una vez configurado, cada vez que hagas push a `main`:
1. GitHub Actions detectará los cambios
2. Construirá la aplicación
3. Ejecutará migraciones (backend)
4. Desplegará automáticamente a Azure

## 💰 Costos Estimados

- **App Service Plan B1**: ~$13/mes
- **Static Web Apps**: Gratis (hasta cierto límite)
- **PostgreSQL**: Depende del tier elegido

## 📚 Recursos Adicionales

- [Documentación de Azure App Service](https://docs.microsoft.com/azure/app-service/)
- [Documentación de Azure Static Web Apps](https://docs.microsoft.com/azure/static-web-apps/)
- [GitHub Actions para Azure](https://github.com/marketplace?type=actions&query=azure)

## ✅ Checklist de Despliegue

- [ ] Recursos creados en Azure
- [ ] Variables de entorno configuradas
- [ ] Secrets configurados en GitHub
- [ ] Workflows de GitHub Actions funcionando
- [ ] Backend accesible y funcionando
- [ ] Frontend accesible y funcionando
- [ ] CORS configurado correctamente
- [ ] Base de datos conectada
- [ ] Migraciones ejecutadas
- [ ] Archivos estáticos cargando correctamente

---

¿Necesitas ayuda? Revisa los logs en Azure Portal o en GitHub Actions.

