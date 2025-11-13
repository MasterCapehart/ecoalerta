"""
Django settings for ecoalerta project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-eccalerta-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# NO usar django.contrib.gis - causa errores con GDAL en Azure
# Agregar el resto de las apps
INSTALLED_APPS.extend([
    'rest_framework',
    'corsheaders',  # CORS support
    'whitenoise.runserver_nostatic',  # WhiteNoise para servir archivos estáticos
    'reportes',
])

MIDDLEWARE = [
    # SecurityMiddleware DESACTIVADO completamente - está causando bucles de redirección
    # 'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'ecoalerta.middleware.DisableCSRFForAPI',  # Desactivar CSRF para API
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # CommonMiddleware DESACTIVADO temporalmente - está causando redirecciones 301
    # 'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'ecoalerta.middleware.PreventRedirectsMiddleware',  # Prevenir redirecciones en API (ÚLTIMO - intercepta después de todos)
]

ROOT_URLCONF = 'ecoalerta.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecoalerta.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Azure PostgreSQL - Usando PostgreSQL estándar (NO PostGIS)
# IMPORTANTE: Forzar ENGINE explícitamente como PostgreSQL estándar
# Aunque instalamos GDAL/GEOS, NO usamos PostGIS para evitar problemas
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # PostgreSQL estándar, NO PostGIS
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'administrador'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'Ecoalerta1'),
        'HOST': os.getenv('DB_HOST', 'ecoalerta.postgres.database.azure.com'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',  # Azure requiere SSL
        },
    }
}

# Validar que el ENGINE sea correcto (forzar PostgreSQL estándar)
if DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
    # Si por alguna razón el ENGINE no es PostgreSQL estándar, forzarlo
    print(f"⚠️ ADVERTENCIA: ENGINE no es PostgreSQL estándar: {DATABASES['default']['ENGINE']}")
    print("   Forzando a django.db.backends.postgresql")
    DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'es-es'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    # Desactivar autenticación por defecto para API pública
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',  # Vite dev server
    'http://127.0.0.1:5173',
    'https://calm-water-08ac6120f.3.azurestaticapps.net',  # Frontend en Azure Static Web Apps
]

# Agregar orígenes de Azure desde variables de entorno
azure_frontend_url = os.getenv('AZURE_FRONTEND_URL', '')
if azure_frontend_url:
    CORS_ALLOWED_ORIGINS.append(azure_frontend_url)

# Permitir todos los orígenes de Azure Static Web Apps (temporal para debugging)
CORS_ALLOW_ALL_ORIGINS = False  # Mantener False para seguridad
CORS_ALLOW_CREDENTIALS = True

# Configuración adicional de CORS para evitar problemas
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Desactivar CSRF para API endpoints (Django REST Framework maneja esto)
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()
if azure_frontend_url:
    CSRF_TRUSTED_ORIGINS.append(azure_frontend_url)

# WhiteNoise configuration para servir archivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Custom user model
AUTH_USER_MODEL = 'reportes.Usuario'

# GDAL/GEOS NO configurado - no usar PostGIS por ahora
# Se eliminó toda configuración de GDAL para evitar errores de importación

# Configuración de seguridad para producción
# Azure App Service maneja HTTPS a través de un proxy inverso
# NO redirigir a HTTPS porque Azure ya lo maneja y puede causar bucles
SECURE_SSL_REDIRECT = False

# IMPORTANTE: Desactivar todas las redirecciones relacionadas con SSL/HTTPS
# Azure App Service ya maneja HTTPS, no necesitamos que Django redirija
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Configuración de proxy headers para Azure App Service
# DESACTIVADO completamente - sin SecurityMiddleware no son necesarios y pueden causar problemas
# USE_X_FORWARDED_HOST = True
# USE_X_FORWARDED_PORT = True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Desactivar completamente las redirecciones de seguridad
# Esto evita que SecurityMiddleware redirija requests
FORCE_SCRIPT_NAME = None

# APPEND_SLASH desactivado para evitar redirecciones en API
# Las URLs de API deben manejarse explícitamente sin redirecciones
APPEND_SLASH = False

# Desactivar redirecciones automáticas para evitar problemas en Azure
PREPEND_WWW = False

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
