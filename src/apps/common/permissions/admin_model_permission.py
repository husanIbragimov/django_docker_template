from django.contrib import admin


def admin_has_permission(func):
    def wrapper(cls, request, *args, **kwargs):
        user = request.user
        if user.is_anonymous:
            return False

        if user.is_admin or user.is_superuser:
            return True
        return func(cls, request, *args, **kwargs)

    return wrapper


class AdminModelPermission(admin.ModelAdmin):
    @admin_has_permission
    def has_view_permission(self, request, obj=...):
        super().has_change_permission(request, obj)

    @admin_has_permission
    def has_module_permission(self, request):
        super().has_module_permission(request)
