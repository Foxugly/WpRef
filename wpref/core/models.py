from django.db import models
from django.utils import timezone


class OutboundEmail(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()
    recipients = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    available_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at", "id"]

    def mark_attempt(self) -> None:
        self.attempts += 1

