from django.db import models

from apps.common.locale import TranslatableText as T
from apps.common.locale import getTextLazy as _


class UserRoleChoice(models.IntegerChoices):
    ADMIN = 0, _(T.admin)
    USER = 1, _(T.user)
