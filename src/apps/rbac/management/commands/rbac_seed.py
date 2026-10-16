"""
API katalogini sinxronlab, ``assets/ui_template.json`` dagi UI modullarni bazaga yozadi.

    python manage.py rbac_seed                       # rbac_sync + rbac_modules load assets/ui_template.json
    python manage.py rbac_seed --path other.json     # boshqa template
    python manage.py rbac_seed --skip-sync           # faqat modullarni yuklash

Takroriy ishga tushirish xavfsiz (update_or_create): template'dagi modullarning nomi/tartibi/API'lari
template bo'yicha qayta yoziladi, template'da yo'q modullarga tegilmaydi.
"""

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

DEFAULT_TEMPLATE = settings.BASE_DIR.parent / "assets" / "ui_template.json"


class Command(BaseCommand):
    help = "rbac_sync + UI modullar template'ini (assets/ui_template.json) bazaga yuklash"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path", default=str(DEFAULT_TEMPLATE), help=f"Template JSON (default: {DEFAULT_TEMPLATE})"
        )
        parser.add_argument("--skip-sync", action="store_true", help="rbac_sync'ni o'tkazib yuborish")

    def handle(self, *args, path, skip_sync=False, **options):
        out = {"stdout": self.stdout, "stderr": self.stderr}
        if not skip_sync:
            call_command("rbac_sync", **out)
        call_command("rbac_modules", "load", path, **out)
