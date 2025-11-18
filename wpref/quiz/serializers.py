# quiz/api/serializers.py
from rest_framework import serializers
from .models import QuizSession, QuizAttempt, QuizQuestion


class QuizSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizSession
        fields = [
            "id",
            "quiz",
            "started_at",
            "is_closed",
            "max_duration",
        ]


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = [
            "session",
            "question",
            "question_order",
            "given_answer",
            "is_correct",
            "answered_at",
        ]
        read_only_fields = ["session", "question", "is_correct", "answered_at"]

class QuizQuestionDetailSerializer(serializers.Serializer):
    class Meta:
        model = QuizQuestion
        fields = [
            "quiz_id",
            "quiz_title",
            "question_id",
            "question_order",
            "title",
            "description",
            "options"
        ]

class QuizSummarySerializer(serializers.Serializer):
    class Meta:
        model = QuizSession
        fields = [
            "id",
            "quiz",
            "started_at",
            "is_closed",
            "max_duration",
            "expires_at",
            "total_questions",
            "answered_questions",
            "correct_answers",
        ]