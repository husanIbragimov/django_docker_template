ifneq (,$(wildcard ./.env))
	include .env
	export
	ENV_FILE_PARAM = --env-file .envs
endif


build:
	cd docker/ && docker-compose --env-file .envs/.env up --build --remove-orphans

up:
	cd docker/ && docker-compose --env-file .envs/.env up -d

down:
	cd docker/ && docker-compose --env-file .envs/.env down

down-v:
	cd docker/ && docker-compose --env-file .envs/.env down -v

logs:
	cd docker/ && docker-compose --env-file .envs/.env logs -f

makemigrations:
	cd docker/ && docker-compose --env-file .envs/.env run --rm django python manage.py makemigrations

migrate:
	cd docker/ && docker-compose --env-file .envs/.env run --rm django python manage.py migrate --no-input

superuser:
	cd docker/ && docker-compose --env-file .envs/.env run --rm django python manage.py createsuperuser

shell:
	cd docker/ && docker-compose --env-file .envs/.env run --rm django python manage.py shell_plus

restart:
	cd docker/ && docker-compose --env-file .envs/.env restart

backup:
	cd docker/ && docker compose --env-file .envs/.env exec postgres backup

backups:
	cd docker/ && docker compose --env-file .envs/.env exec postgres backups

copy-backups:
	cd docker/ && docker cp $(cd docker/ && docker compose --env-file .envs/.env ps -q postgres):/backups ./backups

restore:
	cd docker/ && docker compose --env-file .envs/.env exec postgres restore file_name.sql.gz
