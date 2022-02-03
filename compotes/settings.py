"""Django settings for compotes project."""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

PROJECT = "compotes"
PROJECT_VERBOSE = PROJECT.capitalize()

DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
if DEBUG:
    SECRET_KEY = "django-insecure-un&^-yd2(xdo#_@or@obzh)trtweg))^oegpor8@=$srjplaz1"
else:
    SECRET_KEY = os.environ["SECRET_KEY"]

DOMAIN_NAME = os.environ.get("DOMAIN_NAME", "localhost")
HOSTNAME = os.environ.get("ALLOWED_HOST", f"{PROJECT}.{DOMAIN_NAME}")
ALLOWED_HOSTS = [HOSTNAME, f"{HOSTNAME}:8000"]
CSRF_TRUSTED_ORIGINS = [
    "http://" if DEBUG else "https://" + host for host in ALLOWED_HOSTS
]

# Application definition

INSTALLED_APPS = [
    PROJECT,
    "ndh",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_bootstrap5",
    "django_tables2",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = f"{PROJECT}.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = f"{PROJECT}.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DB = os.environ.get("DB", "db.sqlite3")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / DB,
    }
}
if DB == "postgres":
    DATABASES["default"].update(
        ENGINE="django.db.backends.postgresql",
        NAME=os.environ.get("POSTGRES_DB", DB),
        USER=os.environ.get("POSTGRES_USER", DB),
        HOST=os.environ.get("POSTGRES_HOST", DB),
        PASSWORD=os.environ["POSTGRES_PASSWORD"],
    )

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

VAL = "django.contrib.auth.password_validation"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": f"{VAL}.UserAttributeSimilarityValidator",
    },
    {
        "NAME": f"{VAL}.MinimumLengthValidator",
    },
    {
        "NAME": f"{VAL}.CommonPasswordValidator",
    },
    {
        "NAME": f"{VAL}.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

MEDIA_ROOT = f"/srv/{PROJECT}/media/"
MEDIA_URL = "/media/"
STATIC_URL = "/static/"
STATIC_ROOT = f"/srv/{PROJECT}/static/"
LOGIN_REDIRECT_URL = "/"

EMAIL_USE_SSL = True
EMAIL_PORT = 465
EMAIL_HOST = "mail.gandi.net"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", f"majo@{DOMAIN_NAME}")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", None)
DEFAULT_FROM_EMAIL = f"{PROJECT_VERBOSE} <{EMAIL_HOST_USER}>"
SERVER_EMAIL = f"Server {DEFAULT_FROM_EMAIL}"
REPLY_TO = f"webmaster@{DOMAIN_NAME}"
ADMINS = [(f"{PROJECT_VERBOSE} Webmasters", f"webmaster@{DOMAIN_NAME}")]

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = f"{PROJECT}.User"

AUTHENTICATION_BACKENDS = ["yeouia.backends.YummyEmailOrUsernameInsensitiveAuth"]
