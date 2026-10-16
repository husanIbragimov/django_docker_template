from pathlib import Path

from environs import Env

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = Env()
# In Docker the vars come from compose `env_file`, so the file itself may not exist inside the container
ENV_FILE = BASE_DIR.parent / ".envs" / ".env"
if ENV_FILE.exists():
    env.read_env(str(ENV_FILE))
# Host-side overrides for running Django/Celery by hand against docker-compose.local.yml (localhost ports).
# Never mounted into containers, so it only takes effect outside Docker.
LOCAL_ENV_FILE = BASE_DIR.parent / ".envs" / ".env.local"
if LOCAL_ENV_FILE.exists():
    env.read_env(str(LOCAL_ENV_FILE), override=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost'])
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:8000'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['http://localhost:8000'])

SECRET_KEY = env.str('SECRET_KEY', 'django-insecure')
DEBUG = env.bool('DEBUG') == 'True'

KAFKA_SERVERS = env.str('KAFKA_SERVERS')

# TELEGRAM BOT ALERT
BOT_TOKEN = env.str('BOT_TOKEN')
ADMIN_CHAT_ID = env.str('ADMIN_CHAT_ID')
THREAD_ID = env.str('THREAD_ID')
PRODUCTION = env.str('PRODUCTION', 'False') == 'True'

CRONITOR_API_KEY = env.str("CRONITOR_API_KEY")
SENTRY_DSN = env.str("SENTRY_DSN")

# Base Redis URL without a DB index; cache.py and celery_conf.py append their own DB number
REDIS_URL = env.str("REDIS_URL", "redis://redis:6379").rstrip("/")

TITLE = env.str("TITLE", "Django Project API")
DESCRIPTION = env.str("DESCRIPTION", "Django Project API Documentation")
