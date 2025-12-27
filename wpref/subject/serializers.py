from rest_framework import serializers

from .models import Subject


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
        fields = ["id", "translations", "domain"]

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
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ["id", "name", "description", "domain"]

    def get_name(self, obj: Subject) -> str:
        return obj.safe_translation_getter("name", any_language=True) or ""

    def get_description(self, obj: Subject) -> str:
        return obj.safe_translation_getter("description", any_language=True) or ""