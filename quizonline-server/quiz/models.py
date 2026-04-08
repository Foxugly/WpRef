# quiz/models.py
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import get_language
from django.utils import timezone
from django.utils.text import slugify
from config.models import AuditMixin
from question.models import Question, AnswerOption

from .constants import (
    VISIBILITY_IMMEDIATE,
    VISIBILITY_NEVER,
    VISIBILITY_SCHEDULED,
    VISIBILITY_CHOICES
)


class QuizTemplate(AuditMixin, models.Model):
    """
    Modèle de configuration de quiz (template).
    Définit le mode, le pool de questions, la durée, etc.
    """
    MODE_PRACTICE = "practice"
    MODE_EXAM = "exam"
    MODE_CHOICES = [
        (MODE_PRACTICE, "Practice"),
        (MODE_EXAM, "Examen"),
    ]

    domain = models.ForeignKey(
        "domain.Domain",
        on_delete=models.PROTECT,
        related_name="quiz_templates",
        blank=True,
        null=True,
    )

    title = models.CharField("Titre du quiz", max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    mode = models.CharField(
        max_length=10,
        choices=MODE_CHOICES,
        default=MODE_PRACTICE,  # par défaut : mode pratique
    )
    description = models.TextField("Description", blank=True)
    translations = models.JSONField(default=dict, blank=True)

    # Nombre de questions à utiliser dans ce quiz (parmi le pool)
    max_questions = models.PositiveIntegerField(
        "Nombre de questions dans le quiz",
        default=10,
        help_text="Nombre de questions à poser parmi le pool lié."
    )
    permanent = models.BooleanField("Permanent ?", default=True)

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    with_duration = models.BooleanField("Avec Timer ?", default=True)
    duration = models.PositiveIntegerField("temps (en minutes)", default=10)
    questions = models.ManyToManyField(Question,
                                       through="QuizQuestion",
                                       related_name="question",
                                       verbose_name="Pool de quizquestions"
                                       )
    result_visibility = models.CharField(
        "Visibilité du résultat global",
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_IMMEDIATE,
        help_text="Quand le score global du quiz peut être affiché à l'utilisateur.",
    )
    result_available_at = models.DateTimeField(
        "Résultat global visible à partir de",
        null=True,
        blank=True,
        help_text="Utilisé uniquement si la visibilité est 'À partir d'une date'.",
    )

    # 🔹 visibilité du détail des réponses
    detail_visibility = models.CharField(
        "Visibilité du détail des réponses",
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_IMMEDIATE,
        help_text="Quand les réponses détaillées (réponses de l'utilisateur et bonnes réponses) peuvent être affichées.",
    )
    detail_available_at = models.DateTimeField(
        "Détail visible à partir de",
        null=True,
        blank=True,
        help_text="Utilisé uniquement si la visibilité est 'À partir d'une date'.",
    )
    is_public = models.BooleanField("Public ?", default=False)
    active = models.BooleanField("Actif ?", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def normalized_translations(self) -> dict[str, dict[str, str]]:
        raw = self.translations if isinstance(self.translations, dict) else {}
        normalized: dict[str, dict[str, str]] = {}
        for lang_code, payload in raw.items():
            if not isinstance(lang_code, str) or not isinstance(payload, dict):
                continue
            normalized[lang_code] = {
                "title": str(payload.get("title", "") or ""),
                "description": str(payload.get("description", "") or ""),
            }
        return normalized

    def get_localized_content(self, language_code: str | None = None) -> dict[str, str]:
        translations = self.normalized_translations()
        candidates: list[str] = []
        if language_code:
            candidates.append(language_code)
        active_language = get_language()
        if active_language:
            candidates.append(active_language)
        candidates.extend(["fr", "en"])

        seen: set[str] = set()
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            payload = translations.get(candidate)
            if payload and (payload.get("title") or payload.get("description")):
                return {
                    "title": payload.get("title", "") or self.title or "",
                    "description": payload.get("description", "") or "",
                }

        for payload in translations.values():
            if payload.get("title") or payload.get("description"):
                return {
                    "title": payload.get("title", "") or self.title or "",
                    "description": payload.get("description", "") or "",
                }

        return {
            "title": self.title or "",
            "description": self.description or "",
        }

    def sync_translations_from_fields(self, language_code: str | None = None) -> None:
        translations = self.normalized_translations()
        preferred_language = language_code or get_language() or "fr"
        if not translations:
            translations[preferred_language] = {
                "title": self.title or "",
                "description": self.description or "",
            }
        self.translations = translations

    def sync_fields_from_translations(self, language_code: str | None = None) -> None:
        self.sync_translations_from_fields(language_code)
        localized = self.get_localized_content(language_code)
        self.title = localized["title"] or self.title or "Quiz"
        self.description = localized["description"] or ""

    def _make_unique_title(self):
        """Rend self.title unique en ajoutant un suffixe ' (n)' si nécessaire."""
        max_len = QuizTemplate._meta.get_field("title").max_length
        base = (self.title or "").strip() or "Quiz"

        qs = QuizTemplate.objects.all()
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        existing_titles = set(qs.values_list("title", flat=True))

        title = base
        counter = 1
        while title in existing_titles:
            suffix = f" ({counter})"
            title = base[: max_len - len(suffix)] + suffix
            counter += 1

        self.title = title

    def save(self, *args, **kwargs):
        preferred_language = kwargs.pop("preferred_language", None)
        original_title = self.title
        self.sync_fields_from_translations(preferred_language)
        creating = self.pk is None
        if creating:
            self._make_unique_title()
            if self.title != original_title:
                translations = self.normalized_translations()
                target_language = preferred_language or get_language() or "fr"
                payload = translations.setdefault(target_language, {"title": "", "description": ""})
                if not payload.get("title") or payload.get("title") == original_title:
                    payload["title"] = self.title
                self.translations = translations
        if not self.slug:
            base_slug = slugify(self.title) or "quiz"
            existing_slugs = set(
                QuizTemplate.objects.exclude(pk=self.pk).values_list("slug", flat=True)
            )
            slug = base_slug
            counter = 1
            while slug in existing_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def questions_count(self) -> int:
        """Nombre total de questions attachées au quiz (le pool)."""
        annotated_count = self.__dict__.get("_questions_count")
        if annotated_count is not None:
            return int(annotated_count)
        return self.questions.count()

    @property
    def can_answer(self) -> bool:

        if not self.active:
            return False
        if self.permanent:
            return True
        if self.started_at is None:
            return False
        if self.ended_at is None:
            return True
        return self.started_at <= timezone.now() <= self.ended_at

    def get_ordered_qquestions(self):
        return self.quiz_questions.select_related("question").order_by("sort_order")

    def get_ordered_questions(self):
        qs = self.questions.all().order_by("quiz_questions__sort_order")
        if self.max_questions:
            return qs[: self.max_questions]
        return qs

    def can_show_result(self, when=None) -> bool:
        """
        True si on peut afficher le score global à ce moment.
        """
        if self.mode == self.MODE_PRACTICE:
            return True

        if when is None:
            when = timezone.now()

        if self.result_visibility == VISIBILITY_NEVER:
            return False

        if self.result_visibility == VISIBILITY_IMMEDIATE:
            return True

        if self.result_visibility == VISIBILITY_SCHEDULED:
            if self.result_available_at is None:
                return False
            return when >= self.result_available_at
        return False

    # 🔹 Helpers visibilité détail réponses

    def can_show_details(self, when=None) -> bool:
        """
        True si on peut afficher le détail des réponses
        (réponses utilisateur + bonnes réponses).
        """
        if self.mode == self.MODE_PRACTICE:
            return True

        if when is None:
            when = timezone.now()

        if self.detail_visibility == VISIBILITY_NEVER:
            return False

        if self.detail_visibility == VISIBILITY_IMMEDIATE:
            return True

        if self.detail_visibility == VISIBILITY_SCHEDULED:
            if self.detail_available_at is None:
                return False
            return when >= self.detail_available_at
        return False


class QuizQuestion(models.Model):
    """
    Table de jointure Quiz <-> Question
    avec ordre et éventuellement un poids.
    """
    quiz = models.ForeignKey(QuizTemplate, on_delete=models.CASCADE, related_name="quiz_questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="quiz_questions")
    sort_order = models.PositiveIntegerField(default=0)
    weight = models.PositiveIntegerField(
        default=1,
        help_text="Poids de la question dans le score."
    )

    class Meta:
        unique_together = [("quiz", "question"), ("quiz", "sort_order")]
        ordering = ["sort_order", ]

    def __str__(self):
        return f"Q{self.question_id} (ord:{self.sort_order}, w:{self.weight})"


class Quiz(models.Model):
    """
    Une instance de quiz pour un utilisateur.
    C'est ce 'quiz_id' que tu renvoies 1à /quiz/<slug>/start/.
    """
    domain = models.ForeignKey(
        "domain.Domain",
        on_delete=models.PROTECT,
        related_name="quiz",
        blank=True,
        null=True
    )

    quiz_template = models.ForeignKey(
        "quiz.QuizTemplate",
        on_delete=models.CASCADE,
        related_name="quiz",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="quiz_user",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=False)

    def __str__(self):
        return f"Quiz {self.user} - {self.quiz_template}"

    @property
    def can_answer(self):
        if not self.active:
            return False
        if not self.started_at:
            return False
        if not self.quiz_template.can_answer:
            return False
        if self.ended_at is None:
            return True
        return self.started_at <= timezone.now() <= self.ended_at

    def expire_if_needed(self, at=None, save=True) -> bool:
        if at is None:
            at = timezone.now()

        if not self.active or not self.started_at or self.ended_at is None:
            return False

        if at < self.ended_at:
            return False

        self.active = False
        if save and self.pk:
            Quiz.objects.filter(pk=self.pk, active=True).update(active=False)
        return True

    def start(self):
        self.active = True
        self.started_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        if self.started_at and not self.ended_at and self.quiz_template.with_duration:
            if self.quiz_template.ended_at:
                self.ended_at = min(self.quiz_template.ended_at,
                                    self.started_at + timedelta(minutes=self.quiz_template.duration))
            else:
                self.ended_at = self.started_at + timedelta(minutes=self.quiz_template.duration)
        super().save(*args, **kwargs)


class QuizQuestionAnswer(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    quizquestion = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question_order = models.PositiveIntegerField()

    selected_options = models.ManyToManyField(
        AnswerOption,
        related_name="quiz_answers",
        blank=True,
    )

    given_answer = models.CharField(max_length=255, blank=True, null=True)
    is_correct = models.BooleanField(null=True, blank=True)
    earned_score = models.FloatField(default=0)
    max_score = models.FloatField(default=0)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "quizquestion"],
                name="uniq_answer_per_quiz_question",
            )
        ]
        unique_together = [("quiz", "question_order")]
        ordering = ["quiz", "question_order"]

    def clean(self):
        """
        Validation métier :
        - on ne peut créer/enregistrer une réponse
          que si la session de quiz peut encore être répondue.
        """
        super().clean()
        if not self.quiz_id:
            return

        if not self.quiz.can_answer:
            raise ValidationError("Ce quiz n'est plus disponible pour répondre.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def index(self):
        return self.quizquestion.sort_order

    @property
    def quiz_template(self):
        return self.quiz.quiz_template

    def compute_score(self, save=True):
        correct_opts = set(
            self.quizquestion.question.answer_options.filter(is_correct=True).values_list("id", flat=True)
        )
        selected = set(self.selected_options.values_list("id", flat=True))
        weight = self.quizquestion.weight
        max_score = float(weight)
        if selected == correct_opts and len(correct_opts) > 0:
            earned = max_score
            self.is_correct = True
        else:
            earned = 0.0
            self.is_correct = False
        self.earned_score = earned
        self.max_score = max_score
        if save:
            super().save(update_fields=["earned_score", "max_score", "is_correct"])
        return earned, max_score


class QuizAlertThread(models.Model):
    KIND_QUESTION = "question"
    KIND_ASSIGNMENT = "assignment"
    KIND_CHOICES = [
        (KIND_QUESTION, "Question"),
        (KIND_ASSIGNMENT, "Assignment"),
    ]
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
    ]

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="alert_threads",
    )
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default=KIND_QUESTION)
    quizquestion = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name="alert_threads",
        null=True,
        blank=True,
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reported_quiz_alert_threads",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_quiz_alert_threads",
    )
    reported_language = models.CharField(max_length=10, blank=True, default="")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)
    reporter_reply_allowed = models.BooleanField(default=False)
    last_message_at = models.DateTimeField(auto_now_add=True)
    reporter_last_read_at = models.DateTimeField(null=True, blank=True)
    owner_last_read_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="closed_quiz_alert_threads",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_message_at"]

    def __str__(self):
        return f"Alert #{self.pk} quiz={self.quiz_id} kind={self.kind} question={self.quizquestion_id}"

    @property
    def question_id(self):
        if not self.quizquestion_id:
            return None
        return self.quizquestion.question_id

    @property
    def question_order(self):
        if not self.quizquestion_id:
            return None
        return self.quizquestion.sort_order

    @property
    def question_title(self):
        if self.kind == self.KIND_ASSIGNMENT:
            from .alerting import assignment_alert_copy

            return assignment_alert_copy(self.reported_language).get("title", "New assigned quiz")
        question = self.quizquestion.question
        return question.safe_translation_getter("title", any_language=True) or f"Question #{question.pk}"

    @property
    def quiz_template_title(self):
        return self.quiz.quiz_template.title

    def is_participant(self, user) -> bool:
        from .alerting import is_alert_participant

        return is_alert_participant(self, user)

    def is_owner_user(self, user) -> bool:
        from .alerting import is_alert_owner

        return is_alert_owner(self, user)

    def is_reporter_user(self, user) -> bool:
        from .alerting import is_alert_reporter

        return is_alert_reporter(self, user)

    def can_user_reply(self, user) -> bool:
        from .alerting import can_reply_to_alert

        return can_reply_to_alert(self, user)

    def unread_for(self, user) -> bool:
        from .alerting import is_alert_unread

        return is_alert_unread(self, user)

    def unread_count_for(self, user) -> int:
        from .alerting import unread_count_for_alert

        return unread_count_for_alert(self, user)

    def mark_read_for(self, user, *, at=None, save=True) -> None:
        from .alerting import mark_alert_read

        mark_alert_read(self, user, at=at, save=save)

    def touch_last_message(self, *, at=None, save=True) -> None:
        self.last_message_at = at or timezone.now()
        if save:
            self.save(update_fields=["last_message_at"])

    def close(self, *, user=None, save=True) -> None:
        self.status = self.STATUS_CLOSED
        self.closed_at = timezone.now()
        self.closed_by = user
        if save:
            self.save(update_fields=["status", "closed_at", "closed_by"])

    def reopen(self, save=True) -> None:
        self.status = self.STATUS_OPEN
        self.closed_at = None
        self.closed_by = None
        if save:
            self.save(update_fields=["status", "closed_at", "closed_by"])


class QuizAlertMessage(models.Model):
    thread = models.ForeignKey(
        QuizAlertThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_alert_messages",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"AlertMessage #{self.pk} thread={self.thread_id} author={self.author_id}"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and self.thread_id:
            QuizAlertThread.objects.filter(pk=self.thread_id).update(last_message_at=self.created_at)
