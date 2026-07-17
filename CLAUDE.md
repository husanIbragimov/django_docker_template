# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A modular, Docker-first Django + DRF backend template. Core stack: Django 5.2, Django REST Framework, SimpleJWT auth, Celery (Redis/RabbitMQ broker), PostgreSQL, drf-spectacular (Swagger docs), Sentry, and Telegram-based exception alerting.

All Django code lives under `src/`; `manage.py` and app code are rooted there, not at the repo root.

## Environment setup

Env vars are read from `.envs/.env` (see `src/config/settings/env.py`, which loads `f"{BASE_DIR.parent}/.envs/.env"`). Set up local env files before running anything:

```bash
cp .envs/.env.example .envs/.env
cp .envs/.env.local.example .envs/.env.local
```

Required vars include `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `KAFKA_SERVERS`, `BOT_TOKEN`/`ADMIN_CHAT_ID`/`THREAD_ID` (Telegram alerts), `CRONITOR_API_KEY`, `SENTRY_DSN`, plus Postgres/RabbitMQ credentials used by `docker-compose.yml`.

## Common commands

Everything runs through Docker Compose, driven from the `Makefile` (each target `cd`s into `docker/` and passes `--env-file ../.envs/.env`):

```bash
make build          # build images and start stack (docker-compose up --build)
make up              # start containers detached
make down            # stop containers
make down-v          # stop containers and remove volumes
make logs            # tail logs for all services
make makemigrations  # python manage.py makemigrations (inside django container)
make migrate         # python manage.py migrate --no-input
make superuser       # createsuperuser
make shell           # shell_plus (django-extensions)
make restart         # restart containers
make backup / make backups / make copy-backups / make restore   # Postgres backups via the postgres service's backup/restore entrypoints
```

Alternative local (non-Docker) DB backup/restore scripts live in `scripts/local/`; Docker-side equivalents are in `scripts/docker/`. `scripts/build.sh` does a `git pull` + `docker-compose up --build -d` for deployment; `scripts/clear_docker_build_cache.sh` clears build cache before a rebuild.

Running Django management commands directly (e.g. inside the `template_web` container or a local venv) always targets `src/manage.py`:

```bash
python src/manage.py <command>
```

### Tests

```bash
python src/manage.py test --parallel --exclude-tag=dev-mode
```

This exact command also runs as a pre-commit hook (`django-test`), so it must pass before commits succeed. To run a single app's tests: `python src/manage.py test apps.upload`.

### Linting / formatting

Enforced via `.pre-commit-config.yaml` (black, flake8, isort, mypy, plus a migrations-check and the django-test hook above). Line length is 120 everywhere. Run all hooks manually with `pre-commit run --all-files`.

## Repository structure

```
.
├── Makefile                    # Docker/Django command shortcuts (see Common commands)
├── docker/
│   ├── Dockerfile               # web/celery image
│   ├── DockerfileCron           # cron-worker image
│   └── docker-compose.yml       # web, postgres, redis, rabbit, celery services
├── requirements/
│   ├── base.txt                 # shared deps (Django, DRF, Celery, Kafka, Sentry, ...)
│   ├── local.txt                # dev-only additions on top of base.txt
│   └── production.txt           # prod-only additions on top of base.txt
├── scripts/
│   ├── build.sh                  # git pull + docker-compose up --build -d
│   ├── clear_docker_build_cache.sh
│   ├── down.sh
│   ├── remove_none_docker_images.sh
│   ├── docker/                   # backup_db.sh / restore_db.sh run against the postgres container
│   └── local/                    # same, for a non-Docker local Postgres
├── .envs/                        # .env / .env.local (git-ignored; copy from *.example)
└── src/                           # Django project root (run manage.py commands from here)
    ├── manage.py
    ├── config/                    # project-wide config, not a Django "app" with models
    │   ├── settings/               # see Settings composition below — one file per concern
    │   ├── urls.py                  # root URLconf; mounts apps/v1.py at api/v1/
    │   ├── celery.py                 # Celery app + Cronitor wiring
    │   ├── wsgi.py / asgi.py
    ├── apps/
    │   ├── v1.py                    # v1 API URL aggregator (auth/user/upload namespaces)
    │   ├── _auth/                    # custom User model, JWT auth, user endpoints
    │   │   ├── models/ managers/ serializers/ services/ urls/ views/
    │   │   └── migrations/{dev,prod}/  # env-split migration histories (see below)
    │   ├── common/                   # shared, non-endpoint code used across apps
    │   │   ├── base_api.py             # BaseGenericAPI — see Request/response pipeline
    │   │   ├── models.py                # BaseModel (audit fields) — see Shared model conventions
    │   │   ├── response/                 # ExceptionResponse, ResponseCode, response envelope
    │   │   ├── schema/                    # drf-spectacular helpers for consistent API docs
    │   │   ├── locale/                     # TranslatableText enum — see i18n section
    │   │   ├── choices/, permissions/, serializers/, utils/, filters.py, pagination.py
    │   │   └── migrations/{dev,prod}/
    │   ├── upload/                    # file upload app (models/serializers/views/urls/tests.py)
    │   │   └── migrations/{dev,prod}/
    │   └── logger/                     # cross-app logging + Telegram alerting
    │       ├── _loggers.py               # named logger instances
    │       ├── restapi_exception_handler.py  # DRF EXCEPTION_HANDLER
    │       ├── handlers/telegram_alert_handler.py, send_bot_message.py
    │       └── tasks/notify_admin_task.py     # Celery task that sends the Telegram alert
    └── templates/                     # custom error pages / base template
```

Each local app (`_auth`, `common`, `upload`) follows the same internal layout: `models/`, `serializers/`, `views/`, `urls/` as packages (not single files) once an app has more than one of something, plus its own `migrations/dev/` and `migrations/prod/`. `upload` is simple enough that it still uses flat `serializers.py`/`views.py`/`urls.py` files — follow whichever pattern the app you're editing already uses rather than mixing both within one app.

## Architecture

### Settings composition

`src/config/settings/__init__.py` assembles settings by importing a fixed sequence of single-purpose modules from `src/config/settings/` (env, allowed_host, apps, middleware, templates, conf, db, locale, log, rest_framework, static, debug, elastic_apm_settings, migrations, oauth, sentry_conf, swagger_conf). When changing a setting, find the module owning that concern rather than adding to a monolithic settings file.

### Environment-split migrations

`LOCAL_APPS` (`config/settings/apps.py`) are the project's own apps. `config/settings/migrations.py` auto-creates `migrations/dev/` and `migrations/prod/` subpackages for every local app and routes Django's `MIGRATION_MODULES` to `prod` when `PRODUCTION=True`, otherwise `dev`. This means:
- New migrations must be generated with the correct `PRODUCTION` env value for the target environment.
- Each local app's migrations directory has two live migration histories (`dev` and `prod`), not one — check both when reasoning about schema state.

### Request/response pipeline

- `apps/common/base_api.py` defines `BaseGenericAPI` (`_BaseAPI` + `GenericAPIView`), which overrides `dispatch()` to call an abstract `perform_check()` hook before the HTTP method handler runs, and routes all exceptions through `handle_exception`. `BaseGenericAPI.perform_check` auto-validates `request.data` against `serializer_class` and exposes the result via `self.validate_data`. Views built on this base don't need to call `serializer.is_valid()` themselves.
- `apps/common/response/exception_response.py` (`ExceptionResponse`) is the standard way to raise API errors with a consistent envelope: `status`, `is_success`, `code_detail`, `response_code`, `error`, `data`. `response_code` should be a member of `apps/common/response/response_code.py::ResponseCode` (currently an empty enum — extend it per-domain as needed).
- `REST_FRAMEWORK["EXCEPTION_HANDLER"]` is `apps.logger.restapi_exception_handler.restapi_exception_handler`, which normalizes `Http404`/`PermissionDenied` into DRF exceptions and logs any 5xx or non-`APIException` error via `errorRequestLogger` (defined in `apps/logger/_loggers.py`), including a formatted traceback and requesting user info.

### Logging and alerting

`apps/logger/` centralizes logging: named loggers (`external_service_logger`, `celery_logger`, `error_request_logger`, `kafka_logger`) are declared in `_loggers.py` and configured in `config/settings/log.py`. `handlers/telegram_alert_handler.py` + `send_bot_message.py` push error-level logs to a Telegram chat (via `BOT_TOKEN`/`ADMIN_CHAT_ID`/`THREAD_ID`); `tasks/notify_admin_task.py` is the Celery task used for this so alerting doesn't block the request.

### API structure

- URLs are versioned: `config/urls.py` mounts `apps/v1.py` at `api/v1/`. New endpoints should be added as a new versioned root (or into `v1.py`) rather than directly in `config/urls.py`.
- `apps/v1.py` includes per-app URL modules under namespaces (`auth`, `user`, `upload`, ...). Follow the existing `_auth` app's split of `urls/auth_urls.py` vs `urls/user_urls.py` when an app has multiple logical URL groups.
- API docs are auto-generated by drf-spectacular; schema at `api/schema/`, Swagger UI at `api/docs/`. `apps/common/schema/` holds shared spectacular helpers (`response_scheme`, custom serializer schema) — use these to keep documented response shapes consistent instead of ad hoc `extend_schema` calls per view.

### Auth (`apps/_auth/`)

Custom user model (`AUTH_USER_MODEL` = `_auth.User`) extends `AbstractBaseUser` + `PermissionsMixin` + the shared `BaseModel`, with `username` as `USERNAME_FIELD` and an integer `role` field (`apps/common/choices/role.py`). JWT auth (`djangorestframework_simplejwt`) is configured in `config/settings/rest_framework.py` — access tokens last 1 day, refresh 30 days, rotation + blacklisting enabled. Note the app package is `_auth` (underscore prefix) because `auth` collides with Django's built-in app; always import as `apps._auth...`.

### Shared model conventions

`apps/common/models.py::BaseModel` is an abstract base providing `created_by`/`updated_by` (FK to `_auth.User`) and `created_at`/`updated_at`. New domain models should inherit from this rather than plain `models.Model` to keep audit fields consistent.

### i18n / translatable strings

Rather than calling `gettext_lazy` inline, translatable strings are declared once as enum members in `apps/common/locale/local_language.py::TranslatableText` and referenced elsewhere via `apps.common.locale.getTextLazy` (aliased `_`), e.g. `verbose_name=_(T.username)`. Add new user-facing strings to this enum instead of scattering `gettext_lazy` calls across files.

### Background jobs

Celery app is defined in `src/config/celery.py` (broker/backend config lives in Django settings via `CELERY_*` env vars), with Cronitor monitoring wired in via `cronitor.celery.initialize(app)`. Beat schedule uses `django_celery_beat`'s `DatabaseScheduler`. The `celery` service in `docker/docker-compose.yml` runs `celery -A config worker`; there's also a separate `DockerfileCron` for cron-style jobs.

### Docker topology

`docker/docker-compose.yml` defines `web` (gunicorn, migrates + collectstatic on boot), `postgres`, `redis`, `rabbit` (RabbitMQ, currently unused by the `web`/`celery` services which point at Redis), and `celery`. All source is bind-mounted from `src/` so container restarts pick up code changes without rebuilding.
