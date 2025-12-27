# question/models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatedFields, TranslatableModel
from subject.models import Subject


class Question(TranslatableModel):
    domain = models.ForeignKey(
        "domain.Domain",
        on_delete=models.PROTECT,
        related_name="questions", null=False)
    translations = TranslatedFields(
        title=models.CharField(_("title"), max_length=250),
        description=models.TextField(_("Description"), blank=True),
        explanation=models.TextField(_("Explanation"), blank=True)
    )
    allow_multiple_correct = models.BooleanField(
        "Plusieurs bonnes réponses ?", default=False
    )
    active = models.BooleanField(default=True)
    is_mode_practice = models.BooleanField("Pour s'exercer", default=True)
    is_mode_exam = models.BooleanField("Pour les examens", default=False)
    subjects = models.ManyToManyField(Subject, related_name="questions", through="QuestionSubject")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-pk"]

    def __str__(self):
        return self.safe_translation_getter("title", any_language=True) or f"Question#{self.pk}"

    def clean(self):
        # Règles métier sur les réponses
        opts = list(self.answer_options.all())
        if len(opts) < 2:
            raise ValidationError(_("A Question must have at least 2 possible answers."))
        correct_count = sum(1 for o in opts if o.is_correct)
        if correct_count == 0:
            raise ValidationError("Indique au moins une réponse correcte.")
        if not self.allow_multiple_correct and correct_count != 1:
            raise ValidationError(_("Only ONE answer allowed."))


class QuestionSubject(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    sort_order = models.PositiveIntegerField(default=0)
    weight = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [("question", "subject")]
        ordering = ["-pk"]

    def __str__(self):
        subj = self.subject.safe_translation_getter("name", any_language=True) or f"Subject#{self.subject_id}"
        return f"Q{self.question_id}↔{subj}(ord:{self.sort_order},w:{self.weight})"


class QuestionMedia(models.Model):
    IMAGE = "image"
    VIDEO = "video"
    EXTERNAL = "external"
    KIND_CHOICES = [(IMAGE, "Image"), (VIDEO, "Vidéo"), (EXTERNAL, "Externe")]

    question = models.ForeignKey(Question, related_name="media", on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    file = models.FileField(upload_to="question_media/", blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.kind} - {self.file or self.external_url}"

    def clean(self):
        if self.kind == self.EXTERNAL:
            if not self.external_url or self.file:
                raise ValidationError("External media requires external_url only.")
        else:
            if not self.file or self.external_url:
                raise ValidationError("File media requires file only.")


class AnswerOption(TranslatableModel):
    question = models.ForeignKey(Question, related_name="answer_options", on_delete=models.CASCADE)
    translations = TranslatedFields(content=models.TextField(_("possible answer")))  # rich text
    is_correct = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"Option(Q{self.question_id}) [{'✔' if self.is_correct else '✗'}]"
