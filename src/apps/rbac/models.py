import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Module(TimeStamped):
    """
    UI moduli (menyu, sahifa, tugma, tab ...). Daraxt ko'rinishida.
    Frontend shu ``code`` bo'yicha elementni ko'rsatadi/yashiradi.

    ``endpoints`` — shu UI element ishlashi uchun kerak bo'lgan API'lar.
    Rolga modul berilganda (MODULE_GRANTS_ENDPOINTS=True) bu API'lar ham beriladi.
    """

    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children", verbose_name=_("Yuqori modul")
    )
    code = models.SlugField(_("Kod"), max_length=150, unique=True)
    name = models.CharField(_("Nomi"), max_length=255)
    description = models.TextField(_("Tavsif"), blank=True)
    order = models.PositiveIntegerField(_("Tartib"), default=0)
    endpoints = models.ManyToManyField(
        "rbac.ApiEndpoint", blank=True, related_name="modules", verbose_name=_("Kerakli API'lar")
    )

    class Meta:
        db_table = "rbac_module"
        ordering = ("order", "id")
        verbose_name = _("UI modul")
        verbose_name_plural = _("UI modullar")

    def __str__(self):
        return self.code

    def clean(self):
        node = self.parent
        while node is not None:
            if node.pk == self.pk:
                raise ValidationError({"parent": _("Modul o'zining avlodiga bog'lana olmaydi.")})
            node = node.parent


class ApiEndpoint(TimeStamped):
    """
    Bitta API = bitta ruxsat kaliti (key).

    INTERNAL — Django/DRF view. ``rbac_sync`` buyrug'i URLconf'dan avtomatik yaratadi.
               key = url view_name (masalan ``finance:student-payment-create``),
               ViewSet uchun ``<namespace>:<basename>.<action>``.
    GATEWAY  — Django ichida view'i yo'q, proxy qilingan API. Qo'lda (API/admin orqali) kiritiladi.
               ``path`` — regex (to'liq mos kelishi kerak), ``methods`` — [] bo'lsa hammasi.
    """

    class Kind(models.TextChoices):
        INTERNAL = "internal", _("Ichki API")
        GATEWAY = "gateway", _("Gateway / proxy API")

    key = models.CharField(_("Kalit"), max_length=255, unique=True)
    kind = models.CharField(_("Turi"), max_length=16, choices=Kind.choices, default=Kind.INTERNAL, db_index=True)
    name = models.CharField(_("Nomi"), max_length=255, blank=True)
    description = models.TextField(_("Tavsif"), blank=True)
    group = models.CharField(_("Guruh"), max_length=100, blank=True, db_index=True)
    path = models.CharField(_("Yo'l / regex"), max_length=500, blank=True)
    methods = models.JSONField(_("HTTP metodlar"), default=list, blank=True)
    is_public = models.BooleanField(
        _("Hammaga ochiq"), default=False, help_text=_("Har qanday autentifikatsiyadan o'tgan foydalanuvchiga ruxsat")
    )
    is_active = models.BooleanField(
        _("Faol"), default=True, help_text=_("rbac_sync kodda topilmagan ichki API'larni nofaol qiladi")
    )

    class Meta:
        db_table = "rbac_api_endpoint"
        ordering = ("group", "key")
        verbose_name = _("API endpoint")
        verbose_name_plural = _("API endpointlar")

    def __str__(self):
        return self.key

    def clean(self):
        self.methods = sorted({m.upper() for m in (self.methods or [])})
        if self.kind == self.Kind.GATEWAY:
            if not self.path:
                raise ValidationError({"path": _("Gateway API uchun path regex majburiy.")})
            try:
                re.compile(self.path)
            except re.error as exc:
                raise ValidationError({"path": _("Noto'g'ri regex: %s") % exc}) from exc


class Role(TimeStamped):
    code = models.SlugField(_("Kod"), max_length=100, unique=True)
    name = models.CharField(_("Nomi"), max_length=150)
    description = models.TextField(_("Tavsif"), blank=True)
    is_active = models.BooleanField(_("Faol"), default=True)
    is_super = models.BooleanField(_("To'liq ruxsat"), default=False, help_text=_("Barcha API va modullarga ruxsat"))

    modules = models.ManyToManyField(Module, blank=True, related_name="roles", verbose_name=_("UI modullar"))
    endpoints = models.ManyToManyField(
        ApiEndpoint, blank=True, related_name="roles", verbose_name=_("API'lar (to'g'ridan-to'g'ri)")
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="rbac_roles", verbose_name=_("Foydalanuvchilar")
    )

    class Meta:
        db_table = "rbac_role"
        ordering = ("name",)
        verbose_name = _("Rol")
        verbose_name_plural = _("Rollar")

    def __str__(self):
        return self.name
