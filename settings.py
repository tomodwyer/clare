from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "not-secret"
DEBUG = True
ALLOWED_HOSTS = ["*"]

ROOT_URLCONF = "urls"
WSGI_APPLICATION = "wsgi.application"

INSTALLED_APPS = [
    "django.contrib.staticfiles",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
    },
]

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
