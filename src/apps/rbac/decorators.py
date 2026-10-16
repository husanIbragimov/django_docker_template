"""
@api_view funksiya-view'lari va klasslar uchun RBAC metama'lumotlari.

    @rbac(key="reports.debtors", name="Qarzdorlar hisoboti")
    @api_view(["GET"])
    def debtors(request): ...

    @rbac(public=True)
    class HealthView(APIView): ...
"""

_ATTRS = {
    "key": "rbac_key",
    "name": "rbac_name",
    "group": "rbac_group",
    "public": "rbac_public",
    "per_method": "rbac_per_method",
    "gateway": "rbac_gateway",
}


def rbac(**options):
    unknown = set(options) - set(_ATTRS)
    if unknown:
        raise TypeError(f"rbac(): noma'lum parametr(lar): {', '.join(sorted(unknown))}")

    def decorator(obj):
        targets = [obj]
        for attr in ("cls", "view_class"):  # as_view()/api_view natijasi
            target = getattr(obj, attr, None)
            if target is not None and target not in targets:
                targets.append(target)
        for target in targets:
            for opt, value in options.items():
                setattr(target, _ATTRS[opt], value)
        return obj

    return decorator
