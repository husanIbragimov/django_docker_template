from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from .models import ApiEndpoint, Module, Role
from .services import invalidate


@receiver(post_save, sender=Role)
@receiver(post_delete, sender=Role)
@receiver(post_save, sender=Module)
@receiver(post_delete, sender=Module)
@receiver(post_save, sender=ApiEndpoint)
@receiver(post_delete, sender=ApiEndpoint)
def _on_change(**kwargs):
    invalidate()


@receiver(m2m_changed, sender=Role.modules.through)
@receiver(m2m_changed, sender=Role.endpoints.through)
@receiver(m2m_changed, sender=Role.users.through)
@receiver(m2m_changed, sender=Module.endpoints.through)
def _on_m2m_change(action, **kwargs):
    if action in ("post_add", "post_remove", "post_clear"):
        invalidate()


# Eslatma: user.is_active / is_superuser keshga yozilmaydi — har so'rovda
# user obyektining o'zidan o'qiladi, shuning uchun User signal'i kerak emas.
