from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Domain


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "owner", "languages_display", "created_at", "updated_at")
    list_filter = ("active",)
    search_fields = ("name", "description", "owner__username", "owner__email")
    ordering = ("name",)
    filter_horizontal = ("staff",)  # M2M nice UI

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("name", "description", "active")}),
        (_("Languages"), {"fields": ("allowed_languages",)}),
        (_("Ownership & Staff"), {"fields": ("owner", "staff")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )

    def languages_display(self, obj: Domain) -> str:
        return ", ".join(obj.allowed_languages or [])

    languages_display.short_description = _("Allowed languages")

    def save_model(self, request, obj, form, change):
        """
        Optionnel (mais utile): si owner vide à la création depuis l'admin,
        on le met au user courant.
        """
        if not change and not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)
