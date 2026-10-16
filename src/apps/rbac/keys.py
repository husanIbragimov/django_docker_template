"""
API kalitini (key) aniqlash. Runtime (permission) va ``rbac_sync`` aynan bir xil
qoidadan foydalanadi — shuning uchun hammasi shu yerda.

Qoida (ustuvorlik tartibida):
  1. view'da ``rbac_key`` bor bo'lsa — o'sha (str yoki {action/METHOD: key} dict)
  2. ViewSet bo'lsa      — "<namespace>:<basename>.<action>"
  3. Aks holda           — URL view_name: "<namespace>:<url_name>"
                           (url name yo'q bo'lsa "module.ClassName")
  4. ``rbac_per_method = True`` bo'lsa oxiriga "#<METHOD>" qo'shiladi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator

from django.urls import URLPattern, URLResolver, get_resolver

PER_METHOD_SEP = "#"
IGNORED_METHODS = {"OPTIONS"}


def _normalize_method(method: str) -> str:
    method = method.upper()
    return "GET" if method == "HEAD" else method


def func_path(callback) -> str:
    """Django ResolverMatch._func_path bilan bir xil."""
    func = getattr(callback, "view_class", callback)
    if not hasattr(func, "__name__"):
        return f"{func.__class__.__module__}.{func.__class__.__name__}"
    return f"{func.__module__}.{func.__name__}"


def _ns_prefix(namespace: str | None) -> str:
    return f"{namespace}:" if namespace else ""


def _explicit_key(view_cls, action: str | None, method: str) -> str | None:
    explicit = getattr(view_cls, "rbac_key", None)
    if isinstance(explicit, dict):
        return explicit.get(action) or explicit.get(method)
    return explicit


def _apply_per_method(view_cls, base: str, method: str, is_viewset: bool) -> str:
    if getattr(view_cls, "rbac_per_method", False) and not is_viewset:
        return f"{base}{PER_METHOD_SEP}{method}"
    return base


def resolve_request_key(request, view) -> str:
    """Kelgan so'rov uchun API kalitini qaytaradi (DRF view instance bilan)."""
    method = _normalize_method(request.method)
    action = getattr(view, "action", None)
    is_viewset = hasattr(view, "action") and getattr(view, "basename", None) is not None
    match = getattr(request, "resolver_match", None)

    base = _explicit_key(view, action, method)
    if not base:
        if is_viewset and action:
            base = f"{_ns_prefix(match.namespace if match else '')}{view.basename}.{action}"
        elif match is not None:
            base = match.view_name
        else:
            base = f"{view.__class__.__module__}.{view.__class__.__name__}"
    return _apply_per_method(view, base, method, is_viewset and bool(action))


# ---------------------------------------------------------------- URL discovery


@dataclass
class DiscoveredEndpoint:
    key: str
    path: str
    view_cls: type
    methods: set[str] = field(default_factory=set)


def _iter_patterns(patterns, prefix="", namespaces=()) -> Iterator[tuple[str, object, str | None, tuple]]:
    for p in patterns:
        if isinstance(p, URLResolver):
            ns = namespaces + ((p.namespace,) if p.namespace else ())
            yield from _iter_patterns(p.url_patterns, prefix + str(p.pattern), ns)
        elif isinstance(p, URLPattern):
            yield prefix + str(p.pattern), p.callback, p.name, namespaces


def _clean_route(route: str) -> str:
    route = re.sub(r"\(\?P<(\w+)>[^)]*\)", r"{\1}", route)  # regex group -> {pk}
    route = re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", route)  # <int:pk> -> {pk}
    route = route.replace("^", "").replace("$", "").replace("\\Z", "").replace("\\.", ".")
    return "/" + route.lstrip("/")


def _implemented_methods(view_cls) -> set[str]:
    return {
        m.upper()
        for m in view_cls.http_method_names
        if m not in ("options", "head", "trace") and callable(getattr(view_cls, m, None))
    }


def discover_endpoints(urlconf=None) -> tuple[dict[str, DiscoveredEndpoint], list[type]]:
    """
    URLconf'dagi barcha DRF view'larni topadi.
    Qaytaradi: ({key: DiscoveredEndpoint}, [gateway view klasslari])
    """
    from rest_framework.views import APIView

    found: dict[str, DiscoveredEndpoint] = {}
    gateway_views: list[type] = []

    for route, callback, url_name, namespaces in _iter_patterns(get_resolver(urlconf).url_patterns):
        view_cls = getattr(callback, "cls", None)
        if view_cls is None or not issubclass(view_cls, APIView):
            continue
        if getattr(view_cls, "rbac_public", False):
            continue
        if getattr(view_cls, "rbac_gateway", False):
            gateway_views.append(view_cls)
            continue

        ns = ":".join(namespaces)
        path = _clean_route(route)
        actions = getattr(callback, "actions", None)  # ViewSet

        pairs: list[tuple[str, str]] = []  # (method, key)
        basename = (getattr(callback, "initkwargs", None) or {}).get("basename")
        view_name = ":".join([*namespaces, url_name or func_path(callback)])
        if actions and basename:
            for method, action in actions.items():
                method = method.upper()
                if method in IGNORED_METHODS or method == "HEAD":
                    continue
                key = _explicit_key(view_cls, action, method) or f"{_ns_prefix(ns)}{basename}.{action}"
                pairs.append((method, key))
        else:
            methods = (
                {m.upper() for m in actions} - IGNORED_METHODS - {"HEAD"} if actions else _implemented_methods(view_cls)
            )
            for method in methods:
                action = actions.get(method.lower()) if actions else None
                key = _explicit_key(view_cls, action, method) or view_name
                pairs.append((method, _apply_per_method(view_cls, key, method, False)))

        for method, key in pairs:
            ep = found.setdefault(key, DiscoveredEndpoint(key=key, path=path, view_cls=view_cls))
            ep.methods.add(method)

    return found, gateway_views
