# subject/admin.py
from __future__ import annotations

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin

from .models import Subject


@admin.register(Subject)
class SubjectAdmin(TranslatableAdmin):
    # --- List page ---
    list_display = ("id", "name_any", "domain", "active")
    list_filter = ("domain", "active")
    list_select_related = ("domain",)
    ordering = ("-pk",)

    # --- Search (important for autocomplete_fields) ---
    search_fields = (
        "translations__name",
        "translations__description",
        "domain__translations__name",  # si Domain est aussi Parler (chez toi oui)
    )

    # --- Form ---
    autocomplete_fields = ("domain",)
    fieldsets = (
        (_("Référence"), {"fields": ("domain", "active")}),
        (_("Traductions"), {"fields": ("name", "description")}),
    )

    def name_any(self, obj: Subject) -> str:
        return obj.safe_translation_getter("name", any_language=True) or ""

    name_any.short_description = _("name")
