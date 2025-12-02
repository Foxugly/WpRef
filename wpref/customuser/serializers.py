# customuser/api/serializers.py
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from quiz.models import Quiz
from .models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "last_name",
            "first_name",
            "password",
            "is_staff",
            "is_superuser",
            "is_active",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        request = self.context.get("request")
        current_user = getattr(request, "user", None)

        # Champs protégés : seulement staff/superuser peuvent les modifier
        protected_fields = ["password", "is_staff", "is_superuser", "is_active"]

        # Si l'utilisateur n'est pas staff, on interdit toute modif de ces champs
        if not (current_user and current_user.is_staff):
            forbidden = [f for f in protected_fields if f in validated_data]
            if forbidden:
                raise PermissionDenied(
                    f"Vous n'êtes pas autorisé à modifier : {', '.join(forbidden)}"
                )

        # Gestion du mot de passe (staff uniquement, vu la règle ci-dessus)
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class QuizSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ["id", "title", "slug"]


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    @staticmethod
    def validate_email(value):
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    @staticmethod
    def validate_new_password(self, value):
        validate_password(value)
        return value


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    @staticmethod
    def validate_new_password(value):
        validate_password(value)
        return value


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "first_name", "last_name", "language"]
        read_only_fields = ["id", "username"]
