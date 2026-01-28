# question/models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint, Q
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
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-pk"]

    def __str__(self):
        title = self.safe_translation_getter("title", any_language=True)
        if title:
            return title
        return f"Question#{self.pk}"


class QuestionSubject(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            UniqueConstraint(fields=["question", "subject"], name="uniq_question_subject")
        ]

    def __str__(self):
        subj = self.subject.safe_translation_getter("name", any_language=True) or f"Subject#{self.subject_id}"
        return f"Q{self.question_id}↔{subj}(ord:{self.sort_order})"


class MediaAsset(models.Model):
    IMAGE = "image"
    VIDEO = "video"
    EXTERNAL = "external"
    KIND_CHOICES = [(IMAGE, "Image"), (VIDEO, "Vidéo"), (EXTERNAL, "Externe")]

    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    file = models.FileField(upload_to="question_media/", blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)

    # dédup (sha256 hex 64)
    sha256 = models.CharField(max_length=64, blank=True, null=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["kind", "sha256"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["kind", "sha256"],
                condition=Q(sha256__isnull=False),
                name="uniq_mediaasset_kind_sha256_notnull",
            )
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean(self):
        file_present = bool(self.file and getattr(self.file, "name", ""))

        if self.kind == self.EXTERNAL:
            # EXTERNAL: url obligatoire + interdit file + interdit sha256 (optionnel mais conseillé)
            if not self.external_url or file_present:
                raise ValidationError("External media requires external_url only.")
            if self.sha256:
                raise ValidationError("External media must not have sha256.")
        else:
            # FILE: file obligatoire + interdit external_url + sha256 obligatoire
            if not file_present or self.external_url:
                raise ValidationError("File media requires file only.")
            if not self.sha256:
                raise ValidationError("File media requires sha256.")

    def __str__(self):
        return f"{self.kind} - {self.file or self.external_url}"

class QuestionMedia(models.Model):
    question = models.ForeignKey(Question, related_name="media", on_delete=models.CASCADE)
    asset = models.ForeignKey(MediaAsset, related_name="question_links", on_delete=models.PROTECT)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            UniqueConstraint(fields=["question", "asset"], name="uniq_question_media_asset")
        ]

    def __str__(self):
        return f"Q{self.question_id} → Asset#{self.asset_id} (ord:{self.sort_order})"



class AnswerOption(TranslatableModel):
    question = models.ForeignKey(Question, related_name="answer_options", on_delete=models.CASCADE)
    translations = TranslatedFields(content=models.TextField(_("possible answer")))  # rich text
    is_correct = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Option(Q{self.question_id}) [{'✔' if self.is_correct else '✗'}]"
