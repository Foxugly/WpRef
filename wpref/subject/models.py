from django.db import models

from domain.models import Domain


class Subject(models.Model):
    name = models.CharField("Nom", max_length=120, unique=True)
    description = models.TextField("Description", blank=True)
    domain = models.ForeignKey(
        Domain,
        on_delete=models.PROTECT,
        related_name="subjects", blank=True, null=True
    )

    class Meta:
        ordering = ["-pk"]

    def __str__(self): return self.name

