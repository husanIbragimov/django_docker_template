from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.user.managers.user_manager import UserManager
from apps.common.models import BaseModel, RoleChoice


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    username = models.CharField(
        max_length=150,
        unique=True, db_index=True,
        verbose_name=_("username"),
    )
    first_name = models.CharField(
        blank=True,
        max_length=150,
        verbose_name=_("first name"),
    )
    last_name = models.CharField(
        blank=True,
        max_length=150,
        verbose_name=_("last name"),
    )
    role = models.IntegerField(
        choices=RoleChoice.choices,
        default=RoleChoice.USER,
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting user."
        ),
        verbose_name=_("active"),
    )

    is_staff = models.BooleanField(
        default=False,
        help_text=_(
            "Designates whether the user can log into this admin site.",
        ),
        verbose_name=_("staff status"),
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name=_("superuser status"),
    )
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("date joined"),
    )

    objects = UserManager()

    USERNAME_FIELD = "username"

    class Meta:
        ordering = ("-id",)
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.username
