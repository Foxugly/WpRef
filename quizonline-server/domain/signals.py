from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from .models import Domain


@receiver(m2m_changed, sender=Domain.managers.through)
def ensure_domain_manager_membership(sender, instance: Domain, action: str, pk_set, **kwargs) -> None:
    if action != "post_add" or not pk_set:
        return
    instance.members.add(*pk_set)
