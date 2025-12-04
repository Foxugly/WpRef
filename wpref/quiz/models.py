# quiz/models.py
from django.db import models
from django.utils.text import slugify
import uuid
from django.utils import timezone
from question.models import Question, AnswerOption
from django.conf import settings
from datetime import timedelta


class Quiz(models.Model):
    MODE_PRACTICE = "practice"
    MODE_EXAM = "exam"
    MODE_CHOICES = [
        (MODE_PRACTICE, "Practice"),
        (MODE_EXAM, "Examen"),
    ]

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

    is_active = models.BooleanField("Actif ?", default=True)
    with_duration = models.BooleanField("Avec Timer ?", default=True)
    duration = models.PositiveIntegerField("temps (en minutes)",default=10)

    # Pool de questions possibles pour ce quiz
    questions = models.ManyToManyField(
        Question,
        through="QuizQuestion",
        related_name="quizzes",
        verbose_name="Pool de questions"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "quiz"
            slug = base_slug
            counter = 1

            # Boucle tant qu'un quiz avec ce slug existe déjà
            while Quiz.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def questions_count(self) -> int:
        """Nombre total de questions attachées au quiz (le pool)."""
        return self.questions.count()

    def get_ordered_questions(self):
        """
        Retourne les questions du quiz dans l'ordre,
        limité à `max_questions`.
        """
        qs = (
            self.questions
            .all()
            .order_by("quizquestion__sort_order", "quizquestion__id")
        )
        if self.max_questions and qs.count() > self.max_questions:
            return qs[: self.max_questions]
        return qs


class QuizQuestion(models.Model):
    """
    Table de jointure Quiz <-> Question
    avec ordre et éventuellement un poids.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="quiz_questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="quiz_questions")
    sort_order = models.PositiveIntegerField(default=0)
    weight = models.PositiveIntegerField(
        default=1,
        help_text="Poids de la question dans le score."
    )

    class Meta:
        unique_together = [("quiz", "question")]
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"Quiz {self.quiz_id} ↔ Q{self.question_id} (ord:{self.sort_order}, w:{self.weight})"

class QuizSession(models.Model):
    """
    Une instance de quiz pour un utilisateur (ou anonyme).
    C'est ce 'quiz_id' que tu renvoies 1à /quiz/<slug>/start/.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="sessions")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="quiz_sessions",
    )
    # ✅ date de début du quiz (stocke la date actuelle)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    # ✅ booléen pour savoir si le quiz est clôturé
    is_closed = models.BooleanField(default=False)
    # ✅ durée maximale du quiz (par défaut 10 minutes)

    def __str__(self):
        return f"Session {self.user} - {self.quiz}"

    @property
    def expires_at(self):
        if self.expired_at:
            return self.expired_at
        return None

    @property
    def is_expired(self):
        if self.expired_at :
            return timezone.now() > self.expires_at
        return None

    @property
    def is_done(self):
        return self.is_expired or self.is_closed

    def can_answer(self):
        """Petit helper pratique dans les vues."""
        return not self.is_closed and not self.is_expired

    def save(self, *args, **kwargs):
        if self.started_at and not self.expired_at:
            self.expired_at = self.started_at + timedelta(minutes=self.quiz.duration)
        super().save(*args, **kwargs)

class QuizAttempt(models.Model):
    """
    Réponse à une question dans une session de quiz.

    C'est ce modèle qui est utilisé par :
      - QuizAttemptSerializer
      - QuizAttemptView (/quiz/<quiz_id>/attempt/<question_order>/)

    → 1 ligne = 1 question répondue pour une session donnée.
    """
    session = models.ForeignKey(
        QuizSession,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    question_order = models.PositiveIntegerField()

    # Réponse donnée (à adapter selon ton type de questions :
    # lettre "A/B/C", id d'option, texte libre, etc.)
    given_answer = models.CharField(max_length=255, blank=True, null=True)

    # Calculé éventuellement (True/False)
    is_correct = models.BooleanField(null=True, blank=True)

    answered_at = models.DateTimeField(auto_now_add=True)

    @property
    def quiz(self):
        return self.session.quiz
    
    class Meta:
        unique_together = [("session", "question_order")]
        ordering = ["session", "question_order"]

    def __str__(self):
        return f"Session {self.session_id} - Q{self.question_order} ({self.question_id})"


class QuizAnswer(models.Model):
    """
    Réponse d'un utilisateur à une question dans une tentative de quiz.
    Possibilité de cocher plusieurs options (car Question.allow_multiple_correct).
    """
    attempt = models.ForeignKey(
        QuizAttempt,
        related_name="answers",
        on_delete=models.CASCADE,
    )
    question = models.ForeignKey(
        Question,
        related_name="quiz_answers",
        on_delete=models.CASCADE,
    )

    # Ce que l'utilisateur a sélectionné
    selected_options = models.ManyToManyField(
        AnswerOption,
        related_name="quiz_answers",
        blank=True,
    )

    # Cache de scoring par question (optionnel mais pratique)
    earned_score = models.FloatField(default=0)
    max_score = models.FloatField(default=0)

    class Meta:
        unique_together = [("attempt", "question")]

    def __str__(self):
        return f"Attempt {self.attempt_id} - Q{self.question_id}"

    def compute_score(self, save: bool = True):
        """
        Compare les options sélectionnées aux bonnes réponses.
        Si l'utilisateur a exactement le même set de bonnes réponses,
        il gagne `weight` points, sinon 0.
        """
        # 1. Récupérer les bonnes réponses pour cette question
        correct_opts = set(
            self.question.answer_options.filter(is_correct=True).values_list("id", flat=True)
        )
        # 2. Récupérer ce que l'utilisateur a coché
        selected = set(
            self.selected_options.values_list("id", flat=True)
        )

        # 3. Poids de la question dans le quiz
        try:
            quiz_question = QuizQuestion.objects.get(
                quiz=self.attempt.quiz,
                question=self.question,
            )
            weight = quiz_question.weight
        except QuizQuestion.DoesNotExist:
            # fallback si pas de QuizQuestion (par sécurité)
            weight = 1

        # max_score pour cette question
        max_score = float(weight)

        # scoring : tout ou rien pour l’instant
        if selected == correct_opts and len(correct_opts) > 0:
            earned = max_score
        else:
            earned = 0.0

        self.earned_score = earned
        self.max_score = max_score

        if save:
            self.save(update_fields=["earned_score", "max_score"])

        return earned, max_score