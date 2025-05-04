from django.urls import path

from apps.user.views import (
    AuthAPIView,
    LogoutAPIView,
)

urlpatterns = [
    path("login/", view=AuthAPIView.as_view(), name="login_view"),
    path("logout/", view=LogoutAPIView.as_view(), name="user_logout"),
]
