SECRET_KEY = "test-secret-key-for-django-hrid"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "tests.test_app",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Optional HRID settings
# DJANGO_HRID_ELEMENTS = ('adjective', 'noun', 'verb')
# DJANGO_HRID_DELIMITER = '-'
# DJANGO_HRID_SCRAMBLE = True
