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
    'daphne',
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
    'django.contrib.gis',  # Enabled for PostGIS
    'rest_framework',
    'rest_framework_simplejwt',  # JWT authentication
    'drf_spectacular',  # API documentation
    'corsheaders',  # CORS support
    'whitenoise.runserver_nostatic',  # WhiteNoise para servir archivos estáticos
    'channels',
    'reportes',
    'axes',
    'simple_history',
])

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'ecoalerta.middleware.SecurityLabMiddleware',
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
ASGI_APPLICATION = "ecoalerta.asgi.application"

# Configuración de Channels (WebSockets)
_redis_url = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
_use_redis_channels = not DEBUG and _redis_url not in ('none', 'None', '', 'false')

if _use_redis_channels:
    try:
        import redis as _redis_test
        _r = _redis_test.from_url(_redis_url)
        _r.ping()
        CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels_redis.core.RedisChannelLayer",
                "CONFIG": {
                    "hosts": [_redis_url],
                },
            },
        }
    except Exception:
        CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels.layers.InMemoryChannelLayer"
            }
        }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        }
    }


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

USE_SQLITE_LOCAL = os.getenv('USE_SQLITE_LOCAL', 'false').lower() in ('1', 'true', 'yes')

db_sslmode = os.getenv('DB_SSLMODE', 'require').strip()

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'administrador'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'ecoalerta.postgres.database.azure.com'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': (
            {'sslmode': db_sslmode} if db_sslmode else {}
        ),
    }
}

if USE_SQLITE_LOCAL:
    DATABASES['default'] = {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
    SPATIALITE_LIBRARY_PATH = os.getenv(
        'SPATIALITE_LIBRARY_PATH',
        '/opt/homebrew/opt/libspatialite/lib/mod_spatialite.dylib'
    )


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

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Axes Configuration
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # horas
AXES_LOCKOUT_TEMPLATE = None # Usar JSON para API
AXES_LOCKOUT_URL = None
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]
AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'



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
        'rest_framework.permissions.IsAuthenticated',  # Cambiar a autenticación requerida por defecto
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'reportes.exceptions.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10000/minute',  # General read API (deshabilitado temporalmente)
        'user': '10000/minute',  # General read API (deshabilitado temporalmente)
        'report_submission_anon': '10000/hour',   # Strict submission limit (deshabilitado temporalmente)
        'report_submission_pro': '10000/hour',   # Auth submission limit (deshabilitado temporalmente)
    },
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

# Permitir todos los orígenes solo si se habilita explícitamente en desarrollo
CORS_ALLOW_ALL_ORIGINS = DEBUG and os.getenv('CORS_ALLOW_ALL', 'False').lower() in ('1', 'true', 'yes')
CORS_ALLOW_CREDENTIALS = True

# Configuración adicional de CORS
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

# DRF maneja CSRF por autenticación (por ejemplo SessionAuthentication)
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()
if azure_frontend_url:
    CSRF_TRUSTED_ORIGINS.append(azure_frontend_url)

# WhiteNoise configuration para servir archivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Custom user model
AUTH_USER_MODEL = 'reportes.Usuario'

# Configuración de seguridad base
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = not DEBUG
USE_X_FORWARDED_PORT = not DEBUG
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() in ('1', 'true', 'yes')
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() in ('1', 'true', 'yes')
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'False').lower() in ('1', 'true', 'yes')
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# APPEND_SLASH desactivado para evitar redirecciones en API
# Las URLs de API deben manejarse explícitamente sin redirecciones
APPEND_SLASH = False

# Desactivar redirecciones automáticas para evitar problemas en Azure
PREPEND_WWW = False

# JWT Configuration
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# API Documentation (drf-spectacular)
SPECTACULAR_SETTINGS = {
    'TITLE': 'EcoAlerta API',
    'DESCRIPTION': 'API para gestión de reportes ambientales',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# Caché Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'ecoalerta',
        'TIMEOUT': 300,  # 5 minutos por defecto
    }
}

# Si Redis no está disponible, usar caché en memoria
try:
    import redis
    r = redis.from_url(os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'))
    r.ping()
except Exception:
    CACHES['default'] = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }

# Logging Configuration
LOGGING_DIR = BASE_DIR / 'logs'
LOGGING_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOGGING_DIR / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'reportes': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Configuración de Email
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@ecoalerta.cl')

# Configuración de Celery
# Configuración de Celery
if DEBUG:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'db+sqlite:///results.sqlite'
else:
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0'))
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0'))

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutos
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True

# Configuración de Celery Beat (tareas programadas)
from reportes.celerybeat_schedule import CELERY_BEAT_SCHEDULE
CELERY_BEAT_SCHEDULE = CELERY_BEAT_SCHEDULE

# Validación de variables de entorno críticas en producción
if not DEBUG:
    required_env_vars = ['SECRET_KEY', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(
            f"Variables de entorno faltantes en producción: {', '.join(missing_vars)}"
        )
    
    # Validar que SECRET_KEY no sea el valor por defecto
    if SECRET_KEY == 'django-insecure-eccalerta-dev-key-change-in-production':
        raise ValueError(
            "SECRET_KEY debe ser cambiado en producción. "
            "No uses el valor por defecto."
        )
