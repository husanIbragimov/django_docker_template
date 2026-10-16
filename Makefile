ifneq (,$(wildcard ./.env))
	include .env
	export
	ENV_FILE_PARAM = --env-file .envs
endif


# Stack selector: make up ENV=prod | ENV=dev (default, with nginx) | ENV=local (postgres + redis only)
ENV ?= dev
COMPOSE = bash scripts/compose.sh $(ENV)

build:
	$(COMPOSE) up --build --remove-orphans

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

down-v:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

makemigrations:
	$(COMPOSE) run --rm web python manage.py makemigrations

migrate:
	$(COMPOSE) run --rm web python manage.py migrate --no-input

superuser:
	$(COMPOSE) run --rm web python manage.py createsuperuser

shell:
	$(COMPOSE) run --rm web python manage.py shell_plus

restart:
	$(COMPOSE) restart

backup:
	$(COMPOSE) exec postgres backup

backups:
	$(COMPOSE) exec postgres backups

copy-backups:
	docker cp $$($(COMPOSE) ps -q postgres):/backups ./backups

restore:
	$(COMPOSE) exec postgres restore file_name.sql.gz

dev:
	bash scripts/run_dev.sh

prod:
	bash scripts/run_prod.sh

local:
	bash scripts/run_local.sh
