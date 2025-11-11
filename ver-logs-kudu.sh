#!/bin/bash
# Script para acceder a los logs usando Kudu (SSH)

APP_NAME="ecoalerta-backend"
RESOURCE_GROUP="ecoalerta1"

echo "🔍 Accediendo a logs usando Kudu..."
echo ""

# Obtener la URL de Kudu
KUDU_URL="https://${APP_NAME}.scm.azurewebsites.net"

echo "📍 URL de Kudu: $KUDU_URL"
echo ""
echo "Para acceder a los logs:"
echo "1. Ve a: $KUDU_URL"
echo "2. O usa SSH:"
echo "   az webapp ssh --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "📝 Comandos útiles en Kudu:"
echo "   - Ver logs: https://${APP_NAME}.scm.azurewebsites.net/api/logs/docker"
echo "   - Ver archivos: https://${APP_NAME}.scm.azurewebsites.net/api/vfs/site/wwwroot/"
echo "   - Ver procesos: https://${APP_NAME}.scm.azurewebsites.net/api/processes"
echo ""

# Intentar acceder a los logs usando la API de Kudu
echo "🔍 Intentando acceder a logs..."
curl -s "https://${APP_NAME}.scm.azurewebsites.net/api/logs/docker" | head -100

echo ""
echo "✅ Si no puedes acceder, usa Azure Portal:"
echo "   Azure Portal → App Service → Advanced Tools (Kudu) → Go"
echo ""

