"""
Development settings. Not suitable for production.

This is the default used by manage.py, the ASGI/WSGI entrypoints and pytest,
so local workflows (runserver, the scraper, admin, tests) behave as before.
"""

from .base import *  # noqa: F403

# SECURITY WARNING: this key is public and for local use only.
SECRET_KEY = "django-insecure-2(e-cp4cr8-@w9exf#kq&8rr*z^-=kvu3&fmmm%%r!86*(wt_+"

DEBUG = True

ALLOWED_HOSTS = ["*"]

# django_extensions is a development tool and is deliberately not installed in
# production.
INSTALLED_APPS = INSTALLED_APPS + ["django_extensions"]  # noqa: F405

# Read-write, so the scraper, migrations and admin all work locally.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
