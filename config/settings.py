"""
Configuración de Django para Tribuna.

Base de datos: por defecto SQLite (desarrollo). Para usar PostgreSQL,
comenta el bloque sqlite y descomenta el de postgres.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ⚠️ Cambiar en producción
SECRET_KEY = "django-insecure-tribuna-dev-key-cambiar-en-produccion"

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Librerías de API y JWT
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    # Apps del proyecto
    "tienda",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── Base de datos ─────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
    # Para PostgreSQL (como en la otra plataforma):
    # "default": {
    #     "ENGINE": "django.db.backends.postgresql",
    #     "NAME": "tribuna",
    #     "USER": "postgres",
    #     "PASSWORD": "admin",
    #     "HOST": "localhost",
    #     "PORT": "5432",
    # }
}

# Archivos de medios (fotos de camisetas subidas por importar_imagenes)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

# Internacionalización (Colombia)
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CSRF: la cookie debe ser accesible desde JS para las peticiones del carrito
CSRF_COOKIE_HTTPONLY = False

# El servidor de Vite (5173) hace proxy de /carrito hacia Django (8000):
# el navegador envía Origin: localhost:5173, así que hay que confiar en él.
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# ── React (SPA de Vite) ───────────────────────────────────────
# Mientras sea False, el sitio lo sirven las plantillas de Django.
# Al terminar la SPA (npm run build &&Flip a True), Django sirve
# frontend compilado y las plantillas se retiran.
SPA_ACTIVA = False
SPA_DIST = BASE_DIR / "static" / "spa"

# ── Configuración de Django REST Framework y JWT ──────────────
from datetime import timedelta

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ── CORS ──────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True
