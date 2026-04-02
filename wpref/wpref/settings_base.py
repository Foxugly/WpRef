from pathlib import Path

import environ
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, "django-insecure-dev-key-change-me"),
    ALLOWED_HOSTS=(list, ["*"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:4200", "http://127.0.0.1:4200"]),
    DEFAULT_FROM_EMAIL=(str, "no-reply@monapp.com"),
    EMAIL_BACKEND=(str, "django.core.mail.backends.console.EmailBackend"),
    EMAIL_HOST=(str, "smtp.office365.com"),
    EMAIL_PORT=(int, 587),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
    EMAIL_USE_TLS=(bool, True),
    FRONTEND_BASE_URL=(str, "http://127.0.0.1:4200"),
    PASSWORD_RESET_FRONTEND_PATH_PREFIX=(str, "/user/reset-password"),
    SQLITE_NAME=(str, "db.sqlite3"),
    MEDIA_ROOT_DIR=(str, "media"),
    DEEPL_IS_FREE=(bool, False),
    DATABASE_URL=(str, ""),
)
ENV_FILE = BASE_DIR / ".env"
environ.Env.read_env(str(ENV_FILE))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core.apps.CoreConfig",
    "rest_framework",
    "schema_viewer",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
    "django_extensions",
    "parler",
    "customuser.apps.CustomuserConfig",
    "subject.apps.SubjectConfig",
    "question.apps.QuestionConfig",
    "quiz.apps.QuizConfig",
    "domain.apps.DomainConfig",
    "language.apps.LanguageConfig",
    "translation.apps.TranslationConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "wpref.urls"
AUTH_USER_MODEL = "customuser.CustomUser"

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

WSGI_APPLICATION = "wpref.wsgi.application"
ASGI_APPLICATION = "wpref.asgi.application"

database_url = env("DATABASE_URL", default="").strip()
if database_url:
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / env("SQLITE_NAME"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGES = (
    ("en", _("English")),
    ("fr", _("French")),
    ("nl", _("Dutch")),
    ("it", _("Italy")),
    ("es", _("Spain")),
)

LANGUAGE_CODE = "en"
TIME_ZONE = "Europe/Brussels"
USE_I18N = True
USE_TZ = True

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "WpRef API",
    "VERSION": "1.0.0",
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": True},
    "ENUM_NAME_OVERRIDES": {
        "VisibilityEnum": "quiz.constants.VISIBILITY_CHOICES",
    },
    "COMPONENT_SPLIT_REQUEST": True,
}

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / env("MEDIA_ROOT_DIR")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
FRONTEND_BASE_URL = env("FRONTEND_BASE_URL").rstrip("/")
PASSWORD_RESET_FRONTEND_PATH_PREFIX = "/" + env("PASSWORD_RESET_FRONTEND_PATH_PREFIX").strip("/")

SENSITIVE_FIELDS = {
    "password",
    "password1",
    "password2",
    "old_password",
    "new_password",
    "token",
    "access",
    "refresh",
    "api_key",
    "secret",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

DEEPL_AUTH_KEY = env("DEEPL_AUTH_KEY", default="")
DEEPL_IS_FREE = env("DEEPL_IS_FREE")

PARLER_LANGUAGES = {
    None: tuple({"code": code} for code, _ in LANGUAGES),
    "default": {
        "fallbacks": ["fr"],
        "hide_untranslated": False,
    },
}

X_FRAME_OPTIONS = "DENY"
