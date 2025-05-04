from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    created_by = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="%(class)s_created_by",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="%(class)s_updated_by",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class RoleChoice(models.IntegerChoices):
    USER = 0, _("User")
    BOSS = 1, _("Boss")
    INSPECTOR = 2, _("Inspector")
    ADMIN = 3, _("Admin")
