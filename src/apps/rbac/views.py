from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .conf import rbac_settings
from .models import ApiEndpoint, Module, Role
from .permissions import HasApiAccess
from .serializers import (
    ApiEndpointSerializer,
    ApiEndpointShortSerializer,
    ModuleSerializer,
    RoleAccessSerializer,
    RoleSerializer,
    RoleUsersSerializer,
    UserRolesSerializer,
)
from .services import build_module_tree, get_user_access, match_gateway


class MyAccessView(APIView):
    """
    Joriy foydalanuvchining ruxsatlari — frontend shu bilan UI'ni quradi.
    GET /rbac/me/
    """

    rbac_public = True
    permission_classes = [IsAuthenticated]

    def get(self, request):
        access = get_user_access(request.user, request)
        if access.is_super:
            endpoints = list(ApiEndpoint.objects.filter(is_active=True).values_list("key", flat=True))
        else:
            public = ApiEndpoint.objects.filter(is_active=True, is_public=True).values_list("key", flat=True)
            endpoints = sorted(access.endpoints | set(public))
        return Response(
            {
                "is_super": access.is_super,
                "modules": build_module_tree(lambda m: access.has_module(m.code)),
                "endpoints": endpoints,
            }
        )


class GatewayAuthView(APIView):
    """
    nginx ``auth_request`` uchun: proxy qilingan API'ni tekshiradi.
    204 — ruxsat bor, 401 — login qilinmagan, 403 — ruxsat yo'q.

        location = /_rbac_auth {
            internal;
            proxy_pass http://django/api/rbac/authz/;
            proxy_pass_request_body off;
            proxy_set_header Content-Length "";
            proxy_set_header X-Original-URI $request_uri;
            proxy_set_header X-Original-Method $request_method;
            proxy_set_header Authorization $http_authorization;
        }
    """

    rbac_public = True
    permission_classes = []

    def get(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        uri = request.META.get(rbac_settings.GATEWAY_URI_HEADER, "")
        method = request.META.get(rbac_settings.GATEWAY_METHOD_HEADER, "GET")
        path = uri.split("?", 1)[0]

        access = get_user_access(request.user, request)
        key = match_gateway(path, method)
        allowed = access.allows(key)
        response = Response(status=status.HTTP_204_NO_CONTENT if allowed else status.HTTP_403_FORBIDDEN)
        if key:
            response["X-RBAC-Key"] = key
        return response


class ApiEndpointViewSet(viewsets.ModelViewSet):
    """
    API katalogi. Ichki API'lar ``rbac_sync`` bilan yaratiladi (bu yerda faqat nomi/tavsifi/is_public
    tahrirlanadi). Gateway API'lar shu yerda qo'lda yaratiladi.
    """

    queryset = ApiEndpoint.objects.all()
    serializer_class = ApiEndpointSerializer
    permission_classes = [HasApiAccess]
    search_fields = ["key", "name", "path"]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        for field in ("kind", "group"):
            if params.get(field):
                qs = qs.filter(**{field: params[field]})
        if params.get("is_active") in ("true", "false"):
            qs = qs.filter(is_active=params["is_active"] == "true")
        return qs

    def perform_destroy(self, instance):
        if instance.kind == ApiEndpoint.Kind.INTERNAL and instance.is_active:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Faol ichki API'ni o'chirib bo'lmaydi — avval koddan olib tashlang va rbac_sync.")
        instance.delete()

    @action(detail=False, methods=["get"])
    def groups(self, request):
        """API'lar guruhlab: [{group, endpoints: [...]}] — rol tahrirlash ekrani uchun."""
        result: dict[str, list] = {}
        for ep in self.get_queryset().filter(is_active=True):
            result.setdefault(ep.group or "other", []).append(ApiEndpointShortSerializer(ep).data)
        return Response([{"group": g, "endpoints": eps} for g, eps in sorted(result.items())])


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all().prefetch_related("endpoints")
    serializer_class = ModuleSerializer
    permission_classes = [HasApiAccess]
    pagination_class = None

    @action(detail=False, methods=["get"])
    def tree(self, request):
        return Response(build_module_tree(lambda m: True))


class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = [HasApiAccess]

    def get_queryset(self):
        return Role.objects.annotate(users_count=Count("users", distinct=True)).prefetch_related(
            "modules", "endpoints"
        )

    @action(detail=True, methods=["get"])
    def access(self, request, pk=None):
        """
        Rol tahrirlash ekrani uchun to'liq holat:
          modules   — daraxt, har bir tugunda has_access
          endpoints — guruhlangan API'lar: granted (to'g'ridan-to'g'ri), via_modules (modul orqali)
        """
        role = self.get_object()
        module_ids = set(role.modules.values_list("id", flat=True))
        direct = set(role.endpoints.values_list("id", flat=True))

        via: dict[int, list[str]] = {}
        if rbac_settings.MODULE_GRANTS_ENDPOINTS:
            for ep_id, code in Module.endpoints.through.objects.filter(module_id__in=module_ids).values_list(
                "apiendpoint_id", "module__code"
            ):
                via.setdefault(ep_id, []).append(code)

        groups: dict[str, list] = {}
        for ep in ApiEndpoint.objects.filter(is_active=True):
            groups.setdefault(ep.group or "other", []).append(
                {
                    **ApiEndpointShortSerializer(ep).data,
                    "is_public": ep.is_public,
                    "granted": ep.id in direct,
                    "via_modules": sorted(via.get(ep.id, [])),
                }
            )
        return Response(
            {
                "role": RoleSerializer(self.get_queryset().get(pk=role.pk)).data,
                "modules": build_module_tree(lambda m: m.id in module_ids),
                "endpoints": [{"group": g, "endpoints": eps} for g, eps in sorted(groups.items())],
            }
        )

    @access.mapping.put
    def set_access(self, request, pk=None):
        """PUT /roles/{id}/access/  {"modules": [..], "endpoints": [..]} — berilgan ro'yxat bilan almashtiradi."""
        role = self.get_object()
        serializer = RoleAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            if "modules" in serializer.validated_data:
                role.modules.set(serializer.validated_data["modules"])
            if "endpoints" in serializer.validated_data:
                role.endpoints.set(serializer.validated_data["endpoints"])
        return self.access(request, pk)

    @action(detail=True, methods=["put"])
    def users(self, request, pk=None):
        """PUT /roles/{id}/users/  {"users": [..]}"""
        role = self.get_object()
        serializer = RoleUsersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role.users.set(serializer.validated_data["users"])
        return Response({"users": [u.pk for u in role.users.all()]})


class UserRolesViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    GET /users/{id}/roles/  — foydalanuvchi rollari
    PUT /users/{id}/roles/  {"roles": [..]}
    """

    permission_classes = [HasApiAccess]
    serializer_class = UserRolesSerializer
    queryset = get_user_model().objects.all()

    def retrieve(self, request, pk=None):
        user = get_object_or_404(get_user_model(), pk=pk)
        roles = Role.objects.filter(users=user).annotate(users_count=Count("users"))
        return Response({"user": user.pk, "roles": RoleSerializer(roles, many=True).data})

    def update(self, request, pk=None):
        user = get_object_or_404(get_user_model(), pk=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.rbac_roles.set(serializer.validated_data["roles"])
        return self.retrieve(request, pk)
