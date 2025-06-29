from .apps import INSTALLED_APPS
from .env import DEBUG
from .middleware import MIDDLEWARE

if DEBUG:
    INSTALLED_APPS.append("silk")
    MIDDLEWARE.append("silk.middleware.SilkyMiddleware")
    INTERNAL_IPS = [
        "127.0.0.1",
        "0.0.0.0",
    ]
