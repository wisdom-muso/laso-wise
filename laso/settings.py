from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Use environment variables with fallbacks
SECRET_KEY = os.getenv("SECRET_KEY", "g!y0otek@9t^b+b*7)&q2a5^=8_9&xcdii8@6h^_*wphl-(fu9")

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,65.108.91.110").split(",")

# CSRF settings
csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "https://work-1-dwrrnobogrrhzpma.prod-runtime.all-hands.dev,https://work-2-dwrrnobogrrhzpma.prod-runtime.all-hands.dev,http://65.108.91.110:12000")
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins.split(",") if origin.strip()]

# For development, disable secure cookies if DEBUG is True
if DEBUG:
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
else:
    CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "True").lower() in ("true", "1", "t")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True").lower() in ("true", "1", "t")

INSTALLED_APPS = [
    # Django Unfold admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Third-party apps
    "debug_toolbar",
    "rest_framework",
    "rest_framework.authtoken",
    "channels",
    "corsheaders",
    "ckeditor",
    "whitenoise.runserver_nostatic",  # For serving static files in development
    
    # Project apps
    "core.apps.CoreConfig",
    "accounts",
    "doctors",
    "patients",
    "bookings",
    "mobile_clinic",
    "vitals",
    "dashboard",
    "sync_monitor",
    "telemedicine",  # New telemedicine app
]

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Channels settings for WebSocket support
ASGI_APPLICATION = 'laso.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Django Unfold settings
UNFOLD = {
    "SITE_TITLE": "Laso Digital Health",
    "SITE_HEADER": "Laso Digital Health",
    "SITE_SYMBOL": "settings",  # Symbol from icon set
    "ENVIRONMENT": "Development",
    "COLORS": {
        "primary": {
            "50": "240 253 250",   # #f0fdfa (teal-50)
            "100": "204 251 241",  # #ccfbf1 (teal-100)
            "200": "153 246 228",  # #99f6e4 (teal-200)
            "300": "94 234 212",   # #5eead4 (teal-300)
            "400": "45 212 191",   # #2dd4bf (teal-400)
            "500": "20 184 166",   # #14b8a6 (teal-500)
            "600": "13 148 136",   # #0d9488 (teal-600)
            "700": "15 118 110",   # #0f766e (teal-700)
            "800": "17 94 89",     # #115e59 (teal-800)
            "900": "19 78 74",     # #134e4a (teal-900)
            "950": "4 47 46",      # #042f2e (teal-950)
        },
        "gray": {
            "50": "249 250 251",   # #f9fafb (gray-50)
            "100": "243 244 246",  # #f3f4f6 (gray-100)
            "200": "229 231 235",  # #e5e7eb (gray-200)
            "300": "209 213 219",  # #d1d5db (gray-300)
            "400": "156 163 175",  # #9ca3af (gray-400)
            "500": "107 114 128",  # #6b7280 (gray-500)
            "600": "75 85 99",     # #4b5563 (gray-600)
            "700": "55 65 81",     # #374151 (gray-700)
            "800": "31 41 55",     # #1f2937 (gray-800)
            "900": "17 24 39",     # #111827 (gray-900)
            "950": "3 7 18",       # #030712 (gray-950)
        },
    },
    "STYLESHEETS": [
        "css/laso-theme.css",
        "css/modern-design-system.css",
        "css/admin-modern.css",
    ],
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "laso.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.currency_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "laso.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"

# Optimize static files handling
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Use whitenoise storage without compression to avoid source map issues
STATICFILES_STORAGE = 'whitenoise.storage.StaticFilesStorage'

# Whitenoise configuration
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

MEDIA_ROOT = BASE_DIR / "media"

AUTH_USER_MODEL = "accounts.User"

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Authentication Configuration
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'

INTERNAL_IPS = [
    "127.0.0.1",
]

TIME_INPUT_FORMATS = [
    "%I:%M %p",
]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# CKEditor Configuration
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"
CKEDITOR_JQUERY_URL = (
    "//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"
)

CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "full",
        "height": 300,
        "width": "100%",
        "extraPlugins": ",".join(
            ["widget", "dialog", "dialogui", "codesnippet"]
        ),
    },
}

CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"
DEBUG_TOOLBAR_CONFIG = {
    "IS_RUNNING_TESTS": False,
}

# Django Admin Customization
ADMIN_SITE_HEADER = "Laso Digital Health Administration"
ADMIN_SITE_TITLE = "Laso Digital Health Admin Portal"
ADMIN_INDEX_TITLE = "Welcome to Laso Digital Health Admin Portal"

# Telemedicine Configuration
TELEMEDICINE_CONFIG = {
    'ZOOM_API_KEY': os.getenv('ZOOM_API_KEY', ''),
    'ZOOM_API_SECRET': os.getenv('ZOOM_API_SECRET', ''),
    'GOOGLE_MEET_CLIENT_ID': os.getenv('GOOGLE_MEET_CLIENT_ID', ''),
    'GOOGLE_MEET_CLIENT_SECRET': os.getenv('GOOGLE_MEET_CLIENT_SECRET', ''),
    'JITSI_DOMAIN': os.getenv('JITSI_DOMAIN', 'meet.jit.si'),
    'RECORDING_ENABLED': os.getenv('RECORDING_ENABLED', 'True').lower() in ('true', '1', 't'),
    'MAX_CONSULTATION_DURATION': int(os.getenv('MAX_CONSULTATION_DURATION', '60')),  # minutes
}

# CORS settings for React frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # React dev server
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # React production server
    "http://127.0.0.1:3000",
    "http://65.108.91.110:3000",  # Production React frontend
    "http://65.108.91.110:12000",  # Production nginx
    "http://65.108.91.110:8005",  # Production Django
]

CORS_ALLOW_CREDENTIALS = True

# WebSocket CORS settings
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only for development
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
