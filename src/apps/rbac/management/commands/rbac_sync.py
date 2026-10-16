"""
URLconf'dagi barcha DRF API'larni ``ApiEndpoint`` jadvaliga sinxronlaydi.

    python manage.py rbac_sync            # yaratish/yangilash, yo'qolganlarni nofaol qilish
    python manage.py rbac_sync --dry-run  # faqat ko'rsatish
    python manage.py rbac_sync --prune    # koddan yo'qolgan ichki API'larni o'chirish
    python manage.py rbac_sync --audit    # HasApiAccess ishlatmayotgan view'larni ko'rsatish

Deploy pipeline'iga ``migrate`` dan keyin qo'shing.
"""

import re

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.rbac.conf import rbac_settings
from apps.rbac.keys import discover_endpoints
from apps.rbac.models import ApiEndpoint
from apps.rbac.permissions import HasApiAccess
from apps.rbac.services import invalidate


def _group_for(view_cls) -> str:
    explicit = getattr(view_cls, "rbac_group", None)
    if explicit:
        return explicit
    parts = view_cls.__module__.split(".")
    if "apps" in parts and parts.index("apps") + 1 < len(parts):
        return parts[parts.index("apps") + 1]
    return parts[0]


def _name_for(view_cls) -> str:
    explicit = getattr(view_cls, "rbac_name", None)
    if explicit:
        return explicit
    doc = (view_cls.__doc__ or "").strip()
    from rest_framework.views import APIView

    if doc and doc != (APIView.__doc__ or "").strip():
        return doc.splitlines()[0][:255]
    return view_cls.__name__


def _is_enforced(view_cls) -> bool:
    return any(isinstance(p, type) and issubclass(p, HasApiAccess) for p in view_cls.permission_classes)


class Command(BaseCommand):
    help = "DRF API'larni RBAC katalogiga (ApiEndpoint) sinxronlash"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--prune", action="store_true", help="Koddan yo'qolgan ichki API'larni o'chirish")
        parser.add_argument("--audit", action="store_true", help="HasApiAccess'siz view'larni ko'rsatish")
        parser.add_argument("--overwrite-names", action="store_true", help="name/group'ni koddan qayta yozish")

    def handle(self, *args, dry_run=False, prune=False, audit=False, overwrite_names=False, **options):
        discovered, gateway_views = discover_endpoints()
        excludes = [re.compile(p) for p in rbac_settings.EXCLUDE_KEY_PATTERNS]
        excluded_ns = set(rbac_settings.EXCLUDE_NAMESPACES)

        def excluded(key: str) -> bool:
            ns = key.split(":", 1)[0] if ":" in key else ""
            return ns in excluded_ns or any(p.search(key) for p in excludes)

        discovered = {k: v for k, v in discovered.items() if not excluded(k)}
        existing = {e.key: e for e in ApiEndpoint.objects.filter(kind=ApiEndpoint.Kind.INTERNAL)}
        conflicts = set(
            ApiEndpoint.objects.filter(kind=ApiEndpoint.Kind.GATEWAY, key__in=discovered).values_list("key", flat=True)
        )

        created, updated = [], []
        for key, ep in sorted(discovered.items()):
            if key in conflicts:
                self.stderr.write(self.style.ERROR(f"  ! {key}: gateway endpoint bilan bir xil kalit — o'tkazildi"))
                continue
            values = {
                "path": ep.path,
                "methods": sorted(ep.methods),
                "is_active": True,
            }
            obj = existing.get(key)
            if obj is None:
                created.append(ApiEndpoint(key=key, kind=ApiEndpoint.Kind.INTERNAL, name=_name_for(ep.view_cls),
                                           group=_group_for(ep.view_cls), **values))
                continue
            if overwrite_names:
                values.update(name=_name_for(ep.view_cls), group=_group_for(ep.view_cls))
            if any(getattr(obj, f) != v for f, v in values.items()):
                for f, v in values.items():
                    setattr(obj, f, v)
                obj.updated_at = timezone.now()
                updated.append(obj)

        stale = [e for k, e in existing.items() if k not in discovered and e.is_active]
        removed = [e for k, e in existing.items() if k not in discovered] if prune else []

        for obj in created:
            self.stdout.write(self.style.SUCCESS(f"  + {obj.key}  {obj.methods}  {obj.path}"))
        for obj in updated:
            self.stdout.write(f"  ~ {obj.key}  {obj.methods}  {obj.path}")
        for obj in (removed if prune else stale):
            self.stdout.write(self.style.WARNING(f"  {'x' if prune else '-'} {obj.key}"))

        if not dry_run:
            with transaction.atomic():
                ApiEndpoint.objects.bulk_create(created)
                if updated:
                    ApiEndpoint.objects.bulk_update(
                        updated, ["path", "methods", "is_active", "name", "group", "updated_at"]
                    )
                if prune:
                    ApiEndpoint.objects.filter(pk__in=[e.pk for e in removed]).delete()
                else:
                    ApiEndpoint.objects.filter(pk__in=[e.pk for e in stale]).update(is_active=False)
            invalidate()

        self.stdout.write(
            f"\nJami: {len(discovered)} API | yangi: {len(created)} | yangilangan: {len(updated)} | "
            f"{'o`chirilgan' if prune else 'nofaol qilingan'}: {len(removed) if prune else len(stale)}"
            f"{' (dry-run, bazaga yozilmadi)' if dry_run else ''}"
        )
        if gateway_views:
            names = ", ".join(sorted({v.__name__ for v in gateway_views}))
            self.stdout.write(f"Gateway view'lar (kalit regex orqali aniqlanadi): {names}")

        if audit:
            unenforced = sorted({f"{ep.view_cls.__module__}.{ep.view_cls.__name__}"
                                 for ep in discovered.values() if not _is_enforced(ep.view_cls)})
            if unenforced:
                self.stdout.write(self.style.WARNING(f"\nHasApiAccess ishlatmayotgan view'lar ({len(unenforced)}):"))
                for name in unenforced:
                    self.stdout.write(f"  {name}")
            else:
                self.stdout.write(self.style.SUCCESS("\nBarcha view'lar HasApiAccess bilan himoyalangan."))
