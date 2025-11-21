# question/serializers.py
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Question, QuestionMedia, AnswerOption, QuestionSubject
from subject.models import Subject
from subject.serializers import SubjectSerializer


class QuestionMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionMedia
        fields = ["id", "kind", "file", "external_url", "caption", "sort_order"]


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ["id", "content", "is_correct", "sort_order"]


class QuestionSerializer(serializers.ModelSerializer):
    media = QuestionMediaSerializer(many=True, required=False)
    answer_options = AnswerOptionSerializer(many=True)
    subjects = SubjectSerializer(many=True, read_only=True)
    subject_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    subject_slugs = serializers.ListField(
        child=serializers.SlugField(), write_only=True, required=False
    )

    class Meta:
        model = Question
        fields = [
            "id", "title", "description", "explanation",
            "allow_multiple_correct",
            "subjects", "subject_ids", "subject_slugs",
            "media", "answer_options",
            "created_at",
        ]

    @staticmethod
    def _assign_subjects(question, subject_ids=None, subject_slugs=None):
        if subject_ids is None and subject_slugs is None:
            return
        qs = Subject.objects.none()
        if subject_ids:
            qs = qs.union(Subject.objects.filter(id__in=subject_ids))
        if subject_slugs:
            qs = qs.union(Subject.objects.filter(slug__in=subject_slugs))
        QuestionSubject.objects.filter(question=question).delete()
        for i, s in enumerate(qs.distinct()):
            QuestionSubject.objects.create(question=question, subject=s, sort_order=i)

    def create(self, validated_data):
        media_data = validated_data.pop("media", [])
        options_data = validated_data.pop("answer_options", [])
        subject_ids = validated_data.pop("subject_ids", None)
        subject_slugs = validated_data.pop("subject_slugs", None)

        q = Question.objects.create(**validated_data)
        for opt in options_data:
            AnswerOption.objects.create(question=q, **opt)
        for m in media_data:
            QuestionMedia.objects.create(question=q, **m)

        self._assign_subjects(q, subject_ids, subject_slugs)

        # 🔴 ICI : on convertit la ValidationError Django en ValidationError DRF
        try:
            q.full_clean()
        except DjangoValidationError as e:
            # e.message_dict si tu veux un dict de champs, e.messages pour une liste
            raise serializers.ValidationError(e.message_dict or e.messages)

        return q

    def update(self, instance, validated_data):
        media_data = validated_data.pop("media", None)
        options_data = validated_data.pop("answer_options", None)
        subject_ids = validated_data.pop("subject_ids", None)
        subject_slugs = validated_data.pop("subject_slugs", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        if options_data is not None:
            instance.answer_options.all().delete()
            for opt in options_data:
                AnswerOption.objects.create(question=instance, **opt)

        if media_data is not None:
            instance.media.all().delete()
            for m in media_data:
                QuestionMedia.objects.create(question=instance, **m)

        if subject_ids is not None or subject_slugs is not None:
            self._assign_subjects(instance, subject_ids, subject_slugs)

        # 🔴 Même correction en update
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict or e.messages)

        return instance
