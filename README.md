# 🐍 Django Project Template

This repository is a modular and production-ready Django-based backend structure that includes built-in support for Docker, PostgreSQL, Celery, logging, user management, and more.

## 📦 Project Structure
```markdown
.
├── Makefile                   # CLI shortcuts for Docker and Django commands
├── README.md                 # Project documentation
├── assets/                   # Static/media or frontend assets
├── backups/                  # Database backup directory
├── docker/                   # Docker setup and configurations
│   ├── Dockerfile            # Web container
│   ├── DockerfileCron        # Cron container
│   ├── docker-compose.prod.yml   # Full stack (web, celery, postgres, redis)
│   ├── docker-compose.dev.yml    # prod + nginx for static/media
│   └── docker-compose.local.yml  # postgres + redis only
├── requirements/             # Python dependencies
│   ├── base.txt
│   ├── local.txt
│   └── production.txt
├── scripts/                  # DevOps and automation scripts
│   ├── build.sh
│   ├── clear_docker_build_cache.sh
│   ├── down.sh
│   ├── remove_none_docker_images.sh
│   ├── docker/               # Docker-specific DB tools
│   │   ├── backup_db.sh
│   │   └── restore_db.sh
│   └── local/                # Local DB tools
│       ├── backup_db.sh
│       └── restore_db.sh
└── src/                      # Main Django source
    ├── apps/                 # Modular Django apps
    │   ├── _auth/            # Custom user model and auth system
    │   ├── common/           # Shared logic (pagination, permissions, utils)
    │   ├── logger/           # Logging and exception handling via Telegram
    │   ├── upload/           # File upload management
    │   └── v1.py             # Entry point for v1 APIs
    ├── config/               # Django settings and WSGI/ASGI entry points
    │   ├── settings/         # Environment-based settings (db, swagger, sentry, etc.)
    │   ├── celery.py         # Celery configuration
    │   └── urls.py
    ├── manage.py             # Django management script
    └── templates/            # Custom error pages and base template

````

## 🐳 Docker Usage

### 🔧 Build and Start

```bash
  make build         # Build docker images
  make up            # Start all containers
  make down          # Stop all containers
````

### 🛠️ Rebuild with Cache Clear

```bash
  bash scripts/clear_docker_build_cache.sh
  make build
```

### 📦 DB Backup/Restore

```bash
# Docker
  bash scripts/docker/backup_db.sh
  bash scripts/docker/restore_db.sh

# Local
  bash scripts/local/backup_db.sh
  bash scripts/local/restore_db.sh
```

## ⚙️ Core Features

* ✅ Custom User Model and Authentication
* 📂 Upload System
* 🧩 Modular App Architecture
* 🐇 Celery Integration for Background Tasks
* 📬 Telegram Bot Alerts on Exceptions
* 📜 DRF + Swagger for API documentation
* 🎯 Production/Local Environment Separation
* 🧪 Test-ready Structure

## 🧪 Environment Setup

Create a `.env` and `.env.local` files:

```bash
    cp .envs/.env.example .envs/.env
    cp .envs/.env.local.example .envs/.env.local
```

Then:

```bash
  bash scripts/build.sh
  docker exec -it template_web bash
  python src/manage.py createsuperuser
```

## 📖 API Docs

Once running, visit:

```
http://localhost:8080/api/docs/
```

## 📬 Logging and Alerts

* Exception handling is configured via `logger/` app.
* Telegram alert integration can be found in:

  * `send_bot_message.py`
  * `telegram_alert_handler.py`

## 📁 Migrations

Migrations are split into environments:

* `migrations/dev/`
* `migrations/prod/`

This helps maintain clean control over which migrations are used in different environments.

---

## 🤝 Contributing

Feel free to fork, open issues, and make pull requests. Keep commits clean and write meaningful messages.

## 📝 License

MIT — use as you wish.

---

### Maintained by [github.com/husanIbragimov](https://github.com/husanIbragimov)
