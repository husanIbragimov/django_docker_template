from .env import REDIS_URL

# Redis is the only message broker; DB 0 is reserved for Celery, DB 1 for the Django cache (see cache.py).
CELERY_BROKER_URL = f"{REDIS_URL}/0"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
