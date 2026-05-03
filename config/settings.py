from __future__ import annotations

import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost"],
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",
    "rest_framework",
    "django_celery_beat",

    "apps.chains",
    "apps.cofhe",

    # Zalary onboarding layer
    "apps.onboarding",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ── Database ──────────────────────────────────────────────────
if env("DB_ENGINE", default=""):
    DATABASES = {
        "default": {
            "ENGINE": env("DB_ENGINE", default="django.db.backends.postgresql"),
            "NAME": env("DB_NAME", default="zalary"),
            "USER": env("DB_USER", default="zalary"),
            "PASSWORD": env("DB_PASSWORD", default=""),
            "HOST": env("DB_HOST", default="postgres"),
            "PORT": env("DB_PORT", default="5432"),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {"connect_timeout": 10},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": env("SQLITE_PATH", default=str(BASE_DIR / "db.sqlite3")),
        }
    }

# ── Cache / Redis ─────────────────────────────────────────────
REDIS_URL = env("REDIS_URL", default="redis://127.0.0.1:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# ── REST Framework ────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

# ── CORS ──────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
)

CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=False)

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-api-key",
    "x-api-key",
    "x-csrftoken",
    "x-requested-with",
]

# ── Celery ────────────────────────────────────────────────────
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_TASK_ALWAYS_EAGER = False
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = env("TIME_ZONE", default="Africa/Lagos")

# ── Chain / contract settings ─────────────────────────────────
BASE_SEPOLIA_CHAIN_ID = int(env("BASE_SEPOLIA_CHAIN_ID", default="84532"))
BASE_SEPOLIA_RPC_URL = env("BASE_SEPOLIA_RPC_URL", default="https://sepolia.base.org")

USDC_ADDRESS = env("USDC_ADDRESS", default="")
CONFIDENTIALTOKEN_ADDRESS = env("CONFIDENTIALTOKEN_ADDRESS", default="")
PAYROLLVAULT_ADDRESS = env("PAYROLLVAULT_ADDRESS", default="")
SWAPROUTER_ADDRESS = env("SWAPROUTER_ADDRESS", default="")

CONFIRMATIONS_REQUIRED = int(env("CONFIRMATIONS_REQUIRED", default="3"))
FINALITY_RECHECK_DEPTH = int(env("FINALITY_RECHECK_DEPTH", default="200"))
REPLACEMENT_SCAN_BLOCKS = int(env("REPLACEMENT_SCAN_BLOCKS", default="200"))

# ── Viem worker ───────────────────────────────────────────────
VIEM_WORKER_URL = env("VIEM_WORKER_URL", default="http://127.0.0.1:8787")
VIEM_WORKER_TIMEOUT_SECONDS = int(env("VIEM_WORKER_TIMEOUT_SECONDS", default="45"))

# ── API key ───────────────────────────────────────────────────
API_KEY = env("API_KEY", default="dev-key" if DEBUG else "")

# ── Zalary onboarding settings ────────────────────────────────
ONBOARDING_TOKEN_MAX_AGE_SECONDS = int(
    env("ONBOARDING_TOKEN_MAX_AGE_SECONDS", default=str(60 * 60 * 24 * 7))
)

ONBOARDING_NONCE_TTL_SECONDS = int(
    env("ONBOARDING_NONCE_TTL_SECONDS", default=str(60 * 10))
)

ONBOARDING_EMAIL_CODE_TTL_SECONDS = int(
    env("ONBOARDING_EMAIL_CODE_TTL_SECONDS", default=str(60 * 15))
)

# ── Email settings ────────────────────────────────────────────
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@zalary.app")

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default=(
        "django.core.mail.backends.console.EmailBackend"
        if DEBUG
        else "django.core.mail.backends.smtp.EmailBackend"
    ),
)

EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = int(env("EMAIL_PORT", default="587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_TIMEOUT = int(env("EMAIL_TIMEOUT", default="20"))
FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="http://localhost:5173")
# ── Internationalisation ──────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="Africa/Lagos")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("LOG_LEVEL", default="INFO"),
    },
}