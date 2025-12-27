# lang/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class Language(models.Model):
    """
    Langue disponible dans l'application.
    Sert de référentiel (Domain.allowed_languages, User.lang, etc.).
    """

    code = models.CharField(
        _("code"),
        max_length=10,
        unique=True,
        help_text=_("Code ISO (ex: fr, nl, en, fr-BE)")
    )

    name = models.CharField(
        _("name"),
        max_length=100,
        help_text=_("Nom lisible (ex: Français, Nederlands, English)")
    )

    active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Langue disponible pour la saisie et l'affichage")
    )

    class Meta:
        ordering = ["code"]
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")

    def __str__(self):
        return f"{self.code} — {self.name}"
