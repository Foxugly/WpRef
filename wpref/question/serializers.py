# question/serializers.py
from rest_framework import serializers
from subject.models import Subject

from .models import Question, QuestionMedia, AnswerOption


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "slug", "description"]


class QuestionLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "title"]  # tu peux ajouter d'autres champs si tu veux


class QuestionMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionMedia
        fields = ["id", "kind", "file", "external_url", "sort_order"]
        read_only_fields = ["id", "file", "external_url", "sort_order", "kind"]


class QuestionAnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption  # adapte si ton modèle s'appelle autrement
        fields = ["id", "content", "is_correct", "sort_order"]
        read_only_fields = ["id"]


class QuestionSerializer(serializers.ModelSerializer):
    # sujets en lecture
    subjects = SubjectSerializer(many=True, read_only=True)

    # réponses
    answer_options = QuestionAnswerOptionSerializer(many=True, required=False)

    # médias : read_only, gérés par la vue
    media = QuestionMediaSerializer(many=True, read_only=True)

    subject_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "description",
            "explanation",
            "allow_multiple_correct",
            "is_mode_practice",
            "is_mode_exam",
            "subjects",
            "subject_ids",
            "answer_options",
            "media",
            "created_at",
        ]
        read_only_fields = ["id", "subjects", "media", "created_at"]

    # ---------------------------
    # CREATE
    # ---------------------------
    def create(self, validated_data):
        subject_ids = validated_data.pop("subject_ids", [])
        answer_options_data = validated_data.pop("answer_options", [])
        # 1) Question
        question = Question.objects.create(**validated_data)
        # 2) sujets (M2M)
        if subject_ids:
            subjects_qs = Subject.objects.filter(id__in=subject_ids)
            question.subjects.set(subjects_qs)
        # 3) réponses
        for opt in answer_options_data:
            AnswerOption.objects.create(question=question, **opt)
        return question

    # ---------------------------
    # UPDATE
    # ---------------------------
    def update(self, instance, validated_data):
        subject_ids = validated_data.pop("subject_ids", None)
        answer_options_data = validated_data.pop("answer_options", None)
        # 1) champs simples
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # 2) sujets (M2M)
        if subject_ids is not None:
            subjects_qs = Subject.objects.filter(id__in=subject_ids)
            instance.subjects.set(subjects_qs)
        # 3) réponses : stratégie simple = wipe + recreate
        if answer_options_data is not None:
            instance.answer_options.all().delete()
            for opt in answer_options_data:
                AnswerOption.objects.create(question=instance, **opt)
        # les médias sont gérés dans le ViewSet via _handle_media_upload()
        return instance
