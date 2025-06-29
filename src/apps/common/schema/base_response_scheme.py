from typing import Type

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    PolymorphicProxySerializer,
    extend_schema,
)
from rest_framework import serializers
from rest_framework.serializers import Serializer

auto_schema = AutoSchema()


def response_scheme(response_serializer_class: Type[Serializer]):

    return extend_schema(
        responses={
            200: response_serializer_class,
            400: response_serializer_class,
        },
    )
