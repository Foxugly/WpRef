from typing import List

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import inline_serializer, extend_schema_field
from quiz.models import Quiz
from rest_framework import serializers

from .models import CustomUser
from domain.models import Domain

User = get_user_model()

PasswordResetOKSerializer = inline_serializer(
    name="PasswordResetOK",
    fields={"detail": serializers.CharField()},
)


class CustomUserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_staff", "language", "is_superuser", "is_active"]
        read_only_fields = ["id", "is_staff", "is_superuser", "is_active"]


class CustomUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password", "language"]

    def create(self, validated_data):
        # IMPORTANT: set_password
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomUserUpdateSerializer(serializers.ModelSerializer):
    # optionnel: si tu veux permettre le changement de password via PUT/PATCH ici,
    # sinon retire le champ et garde un endpoint dédié.
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "is_active"]
        read_only_fields = []  # is_active si réservé au staff -> gère via permissions/validate

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class QuizSimpleSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        source="quiz_template.title",
        read_only=True,
    )

    class Meta:
        model = Quiz
        fields = ["id", "title", ]


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    @staticmethod
    def validate_email(value):
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate_new_password1(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["new_password1"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password2": "Les mots de passe ne correspondent pas."})
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    @staticmethod
    def validate_new_password(value):
        validate_password(value)
        return value


class MeSerializer(serializers.ModelSerializer):
    current_domain_title = serializers.CharField(source="current_domain.title", read_only=True)

    owned_domain_ids = serializers.SerializerMethodField()
    managed_domain_ids = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "language",
            "is_superuser",
            "is_staff",
            "current_domain",  # ✅ id ou null
            "current_domain_title",
            "owned_domain_ids",
            "managed_domain_ids",
        ]
        read_only_fields = ["id", "username"]

    def get_owned_domain_ids(self, obj) -> List[int]:
        return list(obj.owned_domains.values_list("id", flat=True))

    def get_managed_domain_ids(self, obj) -> List[int]:
        return list(obj.managed_domains.values_list("id", flat=True))

class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "language",
        ]

class SetCurrentDomainSerializer(serializers.Serializer):
    domain_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        user = self.context["request"].user

        # reset
        if "domain_id" not in attrs or attrs["domain_id"] is None:
            attrs["domain"] = None
            return attrs

        domain = Domain.objects.filter(id=attrs["domain_id"]).first()
        if not domain:
            raise serializers.ValidationError({"domain_id": "Domain not found."})

        if not user.can_manage_domain(domain):
            raise serializers.ValidationError({"domain_id": "Forbidden for this domain."})

        attrs["domain"] = domain
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.current_domain = self.validated_data["domain"]
        user.save(update_fields=["current_domain"])
        return user