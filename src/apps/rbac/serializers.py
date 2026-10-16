from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import ApiEndpoint, Module, Role


class ApiEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiEndpoint
        fields = [
            "id", "key", "kind", "name", "description", "group",
            "path", "methods", "is_public", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["is_active", "created_at", "updated_at"]

    def validate(self, attrs):
        instance = self.instance
        kind = attrs.get("kind", instance.kind if instance else ApiEndpoint.Kind.GATEWAY)

        if instance is None and kind != ApiEndpoint.Kind.GATEWAY:
            raise serializers.ValidationError({"kind": "Ichki API'lar faqat `rbac_sync` orqali yaratiladi."})
        if instance is not None and instance.kind == ApiEndpoint.Kind.INTERNAL:
            # Ichki API'ning texnik maydonlari koddan keladi
            for field in ("key", "kind", "path", "methods"):
                if field in attrs and attrs[field] != getattr(instance, field):
                    raise serializers.ValidationError({field: "Ichki API uchun bu maydon koddan olinadi."})

        technical = ("key", "kind", "path", "methods")
        current = {f: getattr(instance, f) for f in technical} if instance else {}
        probe = ApiEndpoint(**{**current, **{f: attrs[f] for f in technical if f in attrs}})
        probe.kind = kind
        try:
            probe.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        attrs["methods"] = probe.methods
        return attrs


class ApiEndpointShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiEndpoint
        fields = ["id", "key", "kind", "name", "group", "path", "methods"]


class ModuleSerializer(serializers.ModelSerializer):
    endpoints = serializers.PrimaryKeyRelatedField(many=True, queryset=ApiEndpoint.objects.all(), required=False)

    class Meta:
        model = Module
        fields = ["id", "parent", "code", "name", "description", "order", "endpoints"]

    def validate(self, attrs):
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        probe = Module(pk=getattr(self.instance, "pk", None), parent=parent)
        try:
            probe.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        return attrs


class RoleSerializer(serializers.ModelSerializer):
    modules = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    endpoints = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    users_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Role
        fields = [
            "id", "code", "name", "description", "is_active", "is_super",
            "modules", "endpoints", "users_count", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class RoleAccessSerializer(serializers.Serializer):
    """Rolning UI modullari va API'larini to'liq almashtirish (checkbox daraxti saqlanganda)."""

    modules = serializers.PrimaryKeyRelatedField(many=True, queryset=Module.objects.all(), required=False)
    endpoints = serializers.PrimaryKeyRelatedField(many=True, queryset=ApiEndpoint.objects.all(), required=False)


class RoleUsersSerializer(serializers.Serializer):
    users = serializers.PrimaryKeyRelatedField(many=True, queryset=get_user_model().objects.all())


class UserRolesSerializer(serializers.Serializer):
    roles = serializers.PrimaryKeyRelatedField(many=True, queryset=Role.objects.all())
