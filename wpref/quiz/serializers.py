import logging

from drf_spectacular.utils import extend_schema_field
from question.models import Question, AnswerOption
from question.serializers import QuestionInQuizQuestionSerializer
from rest_framework import serializers

from .models import QuizTemplate, QuizQuestion, Quiz, QuizQuestionAnswer

logger = logging.getLogger(__name__)


class GenerateFromSubjectsInputSerializer(serializers.Serializer):
    title = serializers.CharField()
    subject_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    max_questions = serializers.IntegerField(required=False, default=10)


class BulkCreateFromTemplateInputSerializer(serializers.Serializer):
    quiz_template_id = serializers.IntegerField()
    user_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class CreateQuizInputSerializer(serializers.Serializer):
    quiz_template_id = serializers.IntegerField()


class QuizQuestionSerializer(serializers.ModelSerializer):
    """
    Représente une question incluse dans un template de quiz.
    On expose quelques infos de la Question en read-only.
    """
    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        source="question",  # remplit le champ modèle "question"
        write_only=True,
    )
    #
    # question_title = serializers.CharField(source="question.title", read_only=True)

    question = QuestionInQuizQuestionSerializer(read_only=True)

    def __init__(self, *args, **kwargs):
        show_correct = kwargs.pop("show_correct", False)
        super().__init__(*args, **kwargs)
        # transmettre le paramètre au serializer imbriqué
        self.fields["question"] = QuestionInQuizQuestionSerializer(
            read_only=True,
            show_correct=show_correct,
        )

    class Meta:
        model = QuizQuestion
        fields = [
            "id",
            "quiz",
            "question",
            "question_id",
            "sort_order",
            "weight",
        ]
        read_only_fields = ["quiz", "question", ]


class QuizTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer principal pour QuizTemplate (usage admin).
    - lecture : inclut les QuizQuestion avec la Question associée
    - écriture : tu peux rester simple et gérer les QuizQuestion via des endpoints dédiés.
    """
    questions_count = serializers.IntegerField(read_only=True)
    can_answer = serializers.BooleanField(read_only=True)

    quiz_questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = QuizTemplate
        fields = [
            "id",
            "domain",
            "title",
            "slug",
            "mode",
            "description",
            "max_questions",
            "permanent",
            "started_at",
            "ended_at",
            "with_duration",
            "duration",
            "active",
            "created_at",
            "questions_count",
            "can_answer",
            # visibilité résultats
            "result_visibility",
            "result_available_at",
            "detail_visibility",
            "detail_available_at",
            # pool de questions (jointure détaillée)
            "quiz_questions",
        ]
        read_only_fields = ["slug", "created_at", "questions_count", "can_answer"]


class QuizQuestionWriteSerializer(serializers.ModelSerializer):
    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        source="question",
        write_only=True,
    )

    class Meta:
        model = QuizQuestion
        fields = ["id", "question_id", "sort_order", "weight"]

    def validate(self, attrs):
        quiz_template = self.context.get("quiz_template")
        if quiz_template is None:
            raise serializers.ValidationError("quiz_template manquant dans le context.")

        question = attrs.get("question")

        if question and not question.active:
            raise serializers.ValidationError({"question_id": "Cette question n'est pas active."})

        if question:
            qs = QuizQuestion.objects.filter(quiz=quiz_template, question=question)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"question_id": "Cette question est déjà dans ce template."})

        return attrs

    def create(self, validated_data):
        logger.info("QuizQuestionWriteSerializer.create")

        quiz_template = self.context["quiz_template"]
        # validated_data contient déjà "question" (grâce à source="question")
        return QuizQuestion.objects.create(quiz=quiz_template, **validated_data)


class QuizQuestionAnswerSerializer(serializers.ModelSerializer):
    """
    Réponse à une question dans un quiz donné.
    On travaille en nested sous /quiz/{quiz_id}/answer/
    """
    question_id = serializers.IntegerField(source="quizquestion.question_id", read_only=True)
    quizquestion_id = serializers.IntegerField(source="quizquestion.id", read_only=True)

    class Meta:
        model = QuizQuestionAnswer
        fields = [
            "id", "quiz", "quizquestion_id", "question_order",
            "question_id", "selected_options", "answered_at",
        ]
        read_only_fields = fields


class QuizQuestionReadSerializer(serializers.ModelSerializer):
    question = QuestionInQuizQuestionSerializer(read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ["id", "question", "sort_order", "weight"]

    def __init__(self, *args, **kwargs):
        show_correct = kwargs.pop("show_correct", False)
        super().__init__(*args, **kwargs)
        # transmettre le paramètre au serializer imbriqué
        self.fields["question"] = QuestionInQuizQuestionSerializer(
            read_only=True,
            show_correct=show_correct,
        )


class QuizSerializer(serializers.ModelSerializer):
    """
    Représente une session de quiz (Quiz).
    """
    quiz_template_title = serializers.CharField(source="quiz_template.title", read_only=True)
    mode = serializers.CharField(source="quiz_template.mode", read_only=True)
    max_questions = serializers.IntegerField(source="quiz_template.max_questions", read_only=True)
    can_answer = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()
    answers = QuizQuestionAnswerSerializer(many=True, read_only=True)

    total_answers = serializers.SerializerMethodField()
    correct_answers = serializers.SerializerMethodField()
    earned_score = serializers.SerializerMethodField()
    max_score = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "domain",
            "quiz_template",
            "quiz_template_title",
            "user",
            "mode",
            "created_at",
            "started_at",
            "ended_at",
            "active",
            "can_answer",
            "max_questions",
            "questions",
            "answers",
            "total_answers",
            "correct_answers",
            "earned_score",
            "max_score"
        ]
        read_only_fields = ["created_at", "user", "can_answer"]

    def _is_admin(self) -> bool:
        req = self.context.get("request")
        if not req or not hasattr(req, "user"):
            return False
        u = req.user
        return bool(u and (u.is_staff or u.is_superuser))

    def _can_show_details(self, quiz) -> bool:
        return self._is_admin() or bool(quiz.quiz_template.can_show_details())

    def _can_show_result(self, quiz) -> bool:
        return self._is_admin() or bool(quiz.quiz_template.can_show_result())

    @extend_schema_field(QuizQuestionReadSerializer(many=True))
    def get_questions(self, obj):
        qt = obj.quiz_template
        show_details = self._can_show_details(obj)
        qs = (
            qt.quiz_questions
            .select_related("question")
            .prefetch_related("question__answer_options")
            .order_by("sort_order")
        )
        return QuizQuestionReadSerializer(qs, many=True, show_correct=show_details).data

    def _answers_qs(self, obj):
        if not hasattr(obj, "_answers_cache"):
            obj._answers_cache = obj.answers.all()
        return obj._answers_cache

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_total_answers(self, obj):
        if not self._can_show_result(obj):
            return None
        return self._answers_qs(obj).count()

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_correct_answers(self, obj):
        if not self._can_show_result(obj):
            return None
        return self._answers_qs(obj).filter(is_correct=True).count()

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_earned_score(self, obj):
        if not self._can_show_result(obj):
            return None
        return sum(a.earned_score for a in self._answers_qs(obj))

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_max_score(self, obj):
        if not self._can_show_result(obj):
            return None
        return sum(a.max_score for a in self._answers_qs(obj))

    def get_can_answer(self, obj) -> bool:
        return obj.can_answer


class QuizQuestionAnswerWriteSerializer(serializers.ModelSerializer):
    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        required=False,
        write_only=True,
        help_text="ID de la Question (optionnel)"
    )

    question_order = serializers.IntegerField(
        required=False,
        help_text="Ordre de la question dans le template (optionnel)"
    )

    class Meta:
        model = QuizQuestionAnswer
        fields = ["question_id", "question_order", "selected_options"]

    def validate(self, attrs):
        quiz = self.context.get("quiz")
        if not quiz:
            raise serializers.ValidationError("Quiz manquant dans le contexte.")

        if not quiz.can_answer:
            raise serializers.ValidationError({"detail": "Ce quiz n'est plus disponible pour répondre."})

        if self.instance:
            # sécurité : réponse doit appartenir au quiz de l'URL
            if self.instance.quiz_id != quiz.id:
                raise serializers.ValidationError("Réponse hors du quiz courant.")
            return attrs

        has_qid = attrs.get("question_id") is not None
        has_order = attrs.get("question_order") is not None

        if not has_qid and not has_order:
            raise serializers.ValidationError(
                "Fournis au moins un des deux champs: 'question_id' et/ou 'question_order'."
            )

        qq_by_id = None
        qq_by_order = None

        # 1) Si question_id fourni, on résout qq
        if has_qid:
            question = attrs["question_id"]
            try:
                qq_by_id = QuizQuestion.objects.get(
                    quiz=quiz.quiz_template,
                    question=question,
                )
            except QuizQuestion.DoesNotExist:
                raise serializers.ValidationError(
                    {"question_id": "Cette question n'appartient pas au template de ce quiz."}
                )

        # 2) Si question_order fourni, on résout qq
        if has_order:
            order = attrs["question_order"]
            if order <= 0:
                raise serializers.ValidationError({"question_order": "Doit être un entier positif."})
            try:
                qq_by_order = QuizQuestion.objects.get(
                    quiz=quiz.quiz_template,
                    sort_order=order,
                )
            except QuizQuestion.DoesNotExist:
                raise serializers.ValidationError(
                    {"question_order": "Aucune question à cet ordre dans le template de ce quiz."}
                )

        # 3) Cohérence si les deux sont présents
        if qq_by_id and qq_by_order and qq_by_id.pk != qq_by_order.pk:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "question_id et question_order ne sont pas cohérents pour ce quiz."
                    ]
                }
            )

        # 4) On choisit la QuizQuestion finale
        qq = qq_by_id or qq_by_order
        attrs["quizquestion"] = qq

        # 5) Normalisation : si l'un manque, on le complète
        # (pratique pour la DB / logs / retours)
        attrs["question_order"] = qq.sort_order

        return attrs

    def create(self, validated_data):
        quiz = self.context["quiz"]

        selected = validated_data.pop("selected_options", [])
        validated_data.pop("question_id", None)  # input-only
        qq = validated_data.pop("quizquestion")  # injecté en validate()

        instance, created = QuizQuestionAnswer.objects.update_or_create(
            quiz=quiz,
            quizquestion=qq,
            defaults={
                "question_order": qq.sort_order,
            }
        )
        instance.selected_options.set(selected)  # ✅ M2M
        return instance

    def update(self, instance, validated_data):
        """
        Gère correctement le M2M selected_options sur PUT/PATCH.
        Et empêche de changer la question d'une réponse existante.
        """
        # 1) récupérer selected_options (M2M)
        selected = validated_data.pop("selected_options", None)

        # 2) Interdire toute tentative de "changer de question"
        # (on accepte éventuellement que le client renvoie ces champs mais on les ignore)
        validated_data.pop("question_id", None)
        validated_data.pop("question_order", None)  # optionnel : si tu veux figer l'ordre aussi
        validated_data.pop("quizquestion", None)  # injecté en validate() éventuellement

        # 3) Mettre à jour les champs simples (ici il n'en reste presque plus)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 4) Appliquer le M2M si présent dans la requête
        if selected is not None:
            instance.selected_options.set(selected)

        return instance
