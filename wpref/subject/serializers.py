from typing import List

from drf_spectacular.utils import extend_schema_field
from question.models import Question
from rest_framework import serializers

from .models import Subject


class QuestionInSubjectSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
        ]

    def get_title(self, obj: Question) -> dict:
        data = {}
        for t in obj.domain.translations.all():
            data[t.language_code] = {"title": t.title or "", }
        return data


class SubjectWriteSerializer(serializers.ModelSerializer):
    translations = serializers.DictField(
        child=serializers.DictField(),
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
        for lang_code, data in translations.items():
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
        translations = attrs.get("translations")

        if not translations:
            raise serializers.ValidationError(
                {"translations": "Au moins une traduction est requise."}
            )

        # optionnel : imposer certaines langues
        # allowed = {"fr", "nl"}
        # if allowed - set(translations.keys()):
        #     raise serializers.ValidationError("Langues manquantes")

        return attrs


class SubjectReadSerializer(serializers.ModelSerializer):
    translations = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ["id", "domain", "translations"]
        read_only_fields = fields

    def get_translations(self, obj: Subject) -> dict:
        data = {}
        # Parler: obj.translations est le related manager vers SubjectTranslation
        for t in obj.translations.all():
            data[t.language_code] = {
                "name": t.name or "",
                "description": t.description or "",
            }
        return data


class SubjectDetailSerializer(serializers.ModelSerializer):
    translations = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ["id", "active", "domain", "translations", "questions"]

    def get_translations(self, obj: Subject) -> dict:
        data = {}
        # Parler: obj.translations est le related manager vers SubjectTranslation
        for t in obj.translations.all():
            data[t.language_code] = {
                "name": t.name or "",
                "description": t.description or "",
            }
        return data

    @extend_schema_field(QuestionInSubjectSerializer(many=True))
    def get_questions(self, obj: Subject) -> List[dict]:
        qs = obj.questions.all().filter(active=True).order_by("id")
        return QuestionInSubjectSerializer(qs, many=True, context=self.context).data
