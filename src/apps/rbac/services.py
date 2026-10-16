"""
Ruxsatlarni hisoblash va keshlash.

Kesh sxemasi: bitta global "versiya" raqami. Rol / modul / endpoint / bog'lanish
o'zgarganda versiya oshiriladi (signals.py) — eski kesh yozuvlari avtomatik eskiradi.
Shu sababli invalidatsiya O(1) va hech qachon eskirgan ruxsat qaytmaydi.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from functools import lru_cache

from django.core.cache import caches
from django.db.models import Q

from .conf import rbac_settings
from .models import ApiEndpoint, Module, Role

REQUEST_ATTR = "_rbac_access"


def _cache():
    return caches[rbac_settings.CACHE_ALIAS]


def _k(*parts) -> str:
    return ":".join([rbac_settings.CACHE_PREFIX, *map(str, parts)])


def current_version() -> int:
    cache, key = _cache(), _k("version")
    version = cache.get(key)
    if version is None:
        cache.add(key, time.time_ns(), timeout=None)
        version = cache.get(key) or time.time_ns()
    return version


def invalidate() -> None:
    """Barcha RBAC keshini eskirtiradi."""
    cache, key = _cache(), _k("version")
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, time.time_ns(), timeout=None)


# ------------------------------------------------------------------ catalog


@dataclass(frozen=True)
class Catalog:
    registered: frozenset[str]
    public: frozenset[str]
    gateway: tuple[tuple[str, str, tuple[str, ...]], ...]  # (key, regex, methods)


@lru_cache(maxsize=1024)
def _compile(pattern: str) -> re.Pattern:
    return re.compile(pattern)


def get_catalog() -> Catalog:
    cache_key = _k("catalog", current_version())
    data = _cache().get(cache_key)
    if data is None:
        rows = list(
            ApiEndpoint.objects.filter(is_active=True).values_list("key", "kind", "is_public", "path", "methods")
        )
        gateway = [
            (key, path, tuple(m.upper() for m in (methods or [])))
            for key, kind, _, path, methods in rows
            if kind == ApiEndpoint.Kind.GATEWAY and path
        ]
        # Uzunroq (aniqroq) pattern birinchi tekshiriladi
        gateway.sort(key=lambda row: len(row[1]), reverse=True)
        data = {
            "registered": [r[0] for r in rows],
            "public": [r[0] for r in rows if r[2]],
            "gateway": gateway,
        }
        _cache().set(cache_key, data, rbac_settings.CACHE_TIMEOUT)
    return Catalog(
        registered=frozenset(data["registered"]),
        public=frozenset(data["public"]),
        gateway=tuple((k, p, tuple(m)) for k, p, m in data["gateway"]),
    )


def match_gateway(path: str, method: str) -> str | None:
    """Proxy qilingan so'rov yo'li + metodiga mos gateway endpoint kalitini topadi."""
    method = "GET" if method.upper() == "HEAD" else method.upper()
    for key, pattern, methods in get_catalog().gateway:
        if methods and method not in methods:
            continue
        if _compile(pattern).fullmatch(path):
            return key
    return None


# ------------------------------------------------------------------ user access


@dataclass(frozen=True)
class UserAccess:
    is_super: bool
    endpoints: frozenset[str]
    modules: frozenset[str]

    def allows(self, key: str | None, catalog: Catalog | None = None) -> bool:
        if self.is_super:
            return True
        if not key:
            return rbac_settings.ALLOW_UNREGISTERED
        if key in self.endpoints:
            return True
        catalog = catalog or get_catalog()
        if key in catalog.public:
            return True
        if key not in catalog.registered:
            return rbac_settings.ALLOW_UNREGISTERED
        return False

    def has_module(self, code: str) -> bool:
        return self.is_super or code in self.modules


SUPER_ACCESS = UserAccess(is_super=True, endpoints=frozenset(), modules=frozenset())
NO_ACCESS = UserAccess(is_super=False, endpoints=frozenset(), modules=frozenset())


def _compute(user) -> dict:
    roles = Role.objects.filter(users=user, is_active=True)
    if roles.filter(is_super=True).exists():
        return {"is_super": True, "endpoints": [], "modules": []}

    module_codes = list(Module.objects.filter(roles__in=roles).values_list("code", flat=True).distinct())

    grant = Q(roles__in=roles)
    if rbac_settings.MODULE_GRANTS_ENDPOINTS:
        grant |= Q(modules__roles__in=roles)
    endpoint_keys = list(
        ApiEndpoint.objects.filter(is_active=True).filter(grant).values_list("key", flat=True).distinct()
    )
    return {"is_super": False, "endpoints": endpoint_keys, "modules": module_codes}


def get_user_access(user, request=None) -> UserAccess:
    if user is None or not user.is_authenticated:
        return NO_ACCESS
    if not getattr(user, "is_active", True):
        return NO_ACCESS
    if rbac_settings.SUPERUSER_BYPASS and getattr(user, "is_superuser", False):
        return SUPER_ACCESS

    raw_request = getattr(request, "_request", request)
    if raw_request is not None:
        memo = getattr(raw_request, REQUEST_ATTR, None)
        if memo is not None and memo[0] == user.pk:
            return memo[1]

    cache_key = _k("user", user.pk, current_version())
    data = _cache().get(cache_key)
    if data is None:
        data = _compute(user)
        _cache().set(cache_key, data, rbac_settings.CACHE_TIMEOUT)

    access = UserAccess(
        is_super=data["is_super"], endpoints=frozenset(data["endpoints"]), modules=frozenset(data["modules"])
    )
    if raw_request is not None:
        setattr(raw_request, REQUEST_ATTR, (user.pk, access))
    return access


def user_can(user, key: str) -> bool:
    """Kod ichida qo'lda tekshirish uchun: ``if user_can(request.user, "finance:report"): ...``"""
    return get_user_access(user).allows(key)


def build_module_tree(has_access) -> list[dict]:
    """Barcha modullar daraxti, har biriga ``has_access`` bayrog'i bilan."""
    modules = list(Module.objects.all().order_by("order", "id"))
    children: dict[int | None, list[Module]] = {}
    for m in modules:
        children.setdefault(m.parent_id, []).append(m)

    def build(node: Module) -> dict:
        return {
            "id": node.id,
            "code": node.code,
            "name": node.name,
            "description": node.description,
            "has_access": bool(has_access(node)),
            "children": [build(c) for c in children.get(node.id, [])],
        }

    return [build(m) for m in children.get(None, [])]
