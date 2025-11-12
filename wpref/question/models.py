# question/models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

class Subject(models.Model):
    name = models.CharField("Nom", max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField("Description", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self): return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Question(models.Model):
    title = models.CharField("Titre", max_length=255)
    description = models.TextField("Description", blank=True)   # rich text
    explanation = models.TextField("Explication", blank=True)   # rich text
    allow_multiple_correct = models.BooleanField(
        "Plusieurs bonnes réponses ?", default=False
    )
    subjects = models.ManyToManyField(Subject, related_name="questions", through="QuestionSubject")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self): return self.title

    def clean(self):
        # Règles métier sur les réponses
        opts = list(self.answer_options.all())
        if len(opts) < 2:
            raise ValidationError("Une question doit avoir au moins 2 réponses possibles.")
        correct_count = sum(1 for o in opts if o.is_correct)
        if correct_count == 0:
            raise ValidationError("Indique au moins une réponse correcte.")
        if not self.allow_multiple_correct and correct_count != 1:
            raise ValidationError("Cette question n'autorise qu'une seule bonne réponse.")

class QuestionSubject(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    subject  = models.ForeignKey(Subject,  on_delete=models.CASCADE)
    sort_order = models.PositiveIntegerField(default=0)
    weight     = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [("question", "subject")]
        ordering = ["subject__name", "sort_order", "id"]

    def __str__(self):
        return f"Q{self.question_id}↔{self.subject.name}(ord:{self.sort_order},w:{self.weight})"

class QuestionMedia(models.Model):
    IMAGE = "image"
    VIDEO = "video"
    KIND_CHOICES = [(IMAGE, "Image"), (VIDEO, "Vidéo")]

    question = models.ForeignKey(Question, related_name="media", on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    file = models.FileField(upload_to="question_media/", blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)
    caption = models.CharField("Légende", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.kind} - {self.caption or self.file or self.external_url}"

    def clean(self):
        if not self.file and not self.external_url:
            raise ValidationError("Fournis un fichier ou une URL externe.")

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, related_name="answer_options", on_delete=models.CASCADE)
    content = models.TextField("Texte de la réponse")  # rich text
    is_correct = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"Option(Q{self.question_id}) [{'✔' if self.is_correct else '✗'}]"
