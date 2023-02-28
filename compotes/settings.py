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
else:  # pragma: no cover
    SECRET_KEY = os.environ["SECRET_KEY"]

DOMAIN_NAME = os.environ.get("DOMAIN_NAME", "localhost")
HOSTNAME = os.environ.get("ALLOWED_HOST", f"{PROJECT}.{DOMAIN_NAME}")
ALLOWED_HOSTS = [HOSTNAME, f"{HOSTNAME}:8000"]
CSRF_TRUSTED_ORIGINS = [
    ("http://" if DEBUG else "https://") + host for host in ALLOWED_HOSTS
]

# Application definition

INSTALLED_APPS = [
    PROJECT,
    "actions",
    "ndh",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django_bootstrap5",
    "django_tables2",
    "django_filters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
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
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = f"{PROJECT}.wsgi.application"

# Database

DB = os.environ.get("DB", "db.sqlite3")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / DB,
    }
}
if DB == "postgres":  # pragma: no cover
    DATABASES["default"].update(
        ENGINE="django.db.backends.postgresql",
        NAME=os.environ.get("POSTGRES_DB", DB),
        USER=os.environ.get("POSTGRES_USER", DB),
        HOST=os.environ.get("POSTGRES_HOST", DB),
        PASSWORD=os.environ["POSTGRES_PASSWORD"],
    )

# Password validation

_APV = "django.contrib.auth.password_validation"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": f"{_APV}.UserAttributeSimilarityValidator",
    },
    {
        "NAME": f"{_APV}.MinimumLengthValidator",
    },
    {
        "NAME": f"{_APV}.CommonPasswordValidator",
    },
    {
        "NAME": f"{_APV}.NumericPasswordValidator",
    },
]

# Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)

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

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = f"{PROJECT}.User"

AUTHENTICATION_BACKENDS = ["yeouia.backends.YummyEmailOrUsernameInsensitiveAuth"]

SITE_ID = 1
