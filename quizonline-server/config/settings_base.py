from copy import deepcopy
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
    MEDIA_ROOT_DIR=(str, "media"),
    USE_DEEPL=(bool, False),
    DEEPL_IS_FREE=(bool, False),
    DATABASE_URL=(str, ""),
    CELERY_BROKER_URL=(str, "redis://127.0.0.1:6379/0"),
    CELERY_RESULT_BACKEND=(str, "redis://127.0.0.1:6379/1"),
    CELERY_TASK_ALWAYS_EAGER=(bool, False),
    API_PAGE_SIZE=(int, 20),
    DATA_UPLOAD_MAX_MEMORY_SIZE=(int, 10 * 1024 * 1024),
    FILE_UPLOAD_MAX_MEMORY_SIZE=(int, 10 * 1024 * 1024),
    MAX_UPLOAD_FILE_SIZE=(int, 10 * 1024 * 1024),
)
ENV_FILE = BASE_DIR / ".env"
environ.Env.read_env(str(ENV_FILE))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
NAME_APP = "QuizOnline"

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
    "import_export",
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

ROOT_URLCONF = "config.urls"
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {"default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3")}

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
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": env("API_PAGE_SIZE"),
    "DEFAULT_THROTTLE_RATES": {
        "token_obtain": "5/min",
        "password_reset": "3/hour",
        "quiz_answer": "60/min",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": f"{NAME_APP} API",
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
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")
CELERY_TASK_ALWAYS_EAGER = env("CELERY_TASK_ALWAYS_EAGER")
CELERY_TASK_EAGER_PROPAGATES = True
DATA_UPLOAD_MAX_MEMORY_SIZE = env("DATA_UPLOAD_MAX_MEMORY_SIZE")
FILE_UPLOAD_MAX_MEMORY_SIZE = env("FILE_UPLOAD_MAX_MEMORY_SIZE")
MAX_UPLOAD_FILE_SIZE = env("MAX_UPLOAD_FILE_SIZE")

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

DEV_LOGGING = deepcopy(LOGGING)
DEV_LOGGING["root"]["level"] = "DEBUG"

PROD_LOGGING = deepcopy(LOGGING)
PROD_LOGGING["root"]["level"] = "INFO"

DEEPL_AUTH_KEY = env("DEEPL_AUTH_KEY", default="")
USE_DEEPL = env.bool("USE_DEEPL", default=False)
DEEPL_IS_FREE = env.bool("DEEPL_IS_FREE", default=True)

PARLER_LANGUAGES = {
    None: tuple({"code": code} for code, _ in LANGUAGES),
    "default": {
        "fallbacks": ["fr"],
        "hide_untranslated": False,
    },
}

X_FRAME_OPTIONS = "DENY"
