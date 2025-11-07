#!/bin/bash
# Script para configurar el startup command del backend en Azure
# Ejecuta este script UNA VEZ desde Azure Cloud Shell

echo "🔧 Configurando startup command para ecoalerta-backend..."

# Configurar startup command directo (sin depender de startup.sh)
az webapp config set \
  --name ecoalerta-backend \
  --resource-group ecoalerta1 \
  --startup-file "bash -c 'python manage.py migrate --noinput && python manage.py collectstatic --noinput && exec gunicorn ecoalerta.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120 --access-logfile - --error-logfile -'"

echo "✅ Startup command configurado"
echo ""
echo "🔄 Reiniciando la aplicación..."
az webapp restart \
  --name ecoalerta-backend \
  --resource-group ecoalerta1

echo ""
echo "✅ ¡Listo! Espera 1-2 minutos y verifica los logs con:"
echo "   az webapp log tail --name ecoalerta-backend --resource-group ecoalerta1"

