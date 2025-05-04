from django.urls import include, path

urlpatterns = [
    path(
        "auth/", include(("apps.user.urls.auth_urls", "auth"), namespace="auth"),
    ),
    path(
        "user/", include(("apps.user.urls.user_urls", "user"), namespace="user"),
    ),
]
