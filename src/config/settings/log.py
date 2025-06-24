import os
from logging.handlers import TimedRotatingFileHandler

from django.conf import settings

LOG_LEVEL = "ERROR"

logs_path = os.path.join(settings.BASE_DIR.parent, "logs")
if not os.path.exists(logs_path):
    os.makedirs(logs_path)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {pathname}:{lineno} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        # -- telegram bot handler
        # 'telegrambot_alert': {
        #     'level': LOG_LEVEL,
        #     'class': 'logger.handlers.telegram_alert_handler.TelegramBotAlertHandler',
        #     'formatter': 'verbose',
        # },
        # TODO: add telegram bot handler
        # -- error log handler
        "error_log_file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "filename": f"{logs_path}/error.log",
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        # -- celery log handler
        "celery_log_file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "filename": f"{logs_path}/celery.log",
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        # Console handler
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        # -- kafka log handler
        "kafka_log": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "filename": f"{logs_path}/kafka.log",
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        # -- Django default logger
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        # -- Celery logger
        "celery_logger": {
            "handlers": ["celery_log_file", "console"],  # telegrambot_alert
            "level": LOG_LEVEL,
            "propagate": False,
        },
        # -- Error logger
        "error_request_logger": {
            "handlers": ["error_log_file"],  # telegrambot_alert
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "kafka_logger": {
            "handlers": ["console", "kafka_log"],  # telegrambot_alert
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
