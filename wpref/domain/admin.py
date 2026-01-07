# domain/admin.py
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from parler.admin import TranslatableAdmin

from .models import Domain


@admin.register(Domain)
class DomainAdmin(TranslatableAdmin):
    """
    Admin pour Domain (django-parler).
    - Edition des champs traduits (name/description)
    - Gestion allowed_languages, staff
    - Filtrage/Recherche utiles
    - Optimisations queryset
    """

    # Champs affichés dans la liste
    list_display = (
        "id",
        "name_i18n",
        "active",
        "owner",
        "allowed_languages_count",
        "staff_count",
        "updated_at",
    )
    list_display_links = ("id", "name_i18n")
    list_filter = ("active", "created_at", "updated_at")
    ordering = ("id",)
    date_hierarchy = "created_at"

    # Recherche: sur traductions + owner
    search_fields = (
        "translations__name",
        "translations__description",
        "owner__username",
        "owner__email",
    )

    # Widgets M2M plus confortables
    filter_horizontal = ("allowed_languages", "staff")

    # Form (TranslatableAdmin utilise fieldsets par langue automatiquement)
    fieldsets = (
        (None, {"fields": ("active", "owner")}),
        (_("Languages & staff"), {"fields": ("allowed_languages", "staff")}),
        (_("Dates"), {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Parler: prefetch translations + éviter N+1 owner + counts M2M
        return (
            qs.select_related("owner")
              .prefetch_related("translations", "allowed_languages", "staff")
              .annotate(_allowed_lang_count=Count("allowed_languages", distinct=True))
              .annotate(_staff_count=Count("staff", distinct=True))
        )

    @admin.display(description=_("Name"))
    def name_i18n(self, obj: Domain) -> str:
        # ton __str__ fait déjà safe_translation_getter, mais ici c’est clair en colonne
        return obj.safe_translation_getter("name", any_language=True) or f"Domain#{obj.pk}"

    @admin.display(description=_("Allowed languages"), ordering="_allowed_lang_count")
    def allowed_languages_count(self, obj: Domain) -> int:
        return getattr(obj, "_allowed_lang_count", 0)

    @admin.display(description=_("Staff"), ordering="_staff_count")
    def staff_count(self, obj: Domain) -> int:
        return getattr(obj, "_staff_count", 0)
