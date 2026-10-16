"""
UI modullar daraxtini JSON'dan yuklash / JSON'ga chiqarish (my_days'dagi modules.json formati ham qo'llanadi).

    python manage.py rbac_modules load staticfiles/modules.json
    python manage.py rbac_modules dump staticfiles/modules.json

Format:
    [
      {"code": "students", "name": "Talabalar", "description": "",
       "endpoints": ["student:list", "student:create"],
       "children": [ ... ]}
    ]
``code`` bo'lmasa ``name`` dan slug olinadi.
"""

import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.rbac.models import ApiEndpoint, Module
from apps.rbac.services import invalidate


class Command(BaseCommand):
    help = "UI modullarni JSON'dan yuklash yoki JSON'ga chiqarish"

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["load", "dump"])
        parser.add_argument("path")

    def handle(self, *args, action, path, **options):
        if action == "dump":
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(self._dump(), fh, ensure_ascii=False, indent=2)
            self.stdout.write(self.style.SUCCESS(f"Saqlandi: {path}"))
            return

        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        self.endpoints = {e.key: e for e in ApiEndpoint.objects.all()}
        self.count = 0
        with transaction.atomic():
            for order, item in enumerate(data):
                self._load(item, None, order)
        invalidate()
        self.stdout.write(self.style.SUCCESS(f"{self.count} ta modul yuklandi/yangilandi"))

    def _load(self, item, parent, order):
        code = item.get("code") or slugify(item["name"]) or f"module-{item.get('id')}"
        module, _ = Module.objects.update_or_create(
            code=code,
            defaults={
                "name": item.get("name") or code,
                "description": item.get("description") or "",
                "parent": parent,
                "order": item.get("order", order),
            },
        )
        self.count += 1
        if "endpoints" in item:
            missing = [k for k in item["endpoints"] if k not in self.endpoints]
            if missing:
                self.stderr.write(self.style.WARNING(f"  {code}: topilmagan API'lar (avval rbac_sync): {missing}"))
            module.endpoints.set([self.endpoints[k] for k in item["endpoints"] if k in self.endpoints])
        for child_order, child in enumerate(item.get("children") or []):
            self._load(child, module, child_order)

    def _dump(self):
        modules = list(Module.objects.prefetch_related("endpoints").order_by("order", "id"))
        children = {}
        for m in modules:
            children.setdefault(m.parent_id, []).append(m)

        def build(m):
            return {
                "code": m.code,
                "name": m.name,
                "description": m.description,
                "endpoints": sorted(e.key for e in m.endpoints.all()),
                "children": [build(c) for c in children.get(m.id, [])],
            }

        return [build(m) for m in children.get(None, [])]
