"""
Django settings for Road_Audit_Project.

This file contains the configuration for:
1. Django applications
2. Database
3. Templates
4. Static files (CSS and JavaScript)
5. Media files (uploaded road images)
"""

import os
from pathlib import Path


# ==================================================
# 1. BASE DIRECTORY
# ==================================================

# Project root directory containing manage.py.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==================================================
# 2. SECURITY SETTINGS
# ==================================================

# IMPORTANT:
# Replace this placeholder with your EXISTING SECRET_KEY.
# Never publish your real secret key publicly.

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-replace-this-with-your-existing-secret-key"
)


# Enable debugging for local development.
# For production, configure the DEBUG environment variable as False.

DEBUG = os.environ.get("DEBUG", "True").lower() == "true"


# Hosts allowed to access the application.
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1"
    ).split(",")
    if host.strip()
]


# ==================================================
# 3. INSTALLED APPLICATIONS
# ==================================================

INSTALLED_APPS = [
    # Django built-in applications
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Your road audit application
    "Road_Audit_App",
]


# ==================================================
# 4. MIDDLEWARE
# ==================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==================================================
# 5. URL CONFIGURATION
# ==================================================

ROOT_URLCONF = "Road_Audit_Project.urls"


# ==================================================
# 6. TEMPLATE CONFIGURATION
# ==================================================

TEMPLATES = [
    {
        # Django template engine
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        # Project-level templates directory
        "DIRS": [
            BASE_DIR / "templates",
        ],

        # Search for templates inside installed applications
        "APP_DIRS": True,

        # Template context processors
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ==================================================
# 7. WSGI CONFIGURATION
# ==================================================

WSGI_APPLICATION = "Road_Audit_Project.wsgi.application"


# ==================================================
# 8. DATABASE CONFIGURATION
# ==================================================

# Use SQLite for the Road Audit System.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ==================================================
# 9. PASSWORD VALIDATION
# ==================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ==================================================
# 10. LANGUAGE AND TIME ZONE
# ==================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# ==================================================
# 11. STATIC FILE CONFIGURATION
# ==================================================

# URL used to access CSS, JavaScript, and other static files.
STATIC_URL = "/static/"


# Project-level static files directory.
# Your dashboard.css file should be inside static/css/.

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# Destination used by collectstatic during deployment.
# Do not place your source CSS files inside this directory.

STATIC_ROOT = BASE_DIR / "staticfiles"


# ==================================================
# 12. MEDIA FILE CONFIGURATION
# ==================================================

# URL used to access uploaded images.
MEDIA_URL = "/media/"


# Directory where uploaded road images are stored.
MEDIA_ROOT = BASE_DIR / "media"


# ==================================================
# 13. DEFAULT PRIMARY KEY
# ==================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==================================================
# 14. BASIC PRODUCTION SECURITY SETTINGS
# ==================================================

# Enable these cookie settings when HTTPS is configured in production.
# Do not enable secure cookies for ordinary local HTTP development.

if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True
