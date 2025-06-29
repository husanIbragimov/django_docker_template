import os

from .apps import LOCAL_APPS
from .env import BASE_DIR, PRODUCTION


def create_migration_dirs(app):
    app_path = os.path.join(BASE_DIR, app.replace('.', '/'))
    migrations_dir = os.path.join(app_path, 'migrations')

    if not os.path.exists(migrations_dir):
        return None

    for subdir in ("dev", "prod"):
        os.makedirs(os.path.join(migrations_dir, subdir), exist_ok=True)
        open(os.path.join(migrations_dir, subdir, "__init__.py"), "a").close()

    open(os.path.join(migrations_dir, "__init__.py"), "a").close()
    return app


_MIGRATION_APPS = list(filter(None, (create_migration_dirs(app) for app in LOCAL_APPS)))

MIGRATION_MODULES = {
    app: f"{app}.migrations.prod" if PRODUCTION else f"{app}.migrations.dev"
    for app in _MIGRATION_APPS
}
