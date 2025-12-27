from domain.models import Domain
from rest_framework import serializers

from .models import Language


class LanguageReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = [
            "id",
            "code",
            "name",
            "active",
        ]
        read_only_fields = fields


class LanguageWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = [
            "id",
            "code",
            "name",
            "active",
        ]
        read_only_fields = ["id"]

    def validate_code(self, value: str) -> str:
        v = (value or "").strip().lower()

        # règle simple : éviter des codes bizarres
        # (si tu veux IETF complet type fr-BE, dis-le et je te mets un regex)
        if len(v) < 2 or len(v) > 10:
            raise serializers.ValidationError("Code de langue invalide (ex: fr, nl, en).")
        return v
