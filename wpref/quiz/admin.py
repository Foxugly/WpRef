from django.contrib import admin

from .models import QuizTemplate, QuizQuestion, Quiz, QuizQuestionAnswer


class QuizQuestionInline(admin.TabularInline):
    """
    Inline pour gérer les QuizQuestion directement depuis le QuizTemplate.
    Permet d'ordonner les questions, ajuster le poids, etc.
    """
    model = QuizQuestion
    extra = 1
    autocomplete_fields = ["question"]
    fields = ("question", "sort_order", "weight")
    ordering = ("sort_order",)
    verbose_name = "Question du quiz"
    verbose_name_plural = "Questions du quiz"


@admin.register(QuizTemplate)
class QuizTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "domain",
        "mode",
        "active",
        "permanent",
        "with_duration",
        "duration",
        "started_at",
        "ended_at",
        "questions_count",
        "result_visibility",
        "result_available_at",
        "detail_visibility",
        "detail_available_at",
        "created_at",
    )
    list_filter = (
        "domain",
        "mode",
        "active",
        "permanent",
        "with_duration",
        "result_visibility",
        "detail_visibility",
        "created_at",
    )
    search_fields = ("title", "description")
    inlines = [QuizQuestionInline]
    readonly_fields = ("slug", "created_at", "questions_count")
    ordering = ("title",)
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {
            "fields": ("title", "slug", "description", "domain", "mode"),
        }),
        ("Configuration", {
            "fields": (
                "max_questions",
                "permanent",
                "active",
            ),
        }),
        ("Fenêtre de disponibilité", {
            "fields": ("started_at", "ended_at"),
        }),
        ("Durée / timer", {
            "fields": ("with_duration", "duration"),
        }),
        ("Résultat global", {
            "fields": ("result_visibility", "result_available_at"),
            "description": (
                "Contrôle quand le score global (note) est visible pour l'utilisateur."
            ),
        }),
        # 🔹 nouveau bloc : visibilité du détail des réponses
        ("Détail des réponses", {
            "fields": ("detail_visibility", "detail_available_at"),
            "description": (
                "Contrôle quand les réponses détaillées (réponses données + bonnes réponses) sont visibles."
            ),
        }),
        ("Meta", {
            "fields": ("created_at",),
        }),
    )


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    """
    Admin dédié au modèle de jointure, pratique pour déboguer ou gérer en masse.
    """
    list_display = ("quiz", "question", "sort_order", "weight")
    list_filter = ("quiz",)
    search_fields = ("quiz__title", "question__title")
    ordering = ("quiz__title", "sort_order")
    autocomplete_fields = ["quiz", "question"]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """
    Représente une session de quiz pour un utilisateur.
    """
    list_display = (
        "pk",
        "quiz_template",
        "get_user_display",
        "domain",
        "active",
        "started_at",
        "ended_at",
        "created_at",
        "is_currently_answerable",
    )
    list_filter = (
        "active",
        "domain",
        "quiz_template",
        "quiz_template__mode",
        "created_at",
    )
    search_fields = (
        "quiz_template__title",
        "user__username",
        "user__first_name",
        "user__last_name",
    )
    readonly_fields = ("created_at",)
    autocomplete_fields = ["quiz_template", "user"]
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def get_user_display(self, obj):
        if obj.user:
            full_name = obj.user.get_full_name()
            return full_name or obj.user.username
        return "Anonyme"

    get_user_display.short_description = "Utilisateur"

    def is_currently_answerable(self, obj):
        return obj.can_answer

    is_currently_answerable.boolean = True
    is_currently_answerable.short_description = "Encore répondable ?"


@admin.register(QuizQuestionAnswer)
class QuizQuestionAnswerAdmin(admin.ModelAdmin):
    """
    Réponses aux questions d'une session.
    Permet de voir rapidement qui a répondu quoi et le score.
    """
    list_display = (
        "quiz",
        "get_user_display",
        "get_quiz_template",
        "get_question_title",
        "question_order",
        "is_correct",
        "earned_score",
        "max_score",
        "answered_at",
    )
    list_filter = (
        "is_correct",
        "quiz__quiz_template",
        "quiz__quiz_template__mode",
        "answered_at",
    )
    search_fields = (
        "quiz__quiz_template__title",
        "quiz__user__username",
        "quiz__user__first_name",
        "quiz__user__last_name",
        "quizquestion__question__title",
    )
    autocomplete_fields = ["quiz", "quizquestion", "selected_options"]
    date_hierarchy = "answered_at"
    ordering = ("-answered_at",)

    def get_user_display(self, obj):
        user = obj.quiz.user
        if user:
            full_name = user.get_full_name()
            return full_name or user.username
        return "Anonyme"

    get_user_display.short_description = "Utilisateur"

    def get_quiz_template(self, obj):
        return obj.quiz_template

    get_quiz_template.short_description = "Quiz template"

    def get_question_title(self, obj):
        return obj.quizquestion.question.title

    get_question_title.short_description = "Question"
