from enum import Enum
from django.utils.translation import gettext_lazy as _
from .local_language import TranslatableText


def getTextLazy(text: Enum):
    return _(text.value)