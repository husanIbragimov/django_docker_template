import os

import cronitor.celery
from celery.schedules import crontab

from celery import Celery
from .settings.base import env

CRONITOR_API_KEY = env.str("CRONITOR_API_KEY", "secret")

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery monitoring (https://cronitor.io/)
cronitor.api_key = CRONITOR_API_KEY
cronitor.celery.initialize(app)
