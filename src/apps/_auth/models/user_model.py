from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps._auth.managers.user_manager import UserManager
from apps.common.choices import UserRoleChoice
from apps.common.locale import TranslatableText as T
from apps.common.locale import getTextLazy as _
from apps.common.models import BaseModel


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    username = models.CharField(
        max_length=150,
        unique=True,
        db_index=True,
        verbose_name=_(T.username),
    )
    first_name = models.CharField(
        blank=True,
        max_length=150,
        verbose_name=_(T.first_name),
    )
    last_name = models.CharField(
        blank=True,
        max_length=150,
        verbose_name=_(T.last_name),
    )
    role = models.IntegerField(
        choices=UserRoleChoice.choices,
        default=UserRoleChoice.USER,
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_(T.user_with_is_active_help_text),
        verbose_name=_(T.active),
    )

    is_staff = models.BooleanField(
        default=False,
        help_text=_(
            T.user_with_is_staff_help_text,
        ),
        verbose_name=_(T.is_staff),
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name=_(T.is_superuser),
    )
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_(T.date_joined),
    )

    objects = UserManager()

    USERNAME_FIELD = "username"

    class Meta:
        ordering = ("-id",)
        verbose_name = _(T.user)

    def __str__(self):
        return self.username
