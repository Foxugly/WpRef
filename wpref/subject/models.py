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