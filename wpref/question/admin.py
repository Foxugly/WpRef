from django.contrib import admin
from subject.models import Subject

from .models import Question, QuestionMedia, AnswerOption, QuestionSubject


@admin.register(QuestionMedia)
class QuestionMediaAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "file", "external_url", "sort_order")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", )
    search_fields = ("name",)


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "content", "is_correct", "sort_order")
    list_filter = ("is_correct", "question")
    search_fields = ("content", "question__title")
    autocomplete_fields = ["question"]


class QuestionSubjectInline(admin.TabularInline):
    model = QuestionSubject
    extra = 0
    autocomplete_fields = ["subject"]
    ordering = ("sort_order", "id",)


class AnswerOptionInline(admin.StackedInline):
    model = AnswerOption
    extra = 2


class QuestionMediaInline(admin.StackedInline):
    model = QuestionMedia
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("title", "allow_multiple_correct", "active", "is_mode_practice", "is_mode_exam", "created_at")
    list_filter = ("allow_multiple_correct", "active", "is_mode_practice", "is_mode_exam",
                   "subjects")  # OK: on peut filtrer dessus
    search_fields = ("title",)
    inlines = [QuestionMediaInline, AnswerOptionInline, QuestionSubjectInline]
    # ⚠️ Supprimer ceci, c'est la cause de l'erreur :
    # filter_horizontal = ("subjects",)


# (Optionnel) si tu veux pouvoir éditer la table de liaison directement
@admin.register(QuestionSubject)
class QuestionSubjectAdmin(admin.ModelAdmin):
    list_display = ("question", "subject", "sort_order", "weight")
    list_filter = ("subject",)
    search_fields = ("question__title", "subject__name")
    autocomplete_fields = ["question", "subject"]
