from django.contrib import admin
from .models import Subject, Question, QuestionMedia, AnswerOption, QuestionSubject

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

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
    list_display = ("title", "allow_multiple_correct", "created_at")
    list_filter = ("allow_multiple_correct", "subjects")  # OK: on peut filtrer dessus
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
