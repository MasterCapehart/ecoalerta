#!/bin/bash

# Script para configurar recursos de Azure para EcoAlerta
# Requiere Azure CLI instalado y autenticado

set -e

echo "🚀 Configurando recursos de Azure para EcoAlerta..."
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables configurables
RESOURCE_GROUP="ecoalerta-rg"
LOCATION="eastus"
APP_SERVICE_PLAN="ecoalerta-plan"
BACKEND_APP_NAME="ecoalerta-backend"
FRONTEND_APP_NAME="ecoalerta-frontend"
SKU="B1"  # Cambia a F1 para el tier gratuito

# Verificar que Azure CLI está instalado
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI no está instalado. Instálalo desde: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Verificar que está autenticado
echo "🔐 Verificando autenticación en Azure..."
if ! az account show &> /dev/null; then
    echo "⚠️  No estás autenticado. Iniciando login..."
    az login
fi

echo -e "${GREEN}✅ Autenticado en Azure${NC}"
echo ""

# Crear grupo de recursos
echo "📦 Creando grupo de recursos: $RESOURCE_GROUP..."
az group create --name $RESOURCE_GROUP --location $LOCATION --output none
echo -e "${GREEN}✅ Grupo de recursos creado${NC}"
echo ""

# Crear App Service Plan
echo "📋 Creando App Service Plan: $APP_SERVICE_PLAN..."
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku $SKU \
  --is-linux \
  --output none
echo -e "${GREEN}✅ App Service Plan creado${NC}"
echo ""

# Crear Web App para backend
echo "🔧 Creando Web App para backend: $BACKEND_APP_NAME..."
az webapp create \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --runtime "PYTHON:3.11" \
  --output none
echo -e "${GREEN}✅ Web App creada${NC}"
echo ""

# Configurar variables de entorno básicas
echo "⚙️  Configurando variables de entorno..."
echo -e "${YELLOW}⚠️  Necesitarás configurar estas variables manualmente:${NC}"
echo "   - DB_NAME"
echo "   - DB_USER"
echo "   - DB_PASSWORD"
echo "   - DB_HOST"
echo "   - DB_PORT"
echo "   - SECRET_KEY"
echo "   - ALLOWED_HOSTS"
echo "   - AZURE_FRONTEND_URL"
echo ""
read -p "¿Quieres configurar las variables ahora? (s/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    read -p "DB_NAME: " DB_NAME
    read -p "DB_USER: " DB_USER
    read -sp "DB_PASSWORD: " DB_PASSWORD
    echo ""
    read -p "DB_HOST: " DB_HOST
    read -p "DB_PORT [5432]: " DB_PORT
    DB_PORT=${DB_PORT:-5432}
    read -sp "SECRET_KEY: " SECRET_KEY
    echo ""
    read -p "ALLOWED_HOSTS (separados por comas): " ALLOWED_HOSTS
    read -p "AZURE_FRONTEND_URL: " FRONTEND_URL
    
    az webapp config appsettings set \
      --name $BACKEND_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --settings \
        DB_NAME="$DB_NAME" \
        DB_USER="$DB_USER" \
        DB_PASSWORD="$DB_PASSWORD" \
        DB_HOST="$DB_HOST" \
        DB_PORT="$DB_PORT" \
        SECRET_KEY="$SECRET_KEY" \
        DEBUG="False" \
        ALLOWED_HOSTS="$ALLOWED_HOSTS" \
        AZURE_FRONTEND_URL="$FRONTEND_URL" \
      --output none
    
    echo -e "${GREEN}✅ Variables de entorno configuradas${NC}"
else
    echo "Puedes configurarlas más tarde con:"
    echo "az webapp config appsettings set --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --settings KEY=VALUE"
fi
echo ""

# Habilitar always on
echo "🔌 Habilitando 'Always On'..."
az webapp config set \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --always-on true \
  --output none
echo -e "${GREEN}✅ Always On habilitado${NC}"
echo ""

# Configurar script de inicio
echo "📝 Configurando script de inicio..."
az webapp config set \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "bash startup.sh" \
  --output none
echo -e "${GREEN}✅ Script de inicio configurado${NC}"
echo ""

# Obtener perfil de publicación
echo "📥 Obteniendo perfil de publicación..."
PUBLISH_PROFILE=$(az webapp deployment list-publishing-profiles \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --xml \
  --output tsv)

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Configuración completada!${NC}"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Copia el perfil de publicación y agrégalo como secret en GitHub:"
echo "   - Ve a: https://github.com/TU_USUARIO/ecoalerta/settings/secrets/actions"
echo "   - Crea un secret llamado: AZURE_WEBAPP_PUBLISH_PROFILE"
echo "   - Pega el siguiente contenido:"
echo ""
echo "$PUBLISH_PROFILE" | head -20
echo "..."
echo ""
echo "2. Configura los demás secrets en GitHub (ver AZURE_DEPLOY.md)"
echo ""
echo "3. Para crear el Static Web App para el frontend:"
echo "   az staticwebapp create --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --location 'East US 2' --sku Free"
echo ""
echo "4. URL del backend: https://$BACKEND_APP_NAME.azurewebsites.net"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

