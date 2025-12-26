from typing import List

from django.conf import settings
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Domain

User = get_user_model()
LANG_CODES = {code for code, _ in settings.LANGUAGES}


class DomainSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    staff_ids = serializers.PrimaryKeyRelatedField(
        source="staff",
        queryset=User.objects.all(),
        many=True,
        required=False
    )
    staff_usernames = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Domain
        fields = [
            "id",
            "name",
            "description",
            "allowed_languages",
            "active",
            "owner",
            "owner_username",
            "staff_ids",
            "staff_usernames",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "owner"]

    def get_staff_usernames(self, obj) -> List[str]:
        return list(obj.staff.values_list("username", flat=True))

    def validate_allowed_languages(self, value):
        value = value or []
        invalid = [c for c in value if c not in LANG_CODES]
        if invalid:
            raise serializers.ValidationError(f"Invalid language code(s): {', '.join(invalid)}")
        return list(dict.fromkeys(value))  # dédup
