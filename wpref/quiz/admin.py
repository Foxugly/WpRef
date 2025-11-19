# quiz/admin.py
from django.contrib import admin

from .models import (
    Quiz,
    QuizQuestion,
    QuizSession,
    QuizAttempt,
    QuizAnswer,
)


# ============================================================
# Inlines
# ============================================================

class QuizQuestionInline(admin.TabularInline):
    """
    Permet de gérer les QuizQuestion directement dans l’admin du Quiz.
    """
    model = QuizQuestion
    extra = 1
    autocomplete_fields = ["question"]
    ordering = ("sort_order",)
    fields = ("question", "sort_order", "weight")


class QuizAnswerInline(admin.TabularInline):
    """
    Réponses détaillées pour une tentative de quiz.
    (en lecture seule si tu veux éviter les manipulations manuelles)
    """
    model = QuizAnswer
    extra = 0
    filter_horizontal = ["selected_options"]
    readonly_fields = ("earned_score", "max_score")


# ============================================================
# Quiz
# ============================================================

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "mode",
        "is_active",
        "questions_count",
        "created_at",
    )
    list_filter = ("mode", "is_active", "created_at")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [QuizQuestionInline]
    readonly_fields = ("questions_count", "created_at")
    fieldsets = (
        (None, {
            "fields": ("title", "slug", "mode", "description"),
        }),
        ("Configuration", {
            "fields": ("max_questions", "is_active"),
        }),
        ("Métadonnées", {
            "fields": ("questions_count", "created_at"),
        }),
    )


# ============================================================
# QuizSession
# ============================================================

@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "quiz",
        "user",
        "started_at",
        "is_closed",
        "is_expired_admin",
        "max_duration",
    )
    list_filter = ("quiz", "is_closed", "started_at")
    search_fields = ("id", "quiz__title", "user__username", "user__email")
    readonly_fields = ("started_at", "expires_at_admin")

    fieldsets = (
        (None, {
            "fields": ("quiz", "user"),
        }),
        ("État", {
            "fields": ("started_at", "max_duration", "is_closed", "expires_at_admin"),
        }),
    )

    @admin.display(description="Expire à")
    def expires_at_admin(self, obj):
        return obj.expires_at

    @admin.display(boolean=True, description="Expiré ?")
    def is_expired_admin(self, obj):
        return obj.is_expired


# ============================================================
# QuizAttempt
# ============================================================

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session",
        "question",
        "question_order",
        "is_correct",
        "answered_at",
    )
    list_filter = ("is_correct", "answered_at", "question")
    search_fields = (
        "id",
        "session__id",
        "session__quiz__title",
        "question__title",
        "session__user__username",
        "session__user__email",
    )
    readonly_fields = ("answered_at",)
    inlines = [QuizAnswerInline]


# ============================================================
# QuizAnswer
# ============================================================

@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "attempt",
        "question",
        "earned_score",
        "max_score",
    )
    list_filter = ("question",)
    search_fields = (
        "id",
        "attempt__id",
        "attempt__session__quiz__title",
        "question__title",
    )
    filter_horizontal = ["selected_options"]
