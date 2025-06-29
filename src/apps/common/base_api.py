from abc import ABC, abstractmethod
from typing import Type

from rest_framework.generics import GenericAPIView
from rest_framework.serializers import Serializer


class _BaseAPI(GenericAPIView, ABC):

    # perform_check -> har bir request method (get, post, put, delete, patch) chaqirilishi oldidan chaqiriladi

    @abstractmethod
    def perform_check(self, request, *args, **kwargs):
        pass

    def dispatch(self, request, *args, **kwargs):
        # Validate the request data before calling the actual view

        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        try:
            self.initial(request, *args, **kwargs)

            # Get the appropriate handler method
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            """
              abstract method perform_check chaqiriladi
            """
            self.perform_check(request, args, kwargs)

            response = handler(request, *args, **kwargs)

        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response


class BaseGenericAPI(_BaseAPI):
    serializer_class: Type[Serializer] = None
    response_serializer_class: Type[Serializer] = None

    _validate_data = None
    _serializer = None

    def perform_check(self, request, *args, **kwargs):
        self._serializer = self.serializer_class(data=request.data)

        self._serializer.is_valid(raise_exception=True)

        self._validate_data = self.serializer.validated_data

        return self._serializer.validated_data

    @property
    def validate_data(self):
        return self._validate_data

    @property
    def serializer(self):
        return self._serializer
