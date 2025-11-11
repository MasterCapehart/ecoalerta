#!/bin/bash
# Script para solucionar el problema de bucle de redirecciones

APP_NAME="ecoalerta-backend"
RESOURCE_GROUP="ecoalerta1"

echo "🔧 Solucionando bucle de redirecciones..."
echo ""

# 1. Desactivar HTTPS Only temporalmente
echo "1. Desactivando HTTPS Only..."
az webapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --https-only false \
  --output none

echo "✅ HTTPS Only desactivado"
echo ""

# 2. Verificar que no haya SECURE_SSL_REDIRECT
echo "2. Verificando SECURE_SSL_REDIRECT..."
SECURE_SSL=$(az webapp config appsettings list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[?name=='SECURE_SSL_REDIRECT'].value" \
  --output tsv)

if [ ! -z "$SECURE_SSL" ]; then
    echo "⚠️  SECURE_SSL_REDIRECT encontrado: $SECURE_SSL"
    echo "Eliminando SECURE_SSL_REDIRECT..."
    az webapp config appsettings delete \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --setting-names SECURE_SSL_REDIRECT \
      --output none
    echo "✅ SECURE_SSL_REDIRECT eliminado"
else
    echo "✅ SECURE_SSL_REDIRECT no está configurado"
fi

echo ""

# 3. Verificar ALLOWED_HOSTS
echo "3. Verificando ALLOWED_HOSTS..."
ALLOWED_HOSTS=$(az webapp config appsettings list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[?name=='ALLOWED_HOSTS'].value" \
  --output tsv)

if [ -z "$ALLOWED_HOSTS" ]; then
    echo "⚠️  ALLOWED_HOSTS no está configurado"
    echo "Configurando ALLOWED_HOSTS..."
    az webapp config appsettings set \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --settings ALLOWED_HOSTS="ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net" \
      --output none
    echo "✅ ALLOWED_HOSTS configurado"
else
    echo "✅ ALLOWED_HOSTS está configurado: $ALLOWED_HOSTS"
fi

echo ""

# 4. Reiniciar la aplicación
echo "4. Reiniciando la aplicación..."
az webapp restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none

echo "✅ Aplicación reiniciada"
echo ""

# 5. Esperar unos segundos
echo "⏳ Esperando 10 segundos para que la aplicación se inicie..."
sleep 10

echo ""
echo "✅ Configuración completada!"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Intenta ver los logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo "   2. Prueba el endpoint: curl https://ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net/"
echo "   3. Si funciona, puedes reactivar HTTPS Only desde Azure Portal"
echo ""

