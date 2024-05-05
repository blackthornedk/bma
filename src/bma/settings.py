"""Django settings for bma project.

Generated by 'django-admin startproject' using Django 3.2.13.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
from pathlib import Path

import django_stubs_ext

from .environment_settings import *  # noqa: F403

# intialise django_stubs_ext
django_stubs_ext.monkeypatch()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.postgres",
    "django.contrib.humanize",
    # deps
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "taggit",
    "django_bootstrap5",
    "fontawesomefree",
    "polymorphic",
    "ninja",
    "django_htmx",
    "oauth2_provider",
    "guardian",
    "corsheaders",
    "django_filters",
    "django_tables2",
    # bma apps
    "bornhack_allauth_provider",
    "users",
    "utils",
    "files",
    "pictures",
    "videos",
    "audios",
    "documents",
    "frontpage",
    "albums",
    "widgets",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "utils.middleware.ExemptOauthFromCSRFMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "dealer.contrib.django.Middleware",
    "django_htmx.middleware.HtmxMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    "oauth2_provider.backends.OAuth2Backend",
    "guardian.backends.ObjectPermissionBackend",
]

ROOT_URLCONF = "bma.urls"

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
                "dealer.contrib.django.context_processor",
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = "bma.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Copenhagen"

USE_I18N = True

USE_L10N = False

USE_TZ = True

SHORT_DATE_FORMAT = "Ymd"
DATE_FORMAT = "l, M jS, Y"
DATETIME_FORMAT = "l, M jS, Y, H:i (e)"
TIME_FORMAT = "H:i"


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATICFILES_DIRS = [BASE_DIR / "static_src"]  # find static files below here
STATIC_ROOT = BASE_DIR / "static"  # collect all static files here
STATIC_URL = "static/"  # serve the static files here

MEDIA_URL = "media/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# avoid socialaccount_state bug / session cookie name conflicts
SESSION_COOKIE_NAME = "bma_sessionid"
SITE_ID = 1
LOGIN_REDIRECT_URL = "/"
AUTH_USER_MODEL = "users.User"
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_USER_MODEL_EMAIL_FIELD = None
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_ADAPTER = "users.adapter.NoNewUsersAccountAdapter"
SOCIALACCOUNT_ADAPTER = "bornhack_allauth_provider.adapters.BornHackSocialAccountAdapter"
TAGGIT_CASE_INSENSITIVE = True
IMAGEKIT_USE_MEMCACHED_SAFE_CACHE_KEY = False
GALLERY_MANAGER_DEFAULT_PAGINATE_COUNT = 20

X_FRAME_OPTIONS = "SAMEORIGIN"

# https://docs.djangoproject.com/en/4.1/topics/logging/
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "formatters": {
        "syslog": {"format": "%(levelname)s %(name)s.%(funcName)s(): %(message)s"},
        "console": {
            "format": "[%(asctime)s] %(name)s.%(funcName)s() %(levelname)s %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": DJANGO_LOG_LEVEL,  # noqa: F405
            "propagate": False,
        },
        "bma": {
            "handlers": ["console"],
            "level": BMA_LOG_LEVEL,  # noqa: F405
            "propagate": False,
        },
    },
}

GUARDIAN_GET_CONTENT_TYPE = "polymorphic.contrib.guardian.get_polymorphic_base_content_type"

# django-imagekit settings
IMAGEKIT_CACHEFILE_DIR = ""
IMAGEKIT_SPEC_CACHEFILE_NAMER = "imagekit.cachefiles.namers.source_name_dot_hash"

# save csrf tokens in session instead of using double cookie to ease api scripting
CSRF_USE_SESSIONS = True
CSRF_COOKIE_SECURE = not DEBUG  # noqa: F405
SESSION_COOKIE_SECURE = not DEBUG  # noqa: F405

if DEBUG:  # noqa: F405
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
    INTERNAL_IPS = [
        "127.0.0.1",
    ]

DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap5.html"

BOOTSTRAP5 = {
    "css_url": {
        "url": "/static/css/vendor/bootstrap-v5.2.3.min.css",
        "integrity": "sha384-rbsA2VBKQhggwzxH7pPCaAqO46MgnOM80zW1RWuH61DGLwZJEdK2Kadq2F9CUG65",
        "crossorigin": "anonymous",
    },
    "javascript_url": {
        "url": "/static/js/vendor/bootstrap-v5.2.3.min.js",
        "integrity": "sha384-kenU1KFdBIe4zVF0s0G1M5b4hcpxyD9F7jL+jjXkk+Q2h455rYXK/7HAuoJl+0I4",
        "crossorigin": "anonymous",
    },
}
