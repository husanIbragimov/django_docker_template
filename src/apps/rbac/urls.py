"""
    path("rbac/", include(("apps.rbac.urls", "rbac"), namespace="rbac")),  # apps/v1.py

Ruxsat kalitlari (namespace "rbac"):
    rbac:role.list / create / retrieve / update / partial_update / destroy / access / set_access / users
    rbac:endpoint.list / create / ... / groups
    rbac:module.list / ... / tree
    rbac:user-roles.retrieve / update
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ApiEndpointViewSet, GatewayAuthView, ModuleViewSet, MyAccessView, RoleViewSet, UserRolesViewSet

app_name = "rbac"

router = DefaultRouter(trailing_slash=True)
router.include_root_view = False
router.register("roles", RoleViewSet, basename="role")
router.register("endpoints", ApiEndpointViewSet, basename="endpoint")
router.register("modules", ModuleViewSet, basename="module")

user_roles = UserRolesViewSet.as_view({"get": "retrieve", "put": "update"}, basename="user-roles")

urlpatterns = [
    path("me/", MyAccessView.as_view(), name="me"),
    path("authz/", GatewayAuthView.as_view(), name="authz"),
    path("users/<int:pk>/roles/", user_roles, name="user-roles"),
    *router.urls,
]
