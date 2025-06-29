from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps._auth.serializers.auth_serializer import (
    AuthResponseSerializer,
    LogoutSerializer,
)
from apps._auth.services.auth_service import AuthService


class AuthAPIView(GenericAPIView):
    serializer_class = AuthResponseSerializer
    permission_classes = (permissions.AllowAny,)

    @extend_schema(responses=AuthResponseSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        tokens = AuthService.auth_token(username, password)
        return Response(tokens, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)
    service_class = AuthService()

    def post(self, request):
        refresh_token: str = request.data.get("refresh")
        self.service_class.logout(refresh_token)
        return Response(status=status.HTTP_205_RESET_CONTENT)
