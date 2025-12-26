# quiz/models.py
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from question.models import Question, AnswerOption

from .constants import (
    VISIBILITY_IMMEDIATE,
    VISIBILITY_NEVER,
    VISIBILITY_SCHEDULED,
    VISIBILITY_CHOICES
)


class QuizTemplate(models.Model):
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
        default=MODE_PRACTICE,  # par défaut : mode examen
    )
    description = models.TextField("Description", blank=True)

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
    active = models.BooleanField("Actif ?", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def _make_unique_title(self):
        """Rend self.title unique en ajoutant un suffixe ' (n)' si nécessaire."""
        base = (self.title or "").strip() or "Quiz"
        title = base
        counter = 1

        # exclure self.pk (update)
        qs = QuizTemplate.objects.all()
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        while qs.filter(title=title).exists():
            title = f"{base} ({counter})"
            counter += 1

        self.title = title

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if creating:
            self._make_unique_title()
        if not self.slug:
            base_slug = slugify(self.title) or "quiz"
            slug = base_slug
            counter = 1

            # Boucle tant qu'un quiz avec ce slug existe déjà
            while QuizTemplate.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def questions_count(self) -> int:
        """Nombre total de questions attachées au quiz (le pool)."""
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
        "quiz.quizTemplate",
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
