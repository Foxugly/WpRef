from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from language.models import Language
from language.serializers import LanguageReadSerializer
from rest_framework import serializers

from .models import Domain
from subject.serializers import SubjectReadSerializer

User = get_user_model()
LANG_CODES = {code for code, _ in settings.LANGUAGES}


class DomainReadSerializer(serializers.ModelSerializer):
    translations = serializers.SerializerMethodField()
    allowed_languages = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    staff = serializers.SerializerMethodField()

    class Meta:
        model = Domain
        fields = [
            "id",
            "translations",
            "allowed_languages",
            "active",
            "owner",
            "staff",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
        extra_kwargs = {"owner": {"read_only": True}}

    def get_translations(self, obj: Domain) -> dict[str, dict[str, str]]:
        data = {}
        for t in obj.translations.all():
            data[t.language_code] = {"name": t.name or "", "description": t.description or ""}
        return data

    def get_owner(self, obj: Domain) -> dict[str, int | str]:
        return {"id": obj.owner_id, "username": obj.owner.username}

    def get_staff(self, obj: Domain) -> list[dict[str, int | str]]:
        return [{"id": u.id, "username": u.username} for u in obj.staff.all()]

    @extend_schema_field(LanguageReadSerializer(many=True))
    def get_allowed_languages(self, obj: Domain) -> list[dict]:
        qs = obj.allowed_languages.filter(active=True).order_by("id")
        return LanguageReadSerializer(qs, many=True, context=self.context).data

    def validate(self, attrs):
        raise serializers.ValidationError("This serializer is read-only.")


class DomainWriteSerializer(serializers.ModelSerializer):
    allowed_languages = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True, required=True)
    translations = serializers.DictField(child=serializers.DictField(), write_only=True, required=True)
    staff = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=True)

    class Meta:
        model = Domain
        fields = [
            "translations",
            "allowed_languages",
            "active",
            "staff",
        ]
        # read_only_fields = ["id"]

    # ---------------------------
    # helpers
    # ---------------------------
    def _apply_translations(self, domain: Domain, translations: dict) -> None:
        for lang_code, data in (translations or {}).items():
            domain.set_current_language(lang_code)
            domain.name = data.get("name", "")
            domain.description = data.get("description", "")
            domain.save()

    # ---------------------------
    # validation
    # ---------------------------
    def validate_allowed_languages(self, value: list[Language]) -> list[Language]:
        seen_ids = set()
        unique_languages = []
        for lang in value:
            if lang.pk in seen_ids:
                continue
            seen_ids.add(lang.pk)
            unique_languages.append(lang)

        # Validation : code doit exister dans settings.LANGUAGES
        invalid = [lang.code for lang in unique_languages if lang.code not in LANG_CODES]
        if invalid:
            raise serializers.ValidationError(
                f"Invalid language code(s): {', '.join(sorted(invalid))}"
            )

        return unique_languages

    def validate(self, attrs):
        translations = attrs.get("translations")
        if not translations:
            raise serializers.ValidationError({"translations": "Au moins une traduction est requise."})

        allowed_langs = attrs.get("allowed_languages")
        if "allowed_languages" in attrs and allowed_langs == []:
            raise serializers.ValidationError({"allowed_languages": "Au moins une langue est requise."})
        if allowed_langs is not None:
            allowed_codes = {l.code for l in allowed_langs}
            provided = set(translations.keys())
            invalid_codes = provided - LANG_CODES
            if invalid_codes:
                raise serializers.ValidationError({"translations": f"Langues inconnues: {sorted(invalid_codes)}"})

            missing = allowed_codes - provided
            if missing:
                raise serializers.ValidationError(
                    {"translations": f"Traductions manquantes pour: {sorted(missing)}"}
                )

        return attrs

    # ---------------------------
    # create / update
    # ---------------------------
    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not request.user or request.user.is_anonymous:
            raise serializers.ValidationError({"owner": "Owner is required."})
        translations = validated_data.pop("translations")
        langs = validated_data.pop("allowed_languages", [])
        staff = validated_data.pop("staff", [])
        with transaction.atomic():
            domain = Domain.objects.create(owner=request.user, **validated_data)
            if staff:
                domain.staff.set(staff)
            if langs:
                domain.allowed_languages.set(langs)
            self._apply_translations(domain, translations)
        return domain

    def update(self, instance, validated_data):
        translations = validated_data.pop("translations", None)
        langs = validated_data.pop("allowed_languages", None)
        staff = validated_data.pop("staff", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        with transaction.atomic():
            if staff is not None:
                instance.staff.set(staff)

            if langs is not None:
                instance.allowed_languages.set(langs)

            if translations is not None:
                self._apply_translations(instance, translations)

        return instance


class DomainPartialSerializer(DomainWriteSerializer):
    allowed_languages = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True, required=False)
    translations = serializers.DictField(child=serializers.DictField(), write_only=True, required=False)
    staff = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        # Si on touche aux translations => règles complètes
        if "translations" in attrs:
            return super().validate(attrs)

        # Si on touche seulement aux allowed_languages (sans translations), on ne force pas translations
        if "allowed_languages" in attrs:
            allowed_langs = attrs.get("allowed_languages")
            if allowed_langs == []:
                raise serializers.ValidationError({"allowed_languages": "Au moins une langue est requise."})
        return attrs


class DomainDetailSerializer(DomainReadSerializer):
    subjects = serializers.SerializerMethodField()

    class Meta:
        model = Domain
        fields = [
            "id",
            "translations",
            "allowed_languages",
            "active",
            "owner",
            "staff",
            "created_at",
            "updated_at",
            "subjects"
        ]
        read_only_fields = fields
        extra_kwargs = {"owner": {"read_only": True}}

    @extend_schema_field(SubjectReadSerializer(many=True))
    def get_subjects(self, obj: Domain) -> list[dict]:
        qs = obj.subjects.filter(active=True).order_by("id")
        return SubjectReadSerializer(qs, many=True, context=self.context).data

    def validate(self, attrs):
        raise serializers.ValidationError("This serializer is read-only.")
