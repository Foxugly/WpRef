from typing import List

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from domain.models import Domain
from quiz.models import Quiz
from rest_framework import serializers

User = get_user_model()


class PasswordResetOKSerializer(serializers.Serializer):
    detail = serializers.CharField()


class StrictFieldsModelSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        unknown = set(self.initial_data.keys()) - set(self.fields.keys())
        if unknown:
            raise serializers.ValidationError(
                {field: "This field is not allowed." for field in sorted(unknown)}
            )
        return attrs


class CustomUserReadSerializer(serializers.ModelSerializer):
    password_change_required = serializers.BooleanField(source="requires_password_change", read_only=True)
    current_domain_title = serializers.SerializerMethodField()
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
            "email_confirmed",
            "password_change_required",
            "is_superuser",
            "is_staff",
            "is_active",
            "current_domain",
            "current_domain_title",
            "owned_domain_ids",
            "managed_domain_ids",
        ]
        read_only_fields = [
            "id",
            "username",
            "email_confirmed",
            "password_change_required",
            "is_staff",
            "is_superuser",
            "is_active",
        ]

    def get_current_domain_title(self, obj) -> str:
        domain = getattr(obj, "current_domain", None)
        if domain is None:
            return ""
        return domain.safe_translation_getter("name", any_language=True) or ""

    @staticmethod
    def _related_ids(obj, relation_name: str) -> List[int]:
        cache = getattr(obj, "_prefetched_objects_cache", {})
        if relation_name in cache:
            return [related.id for related in cache[relation_name]]
        return list(getattr(obj, relation_name).values_list("id", flat=True))

    def get_owned_domain_ids(self, obj) -> List[int]:
        return self._related_ids(obj, "owned_domains")

    def get_managed_domain_ids(self, obj) -> List[int]:
        return self._related_ids(obj, "linked_domains")


class CustomUserCreateSerializer(StrictFieldsModelSerializer):
    password = serializers.CharField(write_only=True)
    managed_domain_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
        write_only=True,
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password", "language", "managed_domain_ids"]

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate_managed_domain_ids(self, value: List[int]) -> List[int]:
        domain_ids = sorted(set(value))
        domains = Domain.objects.filter(id__in=domain_ids, active=True)
        found_ids = set(domains.values_list("id", flat=True))
        missing_ids = [domain_id for domain_id in domain_ids if domain_id not in found_ids]
        if missing_ids:
            raise serializers.ValidationError(
                f"Unknown or inactive domain id(s): {', '.join(map(str, missing_ids))}."
            )
        return domain_ids

    def create(self, validated_data):
        managed_domain_ids = validated_data.pop("managed_domain_ids", [])
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.email_confirmed = False
        user.set_password(password)
        user.save()
        if managed_domain_ids:
            user.linked_domains.set(Domain.objects.filter(id__in=managed_domain_ids, active=True))
            user.ensure_current_domain_is_valid(auto_fix=True)
        return user


class CustomUserProfileUpdateSerializer(StrictFieldsModelSerializer):
    managed_domain_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "language", "managed_domain_ids"]

    def validate_managed_domain_ids(self, value: List[int]) -> List[int]:
        domain_ids = sorted(set(value))
        domains = Domain.objects.filter(id__in=domain_ids, active=True)
        found_ids = set(domains.values_list("id", flat=True))
        missing_ids = [domain_id for domain_id in domain_ids if domain_id not in found_ids]
        if missing_ids:
            raise serializers.ValidationError(
                f"Unknown or inactive domain id(s): {', '.join(map(str, missing_ids))}."
            )
        return domain_ids

    def update(self, instance, validated_data):
        managed_domain_ids = validated_data.pop("managed_domain_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if managed_domain_ids is not None:
            instance.linked_domains.set(Domain.objects.filter(id__in=managed_domain_ids, active=True))
            instance.ensure_current_domain_is_valid(auto_fix=True)
        return instance


class CustomUserAdminUpdateSerializer(StrictFieldsModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    password_change_required = serializers.BooleanField(required=False, source="must_change_password")

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "language",
            "password",
            "is_active",
            "password_change_required",
        ]

    def validate_password(self, value: str) -> str:
        validate_password(value, user=self.instance)
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
            instance.must_change_password = True
        instance.save()
        return instance


class QuizSimpleSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        source="quiz_template.title",
        read_only=True,
    )

    class Meta:
        model = Quiz
        fields = ["id", "title"]


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


class EmailConfirmationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    @staticmethod
    def validate_new_password(value):
        validate_password(value)
        return value


class SetCurrentDomainSerializer(serializers.Serializer):
    domain_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        user = self.context["request"].user

        if "domain_id" not in attrs or attrs["domain_id"] is None:
            attrs["domain"] = None
            return attrs

        domain = Domain.objects.filter(id=attrs["domain_id"]).first()
        if not domain:
            raise serializers.ValidationError({"domain_id": "Domain not found."})

        if not user.get_visible_domains(active_only=False).filter(id=domain.id).exists():
            raise serializers.ValidationError({"domain_id": "Forbidden for this domain."})

        attrs["domain"] = domain
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.current_domain = self.validated_data["domain"]
        user.save(update_fields=["current_domain"])
        return user
