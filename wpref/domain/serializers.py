from typing import List

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

    def get_translations(self, obj: Domain) -> dict:
        data = {}
        for t in obj.translations.all():
            data[t.language_code] = {"name": t.name or "", "description": t.description or "", }
        return data

    def get_owner(self, obj: Domain) -> dict:
        return {"id": obj.owner_id, "username": obj.owner.username, }

    def get_staff(self, obj: Domain) -> list[dict]:
        return [{"id": u.id, "username": u.username} for u in obj.staff.all()]

    @extend_schema_field(LanguageReadSerializer(many=True))
    def get_allowed_languages(self, obj:Domain) -> List[dict]:
        qs = obj.allowed_languages.all().filter(active=True).order_by("id")
        return LanguageReadSerializer(qs, many=True, context=self.context).data


class DomainWriteSerializer(serializers.ModelSerializer):
    allowed_languages = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True, required=True, )
    translations = serializers.DictField(child=serializers.DictField(), write_only=True, required=True, )
    staff = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=True, )

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
    def validate_allowed_languages(self, value):
        if not value:
            return value

            # déduplication tout en gardant l'ordre
        seen_ids = set()
        unique_languages = []
        for lang in value:
            if lang.pk in seen_ids:
                continue
            seen_ids.add(lang.pk)
            unique_languages.append(lang)

        # validation métier : le code doit exister dans settings.LANGUAGES
        valid_codes = {code for code, _ in settings.LANGUAGES}
        invalid = [lang.code for lang in unique_languages if lang.code not in valid_codes]

        if invalid:
            raise serializers.ValidationError(
                f"Invalid language code(s): {', '.join(sorted(invalid))}"
            )

        return unique_languages

    def validate(self, attrs):
        translations = attrs.get("translations")
        if not translations:
            raise serializers.ValidationError({"translations": "Au moins une traduction est requise."})

        # optionnel : imposer que translations couvre allowed_languages
        allowed = set(attrs.get("allowed_language_codes") or [])
        if allowed:
            provided = set(translations.keys())
            missing = allowed - provided
            if missing:
                raise serializers.ValidationError(
                    {"translations": f"Traductions manquantes pour: {sorted(missing)}"}
                )

        return attrs

    # ---------------------------
    # create / update
    # ---------------------------
    def create(self, validated_data):
        translations = validated_data.pop("translations")
        langs = validated_data.pop("allowed_languages", [])
        staff = validated_data.pop("staff", [])
        with transaction.atomic():
            domain = Domain.objects.create(**validated_data)
            if staff:
                domain.staff.set(staff)
            if len(langs):
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

            if len(langs):
                instance.allowed_languages.set(langs)

        if translations is not None:
            self._apply_translations(instance, translations)

        return instance


class DomainPartialSerializer(DomainWriteSerializer):
    allowed_languages = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True, required=False, )
    translations = serializers.DictField(child=serializers.DictField(), write_only=True, required=False, )
    staff = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False, )
    active = serializers.BooleanField(required=False)


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
            "subjects",
        ]
        read_only_fields = fields
        extra_kwargs = {"owner": {"read_only": True}}

    @extend_schema_field(SubjectReadSerializer(many=True))
    def get_subjects(self, obj: Domain) -> List[dict]:
        qs = obj.subjects.filter(active=True).order_by("id")
        return SubjectReadSerializer(qs, many=True, context=self.context).data
