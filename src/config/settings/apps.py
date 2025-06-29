LOCAL_APPS = [
    "apps._auth",
    "apps.common",
    "apps.upload",
]

THIRD_PARTY_APPS = [
    "rest_framework_simplejwt.token_blacklist",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "django_json_widget",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

INSTALLED_APPS += LOCAL_APPS
INSTALLED_APPS += THIRD_PARTY_APPS
