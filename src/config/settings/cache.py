import sys

from .env import REDIS_URL

# manage.py test --parallel forks isolated worker processes that each get their own
# database, but they'd all share one real Redis instance for cache/throttle state,
# causing cross-worker test interference. Use an in-process cache under the test runner.
if "test" in sys.argv:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": f"{REDIS_URL}/1",
        }
    }
