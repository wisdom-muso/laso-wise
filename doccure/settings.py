from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Use environment variables with fallbacks
SECRET_KEY = os.getenv("SECRET_KEY", "g!y0otek@9t^b+b*7)&q2a5^=8_9&xcdii8@6h^_*wphl-(fu9")

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# CSRF settings
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
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
    "ckeditor",
    "whitenoise.runserver_nostatic",  # For serving static files in development
    
    # Project apps
    "core",
    "accounts",
    "doctors",
    "patients",
    "bookings",
]

# Django Unfold settings
UNFOLD = {
    "SITE_TITLE": "Laso Digital Health",
    "SITE_HEADER": "Laso Digital Health",
    "SITE_SYMBOL": "settings",  # Symbol from icon set
    "ENVIRONMENT": "Development",
    "THEME": {
        "COLORS": {
            "primary": {
                "50": "178 245 243",  # #b2f5f3 (accent)
                "100": "178 245 243",  # #b2f5f3 (accent)
                "200": "178 245 243",  # #b2f5f3 (accent)
                "300": "26 162 160",   # #1a9e9c (accent dark)
                "400": "18 186 184",   # #12bab8 (primary)
                "500": "18 186 184",   # #12bab8 (primary)
                "600": "14 138 136",   # #0e8a88 (primary hover)
                "700": "14 138 136",   # #0e8a88 (secondary)
                "800": "10 110 108",   # #0a6e6c (secondary dark)
                "900": "10 110 108",   # #0a6e6c (secondary dark)
                "950": "10 110 108",   # #0a6e6c (secondary dark)
            },
            "gray": {
                "50": "243 244 246",   # #f3f4f6 (muted)
                "100": "243 244 246",  # #f3f4f6 (muted)
                "200": "229 231 235",  # #e5e7eb (sidebar border)
                "300": "209 213 219",  # #d1d5db
                "400": "156 163 175",  # #9ca3af (muted dark foreground)
                "500": "107 114 128",  # #6b7280 (muted foreground)
                "600": "75 85 99",     # #4b5563
                "700": "55 65 81",     # #374151 (muted dark)
                "800": "31 41 55",     # #1f2937 (sidebar dark)
                "900": "17 24 39",     # #111827
                "950": "3 7 18",       # #030712
            },
        },
        "ROUNDED": {
            "DEFAULT": "0.5rem",       # 8px (base radius)
            "sm": "0.25rem",           # 4px (small radius)
            "md": "0.375rem",          # 6px (medium radius)
            "lg": "0.5rem",            # 8px (large radius)
            "xl": "0.75rem",           # 12px
            "2xl": "1rem",             # 16px
            "3xl": "1.5rem",           # 24px
            "full": "9999px",          # Fully rounded (for badges)
        },
    },
    "STYLESHEETS": [
        "css/laso-theme.css",
    ],
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "doccure.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "doccure.wsgi.application"

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

# Use appropriate static files storage based on environment
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_ROOT = BASE_DIR / "media"

AUTH_USER_MODEL = "accounts.User"

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
