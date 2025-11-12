"""
Script de prueba para verificar que el middleware se está ejecutando
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecoalerta.settings')
django.setup()

from django.test import RequestFactory
from django.http import HttpResponse
from ecoalerta.middleware import PreventRedirectsMiddleware

# Crear un request de prueba
factory = RequestFactory()
request = factory.get('/api/auth/login/')

# Crear una respuesta de redirección simulada
response = HttpResponse(status=301)
response['Location'] = 'https://ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net/api/auth/login/'

# Probar el middleware
middleware = PreventRedirectsMiddleware(get_response=lambda req: response)
result = middleware.process_response(request, response)

print(f"Status code original: {response.status_code}")
print(f"Status code después del middleware: {result.status_code}")
print(f"Content type: {result.get('Content-Type', 'N/A')}")

if result.status_code == 500:
    print("✅ Middleware está interceptando la redirección correctamente")
else:
    print("❌ Middleware NO está interceptando la redirección")

