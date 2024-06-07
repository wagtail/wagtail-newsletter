import os

from pathlib import Path

import dj_database_url


PROJECT_DIR = Path(__file__).resolve().parent
BASE_DIR = PROJECT_DIR.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "not-a-secure-key"  # noqa: S105

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost"]

INSTALLED_APPS = [
    "wagtail_newsletter",
    "demo",
    "wagtail.contrib.search_promotions",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail.api.v2",
    "wagtail.contrib.routable_page",
    "wagtail.contrib.styleguide",
    "wagtail.sites",
    "wagtail",
    "taggit",
    "rest_framework",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "demo.urls"

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
            ]
        },
    }
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache",
    }
}

# don't use the intentionally slow default password hasher
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{PROJECT_DIR / 'db.sqlite3'}",
    ),
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
STATIC_ROOT = PROJECT_DIR / "static_root"
STATIC_URL = "/static/"

MEDIA_ROOT = PROJECT_DIR / "media_root"
MEDIA_URL = "/media/"

WAGTAILADMIN_BASE_URL = "http://localhost:8000"
WAGTAIL_SITE_NAME = "Wagtail Newsletter demo site"
WAGTAIL_GRAVATAR_PROVIDER_URL = None

WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY = os.environ.get(
    "WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY"
)
WAGTAIL_NEWSLETTER_RECIPIENTS_MODEL = "demo.CustomRecipients"
WAGTAIL_NEWSLETTER_FROM_NAME = os.environ.get("WAGTAIL_NEWSLETTER_FROM_NAME")
WAGTAIL_NEWSLETTER_REPLY_TO = os.environ.get("WAGTAIL_NEWSLETTER_REPLY_TO")
