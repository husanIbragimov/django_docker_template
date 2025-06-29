from pathlib import Path

from environs import Env

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = Env()
env.read_env(f"{BASE_DIR.parent}/.envs/.env")

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

TITLE = env.str("TITLE", "Django Project API")
DESCRIPTION = env.str("DESCRIPTION", "Django Project API Documentation")
