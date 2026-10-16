"""
Sozlamalar. settings.py da override qilinadi:

    RBAC = {
        "ALLOW_UNREGISTERED": False,
        "MODULE_GRANTS_ENDPOINTS": True,
        ...
    }
"""

from django.conf import settings

DEFAULTS = {
    # is_superuser=True foydalanuvchi hamma narsaga ruxsatli
    "SUPERUSER_BYPASS": True,
    # Rolga UI modul berilsa, shu modulga bog'langan API'lar ham avtomatik beriladi
    "MODULE_GRANTS_ENDPOINTS": True,
    # Bazada ro'yxatdan o'tmagan (rbac_sync qilinmagan) API'ga ruxsat berilsinmi?
    # Bosqichma-bosqich joriy qilishda vaqtincha True qilish mumkin. Production: False.
    "ALLOW_UNREGISTERED": False,
    "CACHE_ALIAS": "default",
    "CACHE_TIMEOUT": 60 * 60,
    "CACHE_PREFIX": "rbac",
    # rbac_sync bu namespace'lardagi URL'larni ro'yxatga olmaydi
    "EXCLUDE_NAMESPACES": ["admin"],
    # key shu regex'lardan biriga mos kelsa — ro'yxatga olinmaydi
    "EXCLUDE_KEY_PATTERNS": [r"schema", r"swagger", r"redoc", r"^djdt"],
    # nginx auth_request uchun header'lar (request.META nomi)
    "GATEWAY_URI_HEADER": "HTTP_X_ORIGINAL_URI",
    "GATEWAY_METHOD_HEADER": "HTTP_X_ORIGINAL_METHOD",
}


class _Settings:
    def __getattr__(self, name):
        if name not in DEFAULTS:
            raise AttributeError(f"Unknown RBAC setting: {name}")
        return getattr(settings, "RBAC", {}).get(name, DEFAULTS[name])


rbac_settings = _Settings()
