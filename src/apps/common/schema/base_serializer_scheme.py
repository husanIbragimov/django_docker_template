from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Type, TypeVar, Union

from drf_spectacular.drainage import set_override
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework.serializers import Serializer


def _custom_extend_schema_serializer(
    many: Optional[bool] = None,
    exclude_fields: Optional[Sequence[str]] = None,
    deprecate_fields: Optional[Sequence[str]] = None,
    examples_func: Callable[[dict], Optional[Sequence[OpenApiExample]]] = None,
    extensions: Optional[Dict[str, Any]] = None,
    component_name: Optional[str] = None,
) -> Callable[[Type[Serializer]], Type[Serializer]]:
    def decorator(klass: Type[Serializer]):

        if many is not None:
            set_override(klass, "many", many)
        if exclude_fields:
            set_override(klass, "exclude_fields", exclude_fields)
        if deprecate_fields:
            set_override(klass, "deprecate_fields", deprecate_fields)
        if examples_func:
            examples = examples_func(klass.scheme())
            set_override(klass, "examples", examples)
        if extensions:
            set_override(klass, "extensions", extensions)
        if component_name:
            set_override(klass, "component_name", component_name)
        return klass

    return decorator


def response_serializer_scheme():
    return _custom_extend_schema_serializer(examples_func=_get_examples)


def _get_examples(data: dict):
    return [
        OpenApiExample(value={"response_code": 2000, "error": None, "data": data}, name="Success", status_codes=[200]),
        OpenApiExample(
            value={"response_code": 4000, "error": "Error message", "data": None}, name="Fail", status_codes=[400]
        ),
    ]
