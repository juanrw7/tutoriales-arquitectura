from .settings import *
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
TIME_ZONE = "America/Bogota"
LANGUAGE_CODE = "es-co"

SECRET_KEY = "django-insecure-clave-solo-local-no-usar-en-aws"
DEBUG = True

del PAYMENTS_LOG_DIR
