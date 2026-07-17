from django.conf import settings
from django.utils.translation import get_language
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


@extend_schema_field(OpenApiTypes.STR)
class TranslatedField(serializers.Field):
    """Renders a {"ru": "...", "en": "..."} JSONField as a single string in the active language.

    Falls back to settings.LANGUAGE_CODE, then to any available value, so a missing
    translation doesn't blank out the response.
    """

    def __init__(self, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_representation(self, value: dict[str, str]) -> str:
        if not value:
            return ""
        lang = get_language() or settings.LANGUAGE_CODE
        text = value.get(lang) or value.get(settings.LANGUAGE_CODE)
        if text:
            return text
        return next(iter(value.values()), "")
