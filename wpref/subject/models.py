from django.db import models
from django.utils.translation import gettext_lazy as _
from domain.models import Domain
from parler.models import TranslatedFields, TranslatableModel


class Subject(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(_("name"), max_length=120),
        description=models.TextField(_("description"), blank=True),
    )
    domain = models.ForeignKey(
        Domain,
        on_delete=models.PROTECT,
        related_name="subjects", blank=True, null=True
    )

    class Meta:
        ordering = ["-pk"]

    def __str__(self):
        return self.safe_translation_getter("name", any_language=True) or f"Subject#{self.pk}"
