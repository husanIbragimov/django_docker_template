from django.contrib import admin

from .models import ApiEndpoint, Module, Role


@admin.register(ApiEndpoint)
class ApiEndpointAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "kind", "group", "path", "methods", "is_public", "is_active")
    list_filter = ("kind", "group", "is_public", "is_active")
    search_fields = ("key", "name", "path")
    list_editable = ("is_public",)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.kind == ApiEndpoint.Kind.INTERNAL:
            return ("key", "kind", "path", "methods", "is_active")
        return ("is_active",) if obj else ()


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "parent", "order")
    list_filter = ("parent",)
    search_fields = ("code", "name")
    filter_horizontal = ("endpoints",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "is_super")
    search_fields = ("code", "name")
    filter_horizontal = ("modules", "endpoints", "users")
