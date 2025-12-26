from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ValidationError

User = get_user_model()


def settings_language_codes() -> set[str]:
    return {code for code, _ in getattr(settings, "LANGUAGES", [])}


class Domain(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    allowed_languages = models.JSONField(default=list, blank=True)
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
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def clean(self):
        valid = settings_language_codes()
        invalid = [c for c in (self.allowed_languages or []) if c not in valid]
        if invalid:
            raise ValidationError(
                {"allowed_languages": f"Invalid language code(s): {', '.join(invalid)}"}
            )
