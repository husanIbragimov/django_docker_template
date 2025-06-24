from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken


class AuthService:
    @classmethod
    def auth_token(cls, username: str, password: str) -> dict[str, str]:
        """
        Authenticate user and return access and refresh tokens.
        """
        user = authenticate(username=username, password=password)
        if not user:
            raise AuthenticationFailed("Invalid credentials")

        refresh = RefreshToken.for_user(user)

        return {"access": str(refresh.access_token), "refresh": str(refresh)}

    @classmethod
    def logout(cls, refresh_token: str) -> None:
        """
        Blacklist the refresh token.
        """
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            raise AuthenticationFailed("Invalid token") from e
