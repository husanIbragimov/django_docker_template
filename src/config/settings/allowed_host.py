import os

from .env import ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS, DEBUG

ALLOWED_HOSTS = ALLOWED_HOSTS if not DEBUG else ["*"]


CORS_ALLOW_CREDENTIALS = False

if DEBUG:
    CORS_ORIGIN_ALLOW_ALL = True
else:
    CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS

CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS
