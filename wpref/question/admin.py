# question/admin.py
from __future__ import annotations

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _

from parler.admin import TranslatableAdmin, TranslatableTabularInline

from .models import (
    Question,
    AnswerOption,
    QuestionMedia,
    QuestionSubject,
    MediaAsset,
)

# ==========================================================
# Formsets (validations inline)
# ==========================================================

class AnswerOptionInlineFormSet(BaseInlineFormSet):
    """
    Valide les règles métier sur les AnswerOption au moment du save en admin.
    (Car Question.clean dépend des answer_options.)
    """
    def clean(self):
        super().clean()

        forms = [
            f for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get("DELETE", False)
        ]

        if len(forms) < 2:
            raise ValidationError(_("A Question must have at least 2 possible answers."))

        correct_count = sum(1 for f in forms if f.cleaned_data.get("is_correct"))

        if correct_count == 0:
            raise ValidationError(_("Indique au moins une réponse correcte."))

        allow_multi = getattr(self.instance, "allow_multiple_correct", False)
        if not allow_multi and correct_count != 1:
            raise ValidationError(_("Only ONE answer allowed."))


# ==========================================================
# Inlines
# ==========================================================

class AnswerOptionInline(TranslatableTabularInline):
    model = AnswerOption
    formset = AnswerOptionInlineFormSet
    extra = 0
    fields = ("content", "is_correct", "sort_order")
    ordering = ("sort_order", "id")


class QuestionMediaInline(admin.TabularInline):
    """
    Lien Question ↔ MediaAsset (ordre uniquement).
    Le MediaAsset est créé séparément.
    """
    model = QuestionMedia
    extra = 0
    fields = ("asset", "sort_order")
    ordering = ("sort_order", "id")
    autocomplete_fields = ("asset",)


class QuestionSubjectInline(admin.TabularInline):
    model = QuestionSubject
    extra = 0
    fields = ("subject", "sort_order")
    ordering = ("sort_order", "id")
    autocomplete_fields = ("subject",)


# ==========================================================
# Question Admin
# ==========================================================

@admin.register(Question)
class QuestionAdmin(TranslatableAdmin):
    list_display = (
        "id",
        "title_any",
        "domain",
        "active",
        "allow_multiple_correct",
        "is_mode_practice",
        "is_mode_exam",
        "created_at",
    )
    list_filter = (
        "domain",
        "active",
        "allow_multiple_correct",
        "is_mode_practice",
        "is_mode_exam",
    )
    search_fields = (
        "translations__title",
        "translations__description",
        "translations__explanation",
    )
    date_hierarchy = "created_at"
    ordering = ("-pk",)

    autocomplete_fields = ("domain",)

    fieldsets = (
        (_("Référence"), {"fields": ("domain", "active")}),
        (_("Modes"), {"fields": ("is_mode_practice", "is_mode_exam")}),
        (_("Réponses"), {"fields": ("allow_multiple_correct",)}),
        (_("Traductions"), {"fields": ("title", "description", "explanation")}),
    )

    inlines = (
        QuestionSubjectInline,
        AnswerOptionInline,
        QuestionMediaInline,
    )

    def title_any(self, obj: Question) -> str:
        return obj.safe_translation_getter("title", any_language=True) or ""
    title_any.short_description = _("title")

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()
        except ValidationError as e:
            form.add_error(None, e)
            raise
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        try:
            obj.full_clean()
            obj.save()
        except ValidationError as e:
            self.message_user(
                request,
                _("Erreur de validation: %s") % e,
                level=messages.ERROR,
            )
            raise


# ==========================================================
# MediaAsset Admin (séparé)
# ==========================================================

@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "file", "external_url", "sha256", "created_at")
    list_filter = ("kind",)
    search_fields = ("external_url", "sha256")
    ordering = ("-created_at",)

    fields = ("kind", "file", "external_url", "sha256")

    def save_model(self, request, obj: MediaAsset, form, change):
        try:
            obj.full_clean()
        except ValidationError as e:
            form.add_error(None, e)
            raise
        super().save_model(request, obj, form, change)


# ==========================================================
# AnswerOption Admin (optionnel mais pratique)
# ==========================================================

@admin.register(AnswerOption)
class AnswerOptionAdmin(TranslatableAdmin):
    list_display = ("id", "question", "content_any", "is_correct", "sort_order")
    list_filter = ("is_correct",)
    search_fields = ("translations__content", "question__translations__title")
    ordering = ("question_id", "sort_order", "id")
    autocomplete_fields = ("question",)

    fields = ("question", "content", "is_correct", "sort_order")

    def content_any(self, obj: AnswerOption) -> str:
        txt = obj.safe_translation_getter("content", any_language=True) or ""
        return (txt[:60] + "…") if len(txt) > 60 else txt
    content_any.short_description = _("content")
