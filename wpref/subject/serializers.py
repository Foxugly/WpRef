from django.conf import settings
from drf_spectacular.utils import extend_schema_field
from domain.models import Domain
from question.models import Question
from rest_framework import serializers
from wpref.serializers import (
    LocalizedNameDescriptionTranslationSerializer,
    LocalizedQuestionTitleTranslationSerializer,
    LocalizedSubjectDetailTranslationSerializer,
    LocalizedSubjectTranslationSerializer,
    LocalizedTranslationsDictField,
    localized_translations_map_schema,
)

from .models import Subject
LANG_CODES = {code for code, _ in settings.LANGUAGES}


class QuestionInSubjectSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
        ]

    @extend_schema_field(
        localized_translations_map_schema(
            LocalizedQuestionTitleTranslationSerializer,
            "LocalizedQuestionTitleTranslations",
        )
    )
    def get_title(self, obj: Question) -> dict:
        data = {}
        for t in obj.translations.all():
            data[t.language_code] = {"title": t.title or "", }
        return data


class SubjectWriteSerializer(serializers.ModelSerializer):
    translations = LocalizedTranslationsDictField(
        value_serializer=LocalizedNameDescriptionTranslationSerializer,
        write_only=True,
        required=True,
        help_text=(
            'Ex: {"fr":{"name":"Math","description":""},'
            '"nl":{"name":"Wiskunde","description":""}}'
        ),
    )

    class Meta:
        model = Subject
        fields = ["translations", "domain", "active"]

    # ---------------------------
    # helpers
    # ---------------------------

    def _apply_translations(self, subject: Subject, translations: dict):
        for lang_code, data in (translations or {}).items():
            subject.set_current_language(lang_code)
            subject.name = data.get("name", "")
            subject.description = data.get("description", "")
            subject.save()

    # ---------------------------
    # CREATE
    # ---------------------------

    def create(self, validated_data):
        translations = validated_data.pop("translations")

        subject = Subject.objects.create(**validated_data)
        self._apply_translations(subject, translations)

        return subject

    # ---------------------------
    # UPDATE
    # ---------------------------

    def update(self, instance, validated_data):
        translations = validated_data.pop("translations", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if translations:
            self._apply_translations(instance, translations)

        return instance

    # ---------------------------
    # VALIDATION
    # ---------------------------

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        domain = attrs.get("domain") or getattr(self.instance, "domain", None)
        if domain is not None and user is not None and not user.can_manage_domain(domain):
            raise serializers.ValidationError({"domain": "Vous ne pouvez pas gerer ce domaine."})

        translations = attrs.get("translations")
        if not translations and self.instance is None:
            raise serializers.ValidationError({"translations": "Au moins une traduction est requise."})

        if translations:
            invalid_codes = sorted(set(translations.keys()) - LANG_CODES)
            if invalid_codes:
                raise serializers.ValidationError({"translations": f"Langues inconnues: {invalid_codes}"})

            if not any((v or {}).get("name") for v in translations.values()):
                raise serializers.ValidationError({"translations": "Au moins un 'name' est requis."})

        return attrs


class SubjectPartialSerializer(SubjectWriteSerializer):
    translations = serializers.DictField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text=SubjectWriteSerializer._declared_fields["translations"].help_text,
    )
    domain = serializers.PrimaryKeyRelatedField(queryset=Domain.objects.all(), required=False)
    active = serializers.BooleanField(required=False)


class SubjectReadSerializer(serializers.ModelSerializer):
    translations = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ["id", "domain", "active", "translations"]
        read_only_fields = fields

    @extend_schema_field(
        localized_translations_map_schema(
            LocalizedSubjectTranslationSerializer,
            "LocalizedSubjectTranslations",
        )
    )
    def get_translations(self, obj: Subject) -> dict:
        data = {}
        for t in obj.translations.all():
            domain_name = obj.domain.safe_translation_getter(
                "name",
                language_code=t.language_code,
                any_language=True,
            )

            data[t.language_code] = {
                "name": t.name or "",
                "description": t.description or "",
                "domain": {"id": obj.domain.id,"name": domain_name or ""},
            }
        return data


class SubjectDetailSerializer(serializers.ModelSerializer):
    translations = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ["id", "active", "domain", "translations", "questions"]

    @extend_schema_field(
        localized_translations_map_schema(
            LocalizedSubjectDetailTranslationSerializer,
            "LocalizedSubjectDetailTranslations",
        )
    )
    def get_translations(self, obj: Subject) -> dict:
        data = {}
        for t in obj.translations.all():
            domain_name = obj.domain.safe_translation_getter(
                "name",
                language_code=t.language_code,
                any_language=True,
            )
            data[t.language_code] = {
                "name": t.name or "",
                "description": t.description or "",
                "domain_name": domain_name or "",
            }
        return data

    @extend_schema_field(QuestionInSubjectSerializer(many=True))
    def get_questions(self, obj: Subject) -> list[dict]:
        qs = obj.questions.filter(active=True).order_by("id")
        return QuestionInSubjectSerializer(qs, many=True, context=self.context).data
