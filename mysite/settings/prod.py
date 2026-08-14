"""
Production settings.

The database is opened read-only: this app serves fixed game data and never
writes at runtime. Data changes happen in development and ship in the image,
so an accidental write fails loudly instead of drifting.
"""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

# Admin cannot function against a read-only database (login writes
# last_login), so it is not routed at all.
ADMIN_ENABLED = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production.")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must be set in production.")

# as_uri() builds a correct file:// URI on any platform. Django always passes
# uri=True to sqlite3.connect, so mode=ro is honoured.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": (BASE_DIR / "db.sqlite3").as_uri() + "?mode=ro",  # noqa: F405
    }
}


# Static files
#
# Content-hashed filenames plus pre-compressed .gz variants, built by
# collectstatic during the image build and served by nginx.
#
# Deliberately not in base.py: this backend refuses to resolve a {% static %}
# URL unless collectstatic has produced staticfiles.json, and Django forces
# DEBUG=False while running tests, which disables the non-hashed fallback. Any
# test rendering a template with {% static %} would then fail on a clean
# checkout where collectstatic has never run.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Security
# https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# Requests arrive via the nginx reverse proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

# HTTPS-only settings. Enable once the deployment terminates TLS, otherwise
# SECURE_SSL_REDIRECT would redirect-loop a plain HTTP deployment.
if os.environ.get("DJANGO_SECURE_SSL") == "1":
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# Logging: stdout only, so the container runtime owns collection.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
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
        "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
