import os
from logging.handlers import TimedRotatingFileHandler

from .env import BASE_DIR

LOG_LEVEL = "ERROR"

logs_path = os.path.join(BASE_DIR.parent, "logs")
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
        "telegrambot_alert": {
            "level": LOG_LEVEL,
            "class": "apps.logger.handlers.TelegramBotAlertHandler",
            "formatter": "verbose",
        },
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
        "external_service_file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "filename": f"{logs_path}/external_service_error.log",
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
            "level": "DEBUG",
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
            "handlers": ["celery_log_file", "console", "telegrambot_alert"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        # -- Error logger
        "error_request_logger": {
            "handlers": ["error_log_file", "console", "telegrambot_alert"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "kafka_logger": {
            "handlers": ["console", "telegrambot_alert", "kafka_log"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "external_service_logger": {
            "handlers": ["external_service_file", "console", "telegrambot_alert"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
