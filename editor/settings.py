# editor/settings.py

"""
Django settings for editor project.

Przystosowane do publicznego repozytorium:
* brak twardo zakodowanych sekretów
* wartości wrażliwe pobierane z zmiennych środowiskowych
* bezpieczne domyślne ustawienia dla dev‑serwera
"""

from pathlib import Path
import os

# --- Ścieżki --------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Sekrety i tryb debug -----------------------------------------------
# Produkcja: ustaw DJANGO_SECRET_KEY w menedżerze sekretów / zmiennych środow.
# Dev: jeśli brak klucza, generujemy losowy (nie utrwalany na dysku).
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    from django.core.management.utils import get_random_secret_key

    SECRET_KEY = get_random_secret_key()
    # Ostrzeż, jeśli uruchamiamy w trybie debug‑off bez jawnego klucza
    if os.getenv("DJANGO_DEBUG", "1") in {"0", "false", "False"}:
        import warnings

        warnings.warn(
            "DJANGO_SECRET_KEY nie ustawiony! Generuję tymczasowy klucz. "
            "Ustaw DJANGO_SECRET_KEY dla środowiska produkcyjnego.",
            RuntimeWarning,
        )

# DEBUG pobieramy z env, domyślnie = 1 (development)
DEBUG = os.getenv("DJANGO_DEBUG", "1") in {"1", "true", "True"}

# --- Hosty ---------------------------------------------------------------
# Podaj w env jako listę oddzieloną przecinkami: "myapp.com,.mycorp.internal"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost"
    ).split(",")
    if host.strip()
]

# --- Aplikacje -----------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third‑party
    "leaflet",
    "tailwind",
    "theme",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    'widget_tweaks',
    # local
    "routes",
]

TAILWIND_APP_NAME = "theme"


# --- Middleware ----------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

APPEND_SLASH = True

ROOT_URLCONF = "editor.urls"

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

WSGI_APPLICATION = "editor.wsgi.application"

# --- Baza danych ---------------------------------------------------------
# Domyślnie SQLite (pliku w repo nie wersjonujemy). Produkcja: ustaw DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    try:
        import dj_database_url
    except ImportError as e:
        raise ImportError(
            "Ustawiono DATABASE_URL, ale brak pakietu dj-database-url. "
            "Dodaj go do requirements.txt lub usuń zmienną."
        ) from e

    DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --- Walidacja haseł -----------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- I18N / l10n ---------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Pliki statyczne i media -------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- Klucz główny modeli -------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework ----------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
     "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# --- Auth redirects ------------------------------------------------------
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "board_list_mine"
LOGOUT_REDIRECT_URL = "login"
