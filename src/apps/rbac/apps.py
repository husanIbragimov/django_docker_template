from django.apps import AppConfig


class RbacConfig(AppConfig):
    name = "apps.rbac"
    label = "rbac"
    verbose_name = "RBAC (API access)"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import signals  # noqa: F401
