"""
Demo rollar va foydalanuvchilarni yaratadi (har bir rolning ruxsatlari har xil).

    python manage.py rbac_demo                 # parol: 123
    python manage.py rbac_demo --password abc

Modullar avval yuklangan bo'lishi kerak (``rbac_seed``). Takroriy ishga tushirish xavfsiz:
rollarning modullari template bo'yicha qayta yoziladi, foydalanuvchi paroli yangilanadi.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.rbac.models import Module, Role

PROFILE = ["profile", "profile-logout"]

# code -> (nomi, tavsif, modullar)
DEMO_ROLES = {
    "rbac-admin": (
        "RBAC administrator",
        "Rollar, modullar va API'larni to'liq boshqaradi (fayl yuklashsiz)",
        PROFILE
        + [
            "rbac",
            "rbac-roles",
            "rbac-roles-create",
            "rbac-roles-update",
            "rbac-roles-delete",
            "rbac-roles-access",
            "rbac-roles-users",
            "rbac-user-roles",
            "rbac-modules",
            "rbac-modules-create",
            "rbac-modules-update",
            "rbac-modules-delete",
            "rbac-endpoints",
            "rbac-endpoints-create",
            "rbac-endpoints-update",
            "rbac-endpoints-delete",
        ],
    ),
    "manager": (
        "Menejer",
        "Rollarni ko'radi, foydalanuvchilarga rol biriktiradi, fayl yuklaydi",
        PROFILE + ["upload", "rbac", "rbac-roles", "rbac-roles-users", "rbac-user-roles"],
    ),
    "auditor": (
        "Auditor",
        "Rollar, modullar va API'larni faqat ko'radi",
        PROFILE + ["rbac", "rbac-roles", "rbac-modules", "rbac-endpoints"],
    ),
    "operator": (
        "Operator",
        "Faqat profil va fayl yuklash",
        PROFILE + ["upload"],
    ),
}

# username -> (ism, familiya, rol kodi)
DEMO_USERS = {
    "rbac_admin": ("Rbac", "Admin", "rbac-admin"),
    "manager": ("Demo", "Menejer", "manager"),
    "auditor": ("Demo", "Auditor", "auditor"),
    "operator": ("Demo", "Operator", "operator"),
}


class Command(BaseCommand):
    help = "Demo rollar (har xil ruxsatlar bilan) va ularga biriktirilgan foydalanuvchilarni yaratish"

    def add_arguments(self, parser):
        parser.add_argument("--password", default="123", help="Demo foydalanuvchilar paroli (default: 123)")

    @transaction.atomic
    def handle(self, *args, password, **options):
        modules = {m.code: m for m in Module.objects.all()}
        missing = {c for _, _, codes in DEMO_ROLES.values() for c in codes} - modules.keys()
        if missing:
            raise CommandError(f"Modullar topilmadi: {', '.join(sorted(missing))}. Avval `rbac_seed` ni ishga tushiring.")

        roles = {}
        for code, (name, description, codes) in DEMO_ROLES.items():
            role, _ = Role.objects.update_or_create(
                code=code, defaults={"name": name, "description": description, "is_active": True, "is_super": False}
            )
            role.modules.set([modules[c] for c in codes])
            roles[code] = role
            self.stdout.write(f"Rol: {code} ({len(codes)} modul)")

        User = get_user_model()
        for username, (first_name, last_name, role_code) in DEMO_USERS.items():
            user, _ = User.objects.update_or_create(
                username=username, defaults={"first_name": first_name, "last_name": last_name, "is_active": True}
            )
            user.set_password(password)
            user.save(update_fields=["password"])
            user.rbac_roles.set([roles[role_code]])
            self.stdout.write(f"Foydalanuvchi: {username} -> {role_code}")

        self.stdout.write(self.style.SUCCESS("Demo rollar va foydalanuvchilar tayyor."))
