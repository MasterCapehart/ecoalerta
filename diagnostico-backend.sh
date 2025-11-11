#!/bin/bash
# Script para diagnosticar el problema del backend

APP_NAME="ecoalerta-backend"
RESOURCE_GROUP="ecoalerta1"

echo "🔍 Diagnóstico del Backend"
echo "=========================="
echo ""

# 1. Verificar estado
echo "1. Estado de la aplicación:"
az webapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "{state:state, httpsOnly:httpsOnly}" \
  --output table

echo ""

# 2. Verificar startup command
echo "2. Startup Command:"
STARTUP_CMD=$(az webapp config show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "appCommandLine" \
  --output tsv)

if [ -z "$STARTUP_CMD" ]; then
    echo "⚠️  Startup command NO está configurado"
else
    echo "✅ Startup command está configurado"
    echo "   Longitud: ${#STARTUP_CMD} caracteres"
fi

echo ""

# 3. Verificar variables de entorno
echo "3. Variables de entorno críticas:"
az webapp config appsettings list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[?name=='SECURE_SSL_REDIRECT' || name=='ALLOWED_HOSTS' || name=='DEBUG' || name=='SECRET_KEY']" \
  --output table

echo ""

# 4. Probar endpoint
echo "4. Probando endpoint (sin seguir redirecciones):"
curl -v --max-redirs 0 -X POST \
  "https://${APP_NAME}-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  2>&1 | grep -i "HTTP\|Location\|301\|302\|500" | head -5

echo ""

# 5. Verificar logs usando Kudu API
echo "5. Intentando acceder a logs (últimas 20 líneas):"
LOG_URL="https://${APP_NAME}.scm.azurewebsites.net/api/logs/docker/zip"
echo "   URL: $LOG_URL"
echo "   (Nota: Esto requiere autenticación, usa Azure Portal para ver logs)"
echo ""

# 6. Verificar si el código se desplegó
echo "6. Verificando despliegues recientes:"
az webapp deployment list-publishing-profiles \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --xml 2>&1 | grep -i "publishUrl\|destinationAppUrl" | head -2

echo ""

# 7. Recomendaciones
echo "📝 Recomendaciones:"
echo "   1. Verifica los logs en Azure Portal → Log stream"
echo "   2. Verifica que el código se haya desplegado correctamente"
echo "   3. Prueba acceder vía SSH: az webapp ssh --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo "   4. Verifica que el middleware PreventRedirectsMiddleware esté funcionando"
echo ""

