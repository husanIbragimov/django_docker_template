from abc import ABC, abstractmethod
from typing import Type

from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
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


class BaseGenericListCreateAPI(BaseGenericAPI):
    """BaseGenericAPI variant for a view combining GET list + POST create at one URL.

    perform_check always runs on every HTTP method (see _BaseAPI.dispatch), so a plain
    BaseGenericAPI would try to validate an empty GET body against serializer_class and
    fail. This skips that validation for anything other than POST.
    """

    def perform_check(self, request, *args, **kwargs):
        if request.method != "POST":
            return None
        return super().perform_check(request, *args, **kwargs)


class BaseGenericUpdateAPI(BaseGenericAPI):
    """BaseGenericAPI variant for PUT/PATCH endpoints, safe to combine with retrieve/destroy.

    Validates against the existing instance (so unique-field validators correctly exclude
    it) instead of BaseGenericAPI's default instance-less `serializer_class(data=...)`, and
    only runs on PUT/PATCH so GET/DELETE on the same view aren't forced through validation.
    """

    def perform_check(self, request, *args, **kwargs):
        if request.method not in ("PUT", "PATCH"):
            return None
        instance = self.get_object()
        partial = request.method == "PATCH"
        self._serializer = self.serializer_class(instance, data=request.data, partial=partial)
        self._serializer.is_valid(raise_exception=True)
        self._validate_data = self._serializer.validated_data
        return self._validate_data


class AdminListCreateAPI(mixins.ListModelMixin, BaseGenericListCreateAPI):
    """Standard admin CRUD collection endpoint: GET list (IsAdminUser) + POST create."""

    permission_classes = (IsAdminUser,)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        instance = self.serializer.save(created_by=request.user)
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)


class AdminDetailAPI(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, BaseGenericUpdateAPI):
    """Standard admin CRUD detail endpoint: GET/DELETE (IsAdminUser) + PUT/PATCH update."""

    permission_classes = (IsAdminUser,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        instance = self.serializer.save(updated_by=request.user)
        return Response(self.get_serializer(instance).data)

    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)
