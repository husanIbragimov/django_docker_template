from abc import abstractmethod

from rest_framework import serializers


class ResponseSerializerInterface:
    @abstractmethod
    def code(self) -> int | None:
        pass

    @abstractmethod
    def error_message(self) -> str | None:
        pass

    def scheme(self) -> dict:
        raise NotImplementedError(
            "You must implement this method : Bu method ovveride qilinib, seraizerni json "
            "sxemasini qaytararishi krak"
        )

    def presentation(self, to_representation):
        return {"error": self.error_message(), "response_code": self.code(), "data": to_representation}


# @response_serializer_scheme()
class BaseResponseSerializer(serializers.Serializer, ResponseSerializerInterface):
    response_code = serializers.SerializerMethodField("get_response_code", allow_null=True)
    error = serializers.SerializerMethodField("get_error", allow_null=True)

    def to_representation(self, instance):
        return self.presentation(super().to_representation(instance))

    def get_response_code(self, obj):
        return self.code()

    def get_error(self, obj):
        return self.error_message()


# @response_serializer_scheme()
class BaseResponseModelSerializer(serializers.ModelSerializer, ResponseSerializerInterface):
    def to_representation(self, instance):
        return self.presentation(super().to_representation(instance))

    def get_response_code(self, obj):
        return self.code()

    def get_error(self, obj):
        return self.error_message()
