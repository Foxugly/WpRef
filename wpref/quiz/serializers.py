# quiz/api/serializers.py
from rest_framework import serializers

from .models import Quiz, QuizSession, QuizAttempt, QuizQuestion


class QuizSessionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="quiz.title", read_only=True)
    with_duration = serializers.BooleanField(source="quiz.with_duration", read_only=True)
    duration = serializers.IntegerField(source="quiz.duration", read_only=True)
    max_questions = serializers.IntegerField(source="quiz.max_questions", read_only=True )
    user = serializers.CharField(source="user.get_full_name", read_only=True)
    mode = serializers.CharField(source="quiz.mode", read_only=True)

    class Meta:
        model = QuizSession
        fields = [
            "id",
            "title", # quiz
            "user",
            "mode",
            "created_at",
            "started_at",
            "expired_at",
            "is_closed",
            "with_duration", # quiz
            "duration", # quiz
            "max_questions", #quiz
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

class QuizAttemptInputSerializer(serializers.Serializer):
    """
    Entrée pour POST /api/quiz/<quiz_id>/attempt/<question_order>/.

    - given_answer : pour les questions "texte libre" (comme dans les tests actuels)
    - selected_option_ids : pour les QCM basées sur AnswerOption
    """
    given_answer = serializers.CharField(
        allow_blank=True,
        required=False,
    )
    selected_option_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        required=False,
    )

    def validate(self, attrs):
        """
        On impose qu'au moins une des deux infos soit présente.
        """
        if not attrs.get("given_answer") and not attrs.get("selected_option_ids"):
            raise serializers.ValidationError(
                "Vous devez fournir soit 'given_answer', soit 'selected_option_ids'."
            )
        return attrs

class QuizOptionStateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    content = serializers.CharField()
    is_selected = serializers.BooleanField()
    is_correct = serializers.BooleanField(required=False)


class QuizAttemptDetailSerializer(serializers.Serializer):
    quiz_id = serializers.UUIDField()
    quiz_title = serializers.CharField()
    question_id = serializers.IntegerField()
    question_order = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    options = QuizOptionStateSerializer(many=True)


class QuizSummarySerializer(serializers.Serializer):
    title = serializers.CharField(source="quiz.title", read_only=True)
    with_duration = serializers.BooleanField(source="quiz.with_duration", read_only=True)
    duration = serializers.IntegerField(source="quiz.duration", read_only=True)
    max_questions = serializers.IntegerField(source="quiz.max_questions", read_only=True)
    user = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = QuizSession
        fields = [
            "id",
            "title",
            "quiz",
            "created_at",
            "started_at",
            "expired_at",
            "is_closed",
            "with_duration",
            "duration",
            "max_questions",
            "answered_questions",
            "correct_answers",
        ]


class QuizSerializer(serializers.ModelSerializer):
    """
    CRUD quiz par les admins, lookup par slug.
    """
    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "with_duration",
            "duration",
            "max_questions",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]


class QuizQuestionInlineSerializer(serializers.ModelSerializer):
    """
    Pour lister les questions d'un quiz (via QuizQuestion).
    """
    question_title = serializers.CharField(source="question.title", read_only=True)

    class Meta:
        model = QuizQuestion
        fields = [
            "id",
            "question",        # id de la question
            "question_title",
            "sort_order",
            "weight",
        ]


class QuizQuestionUpdateSerializer(serializers.Serializer):
    """
    Pour ajouter / modifier une question dans le quiz.
    """
    question_id = serializers.IntegerField()
    sort_order = serializers.IntegerField(required=False, default=0)
    weight = serializers.IntegerField(required=False, default=1)

class QuizGenerateInputSerializer(serializers.Serializer):
    subject_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text="Liste d'IDs de sujets"
    )
    max_questions = serializers.IntegerField(min_value=1, default=10)
    with_duration = serializers.BooleanField(default=False)
    duration = serializers.IntegerField(min_value=1, default=10)

    title = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)