from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from utils.developer_required import developer_user_required as only_developer

urlpatterns = [
    path("scheme/", only_developer(SpectacularAPIView.as_view()), name="scheme"),
    path("", only_developer(SpectacularSwaggerView.as_view(url_name="scheme")), name="swagger-ui"),
    path("redoc/", only_developer(SpectacularRedocView.as_view(url_name="scheme")), name="redoc"),
]
