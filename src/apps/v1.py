from django.urls import include, path

urlpatterns = [
    path(
        "auth/",
        include(("apps._auth.urls.auth_urls", "auth"), namespace="auth"),
    ),
    path(
        "user/",
        include(("apps._auth.urls.user_urls", "user"), namespace="user"),
    ),
    path("upload/", include(("apps.upload.urls", "upload"), namespace="upload")),
]
