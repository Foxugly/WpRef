import logging

from django.conf import settings
from django.http import Http404
from drf_spectacular.utils import inline_serializer
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.exceptions import NotFound

logger = logging.getLogger(__name__)

ErrorDetailSerializer = inline_serializer(
    name="ErrorDetail",
    fields={
        "detail": serializers.CharField(required=False),
    },
)


def mask_sensitive_data(data):
    """
    Masque récursivement les champs sensibles dans dicts & listes.
    """
    if isinstance(data, dict):
        return {
            key: "***MASKED***"
            if key.lower() in settings.SENSITIVE_FIELDS
            else mask_sensitive_data(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]

    return data


class MyModelViewSet(viewsets.ModelViewSet):
    def _log_call(self, *, method_name: str, endpoint: str, input_expected: str, output: str,
                  extra: dict | None = None):
        """
        Log standardisé pour tracer :
        - endpoint
        - input/output
        - user
        - action
        - payload (prudent) + params
        """
        user_id = getattr(getattr(self.request, "user", None), "id", None)
        action = getattr(self, "action", None)

        try:
            masked_payload = mask_sensitive_data(self.request.data)
        except Exception:
            masked_payload = "<unreadable>"

        logger.info(
            "[%s] action=%s user=%s endpoint=%s input=%s output=%s payload_keys=%s params=%s extra=%s",
            method_name,
            action,
            user_id,
            endpoint,
            input_expected,
            output,
            masked_payload,
            dict(getattr(self.request, "query_params", {})),
            extra or {},
        )

    def handle_exception(self, exc):
        """
        Loggue l'exception avec contexte supplémentaire.
        """
        logger.exception(
            "Erreur dans %s (action=%s, user=%s)",
            self.__class__.__name__,
            getattr(self, "action", None),
            getattr(self.request.user, "id", None),
        )
        if isinstance(exc, Http404):
            exc = NotFound()  # ou NotFound("Not found.")
        return super().handle_exception(exc)
