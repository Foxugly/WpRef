from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

User = get_user_model()


def settings_language_codes() -> set[str]:
    return {code for code, _ in getattr(settings, "LANGUAGES", [])}


class Domain(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(_("name"), max_length=120),
        description=models.TextField(_("description"), blank=True),
    )

    allowed_languages = models.ManyToManyField(
        "language.Language",
        related_name="domains",
        blank=True,
    )
    active = models.BooleanField(default=True, db_index=True)

    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="owned_domains",
    )

    # ✅ Le staff/gestionnaires du domaine
    staff = models.ManyToManyField(
        User,
        blank=True,
        related_name="managed_domains",  # ✅ côté user : user.managed_domains.all()
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.safe_translation_getter("name", any_language=True) or f"Domain#{self.pk}"

    def clean(self):
        valid = settings_language_codes()
        codes = set(self.allowed_languages.values_list("code", flat=True))

        invalid = sorted([c for c in codes if c not in valid])
        if invalid:
            raise ValidationError(
                {"allowed_languages": [f"Invalid language code(s): {', '.join(invalid)}"]}
            )
