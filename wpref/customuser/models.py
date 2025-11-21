from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    language = models.CharField(_("language"), max_length=8, choices=settings.LANGUAGES, default=settings.LANGUAGES[0][0])

    def __str__(self):
        return self.username if not (self.first_name and self.last_name) else self.get_full_name()

    def get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)
