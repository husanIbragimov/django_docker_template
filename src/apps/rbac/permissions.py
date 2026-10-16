from rest_framework.permissions import BasePermission

from .keys import resolve_request_key
from .services import get_catalog, get_user_access, match_gateway


class HasApiAccess(BasePermission):
    """
    Asosiy DRF permission. settings.py:

        REST_FRAMEWORK = {
            "DEFAULT_PERMISSION_CLASSES": ["apps.rbac.permissions.HasApiAccess"],
        }

    View atributlari (ixtiyoriy):
        rbac_key = "custom.key"            # yoki {"list": "...", "create": "..."} / {"GET": ..., "POST": ...}
        rbac_public = True                 # tekshirilmaydi (login, refresh, me ...)
        rbac_per_method = True             # GET va POST alohida ruxsat: "<key>#GET", "<key>#POST"
        rbac_gateway = True                # proxy view: key = gateway endpoint regex bo'yicha
    """

    message = "Sizda ushbu API'dan foydalanish uchun ruxsat yo'q."

    def has_permission(self, request, view):
        if getattr(view, "rbac_public", False):
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False

        access = get_user_access(user, request)
        if access.is_super:
            return True

        if getattr(view, "rbac_gateway", False):
            key = match_gateway(request.path, request.method)
        else:
            key = resolve_request_key(request, view)

        request._request.rbac_key = key  # log / debug uchun
        return access.allows(key, get_catalog())


class HasModule(BasePermission):
    """
    Qo'shimcha: view'ni UI modulga bog'lash (kamdan-kam kerak bo'ladi).
        permission_classes = [HasModule.require("students.export")]
    """

    module_code: str = ""

    @classmethod
    def require(cls, code: str):
        return type(f"HasModule_{code}", (cls,), {"module_code": code})

    def has_permission(self, request, view):
        return get_user_access(request.user, request).has_module(self.module_code)
