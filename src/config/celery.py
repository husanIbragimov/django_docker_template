import os

import cronitor.celery
from celery import Celery
from celery.schedules import crontab

from .settings.env import CRONITOR_API_KEY

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Celery monitoring (https://cronitor.io/)
cronitor.api_key = CRONITOR_API_KEY
cronitor.celery.initialize(app)
