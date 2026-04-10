import logging

from drf_spectacular.utils import extend_schema_field
from django.db import IntegrityError, transaction
from question.models import Question, AnswerOption
from question.serializers import QuestionInQuizQuestionSerializer, QuestionReadSerializer
from rest_framework import serializers
from config.serializers import UserSummarySerializer
from config.serializers import (
    LocalizedQuizTemplateTranslationSerializer,
    LocalizedTranslationsDictField,
    localized_translations_map_schema,
)

from .models import (
    QuizTemplate,
    QuizQuestion,
    Quiz,
    QuizQuestionAnswer,
    QuizAlertThread,
    QuizAlertMessage,
)
from .alerting import (
    alert_last_message_preview,
    append_alert_message,
    can_manage_alert,
    can_reply_to_alert,
    create_alert_thread,
    is_alert_unread,
    message_is_mine,
    message_is_unread_for_user,
    unread_count_for_alert,
)
from .policies import (
    ANSWER_CORRECTNESS_FULL,
    ANSWER_CORRECTNESS_HIDDEN,
    ANSWER_CORRECTNESS_UNKNOWN,
    answer_correctness_state,
    can_show_quiz_result,
    is_quiz_admin,
)

logger = logging.getLogger(__name__)


class RequestUserMixin:
    def request_user(self):
        return getattr(self.context.get("request"), "user", None)

    def preferred_language(self) -> str:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return (
            getattr(user, "language", None)
            or getattr(request, "LANGUAGE_CODE", None)
            or "fr"
        )


class ShowCorrectContextMixin:
    def __init__(self, *args, **kwargs):
        show_correct = kwargs.pop("show_correct", None)
        context = kwargs.get("context")
        if show_correct is not None:
            kwargs["context"] = {
                **(context or {}),
                "show_correct": show_correct,
            }
        super().__init__(*args, **kwargs)


class GenerateFromSubjectsInputSerializer(serializers.Serializer):
    title = serializers.CharField()
    subject_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    max_questions = serializers.IntegerField(required=False, default=10)
    with_duration = serializers.BooleanField(required=False, default=True)
    duration = serializers.IntegerField(required=False, allow_null=True, min_value=1, default=10)

    def validate(self, attrs):
        if not attrs.get("with_duration", True):
            attrs["duration"] = None
            return attrs

        if attrs.get("duration") is None:
            attrs["duration"] = 10
        return attrs


class BulkCreateFromTemplateInputSerializer(serializers.Serializer):
    quiz_template_id = serializers.IntegerField()
    user_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class CreateQuizInputSerializer(serializers.Serializer):
    quiz_template_id = serializers.IntegerField()


class QuizQuestionSerializer(ShowCorrectContextMixin, serializers.ModelSerializer):
    """
    ReprÃ©sente une question incluse dans un template de quiz.
    On expose quelques infos de la Question en read-only.
    """

    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        source="question",
        write_only=True,
    )

    question = QuestionInQuizQuestionSerializer(read_only=True)

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
        read_only_fields = ["quiz", "question"]


class QuizTemplateSerializer(RequestUserMixin, serializers.ModelSerializer):
    """
    Serializer principal pour QuizTemplate (usage admin).
    - lecture : inclut les QuizQuestion avec la Question associÃ©e
    - Ã©criture : tu peux rester simple et gÃ©rer les QuizQuestion via des endpoints dÃ©diÃ©s.
    """

    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()
    questions_count = serializers.IntegerField(read_only=True)
    can_answer = serializers.BooleanField(read_only=True)
    quiz_questions = QuizQuestionSerializer(many=True, read_only=True)
    created_by = serializers.IntegerField(source="created_by_id", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, default="")

    class Meta:
        model = QuizTemplate
        fields = [
            "id",
            "domain",
            "title",
            "slug",
            "mode",
            "description",
            "translations",
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
            "result_visibility",
            "result_available_at",
            "detail_visibility",
            "detail_available_at",
            "is_public",
            "created_by",
            "created_by_username",
            "quiz_questions",
        ]
        read_only_fields = ["slug", "created_at", "questions_count", "can_answer"]

    def get_title(self, obj: QuizTemplate) -> str:
        return obj.get_localized_content(self.preferred_language()).get("title", "")

    def get_description(self, obj: QuizTemplate) -> str:
        return obj.get_localized_content(self.preferred_language()).get("description", "")

    @extend_schema_field(
        localized_translations_map_schema(
            LocalizedQuizTemplateTranslationSerializer,
            "LocalizedQuizTemplateTranslations",
        )
    )
    def get_translations(self, obj: QuizTemplate) -> dict[str, dict[str, str]]:
        translations = obj.normalized_translations()
        if translations:
            return translations
        preferred_language = self.preferred_language()
        return {
            preferred_language: {
                "title": obj.title or "",
                "description": obj.description or "",
            }
        }


class QuizTemplateWriteSerializer(RequestUserMixin, serializers.ModelSerializer):
    translations = LocalizedTranslationsDictField(
        value_serializer=LocalizedQuizTemplateTranslationSerializer,
        write_only=True,
        required=False,
        help_text='Ex: {"fr":{"title":"Quiz FR","description":"Consignes FR"},"en":{"title":"Quiz EN","description":"Instructions EN"}}',
    )

    def _normalize_translations(self, translations: dict | None, fallback_title: str, fallback_description: str) -> dict:
        preferred_language = self.preferred_language()
        normalized: dict[str, dict[str, str]] = {}
        for lang_code, payload in (translations or {}).items():
            if not isinstance(lang_code, str) or not isinstance(payload, dict):
                continue
            normalized[lang_code] = {
                "title": str(payload.get("title", "") or ""),
                "description": str(payload.get("description", "") or ""),
            }
        if not normalized:
            normalized[preferred_language] = {
                "title": fallback_title,
                "description": fallback_description,
            }
        return normalized

    def _payload_language(self, translations: dict, fallback_title: str) -> str:
        title = (fallback_title or "").strip()
        if title:
            for lang_code, payload in translations.items():
                if str((payload or {}).get("title", "")).strip() == title:
                    return lang_code
        return self.preferred_language()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            raise serializers.ValidationError("Authentication required.")

        translations = attrs.get("translations")
        fallback_title = str(attrs.get("title") or getattr(self.instance, "title", "") or "").strip()
        fallback_description = str(
            attrs.get("description") or getattr(self.instance, "description", "") or ""
        ).strip()
        attrs["translations"] = self._normalize_translations(
            translations,
            fallback_title,
            fallback_description,
        )

        if not any((value or {}).get("title") for value in attrs["translations"].values()):
            raise serializers.ValidationError({"translations": "At least one translated title is required."})

        domain = attrs.get("domain") or getattr(self.instance, "domain", None)
        mode = attrs.get("mode") or getattr(self.instance, "mode", QuizTemplate.MODE_PRACTICE)

        if domain is None:
            raise serializers.ValidationError({"domain": "Domain is required."})

        if getattr(user, "is_superuser", False):
            return attrs

        if mode == QuizTemplate.MODE_EXAM:
            if not user.can_manage_domain(domain):
                raise serializers.ValidationError(
                    {"mode": "Only a domain owner or domain staff can create or edit exam templates."}
                )
            return attrs

        if not user.get_visible_domains(active_only=False).filter(id=domain.id).exists():
            raise serializers.ValidationError(
                {"domain": "You are not linked to this domain."}
            )
        return attrs

    def create(self, validated_data):
        translations = validated_data.pop("translations", {})
        payload_language = self._payload_language(translations, validated_data.get("title", ""))
        instance = QuizTemplate(**validated_data)
        instance.translations = translations
        try:
            instance.sync_fields_from_translations(payload_language)
            instance.save(preferred_language=payload_language)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"title": "A quiz template with this title already exists."}
            ) from exc
        return instance

    def update(self, instance, validated_data):
        translations = validated_data.pop("translations", None)
        next_title = validated_data.get("title", instance.title)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if translations is not None:
            instance.translations = translations
        payload_language = self._payload_language(instance.normalized_translations(), next_title)
        try:
            instance.sync_fields_from_translations(payload_language)
            instance.save(preferred_language=payload_language)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"title": "A quiz template with this title already exists."}
            ) from exc
        return instance

    class Meta:
        model = QuizTemplate
        fields = [
            "domain",
            "title",
            "mode",
            "description",
            "translations",
            "max_questions",
            "permanent",
            "started_at",
            "ended_at",
            "with_duration",
            "duration",
            "is_public",
            "active",
            "result_visibility",
            "result_available_at",
            "detail_visibility",
            "detail_available_at",
        ]


class QuizTemplatePartialSerializer(QuizTemplateWriteSerializer):
    domain = serializers.PrimaryKeyRelatedField(queryset=QuizTemplate._meta.get_field("domain").remote_field.model.objects.all(), required=False, allow_null=True)
    title = serializers.CharField(required=False)
    mode = serializers.ChoiceField(choices=QuizTemplate.MODE_CHOICES, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    translations = LocalizedTranslationsDictField(
        value_serializer=LocalizedQuizTemplateTranslationSerializer,
        write_only=True,
        required=False,
    )
    max_questions = serializers.IntegerField(required=False, min_value=1)
    permanent = serializers.BooleanField(required=False)
    started_at = serializers.DateTimeField(required=False, allow_null=True)
    ended_at = serializers.DateTimeField(required=False, allow_null=True)
    with_duration = serializers.BooleanField(required=False)
    duration = serializers.IntegerField(required=False, min_value=1)
    is_public = serializers.BooleanField(required=False)
    active = serializers.BooleanField(required=False)
    result_visibility = serializers.ChoiceField(choices=QuizTemplate._meta.get_field("result_visibility").choices, required=False)
    result_available_at = serializers.DateTimeField(required=False, allow_null=True)
    detail_visibility = serializers.ChoiceField(choices=QuizTemplate._meta.get_field("detail_visibility").choices, required=False)
    detail_available_at = serializers.DateTimeField(required=False, allow_null=True)


class QuizQuestionWriteSerializer(serializers.ModelSerializer):
    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        source="question",
        write_only=True,
    )

    class Meta:
        model = QuizQuestion
        fields = ["question_id", "sort_order", "weight"]

    def validate(self, attrs):
        quiz_template = self.context.get("quiz_template")
        if quiz_template is None:
            raise serializers.ValidationError("quiz_template manquant dans le context.")

        question = attrs.get("question")
        if question is None and self.instance is not None:
            question = self.instance.question

        if question and not question.active:
            raise serializers.ValidationError({"question_id": "Cette question n'est pas active."})

        if question and quiz_template.domain_id and question.domain_id != quiz_template.domain_id:
            raise serializers.ValidationError(
                {"question_id": "Cette question n'appartient pas au domaine de ce quiz."}
            )

        if question and quiz_template.mode == QuizTemplate.MODE_EXAM and not question.is_mode_exam:
            raise serializers.ValidationError(
                {"question_id": "Cette question n'est pas disponible pour le mode examen."}
            )

        if question:
            qs = QuizQuestion.objects.filter(quiz=quiz_template, question=question)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"question_id": "Cette question est dÃ©jÃ  dans ce template."})

        return attrs

    def create(self, validated_data):
        logger.debug("QuizQuestionWriteSerializer.create")
        quiz_template = self.context["quiz_template"]
        return QuizQuestion.objects.create(quiz=quiz_template, **validated_data)


class QuizQuestionPartialSerializer(QuizQuestionWriteSerializer):
    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        source="question",
        write_only=True,
        required=False,
    )
    sort_order = serializers.IntegerField(required=False, min_value=1)
    weight = serializers.IntegerField(required=False, min_value=1)


class QuizQuestionAnswerSerializer(serializers.ModelSerializer):
    """
    RÃ©ponse Ã  une question dans un quiz donnÃ©.
    On travaille en nested sous /quiz/{quiz_id}/answer/
    """

    question_id = serializers.IntegerField(source="quizquestion.question_id", read_only=True)
    quizquestion_id = serializers.IntegerField(source="quizquestion.id", read_only=True)

    class Meta:
        model = QuizQuestionAnswer
        fields = [
            "id",
            "quiz",
            "quizquestion_id",
            "question_order",
            "question_id",
            "selected_options",
            "answered_at",
        ]
        read_only_fields = fields


class QuizQuestionReadSerializer(ShowCorrectContextMixin, serializers.ModelSerializer):
    question = serializers.SerializerMethodField()

    class Meta:
        model = QuizQuestion
        fields = ["id", "question", "sort_order", "weight"]

    @extend_schema_field(QuestionReadSerializer)
    def get_question(self, obj) -> dict:
        context = {
            **self.context,
            "show_correct": bool(self.context.get("show_correct", False)),
        }
        return QuestionReadSerializer(
            obj.question,
            context=context,
        ).data


class QuizListSerializer(RequestUserMixin, serializers.ModelSerializer):
    """RÃ©sumÃ© lÃ©ger d'une session de quiz pour la liste."""

    quiz_template_title = serializers.SerializerMethodField()
    quiz_template_description = serializers.SerializerMethodField()
    mode = serializers.CharField(source="quiz_template.mode", read_only=True)
    max_questions = serializers.IntegerField(source="quiz_template.max_questions", read_only=True)
    can_answer = serializers.SerializerMethodField()
    user_summary = serializers.SerializerMethodField()
    with_duration = serializers.BooleanField(source="quiz_template.with_duration", read_only=True)
    duration = serializers.IntegerField(source="quiz_template.duration", read_only=True)
    earned_score = serializers.FloatField(source="_earned_score", read_only=True)
    max_score = serializers.FloatField(source="_max_score", read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "domain",
            "quiz_template",
            "quiz_template_title",
            "quiz_template_description",
            "user",
            "user_summary",
            "mode",
            "created_at",
            "started_at",
            "ended_at",
            "active",
            "can_answer",
            "max_questions",
            "with_duration",
            "duration",
            "earned_score",
            "max_score",
        ]
        read_only_fields = [
            "created_at",
            "user",
            "user_summary",
            "can_answer",
            "quiz_template_title",
            "quiz_template_description",
            "mode",
            "max_questions",
            "with_duration",
            "duration",
            "earned_score",
            "max_score",
        ]

    @extend_schema_field(UserSummarySerializer(allow_null=True))
    def get_user_summary(self, obj) -> dict | None:
        if obj.user_id is None:
            return None
        return {
            "id": obj.user_id,
            "username": obj.user.username,
        }

    def get_can_answer(self, obj) -> bool:
        return obj.can_answer

    def get_quiz_template_title(self, obj) -> str:
        return obj.quiz_template.get_localized_content(self.preferred_language()).get("title", "")

    def get_quiz_template_description(self, obj) -> str:
        return obj.quiz_template.get_localized_content(self.preferred_language()).get("description", "")


class QuizSerializer(QuizListSerializer):
    """
    ReprÃ©sente une session de quiz (Quiz).
    """

    questions = serializers.SerializerMethodField()
    answers = QuizQuestionAnswerSerializer(many=True, read_only=True)
    total_answers = serializers.SerializerMethodField()
    correct_answers = serializers.SerializerMethodField()
    earned_score = serializers.SerializerMethodField()
    max_score = serializers.SerializerMethodField()
    answer_correctness_state = serializers.SerializerMethodField()

    class Meta(QuizListSerializer.Meta):
        fields = QuizListSerializer.Meta.fields + [
            "questions",
            "answers",
            "total_answers",
            "correct_answers",
            "earned_score",
            "max_score",
            "answer_correctness_state",
        ]
        read_only_fields = QuizListSerializer.Meta.read_only_fields

    def _is_admin(self) -> bool:
        req = self.context.get("request")
        return is_quiz_admin(getattr(req, "user", None))

    def _answer_correctness_state(self, quiz) -> str:
        req = self.context.get("request")
        return answer_correctness_state(quiz=quiz, user=getattr(req, "user", None))

    def _can_show_result(self, quiz) -> bool:
        req = self.context.get("request")
        return can_show_quiz_result(quiz=quiz, user=getattr(req, "user", None))

    @extend_schema_field(
        serializers.ChoiceField(
            choices=[ANSWER_CORRECTNESS_FULL, ANSWER_CORRECTNESS_UNKNOWN, ANSWER_CORRECTNESS_HIDDEN]
        )
    )
    def get_answer_correctness_state(self, obj) -> str:
        return self._answer_correctness_state(obj)

    @extend_schema_field(QuizQuestionReadSerializer(many=True))
    def get_questions(self, obj) -> serializers.ModelSerializer:
        qt = obj.quiz_template
        correctness_state = self._answer_correctness_state(obj)
        return QuizQuestionReadSerializer(
            qt.quiz_questions.all(),
            many=True,
            context={
                **self.context,
                "show_correct_state": correctness_state,
            },
        ).data

    def _answers_list(self, obj):
        if not hasattr(obj, "_answers_cache"):
            obj._answers_cache = list(obj.answers.all())
        return obj._answers_cache

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_total_answers(self, obj) -> int:
        if not self._can_show_result(obj):
            return None
        return len(self._answers_list(obj))

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_correct_answers(self, obj) -> int:
        if not self._can_show_result(obj):
            return None
        return sum(1 for a in self._answers_list(obj) if a.is_correct)

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_earned_score(self, obj) -> float:
        if not self._can_show_result(obj):
            return None
        return sum(a.earned_score for a in self._answers_list(obj))

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_max_score(self, obj) -> float:
        if not self._can_show_result(obj):
            return None
        return sum(a.max_score for a in self._answers_list(obj))


class QuizAssignmentListSerializer(QuizListSerializer):
    earned_score = serializers.SerializerMethodField()
    max_score = serializers.SerializerMethodField()
    total_answers = serializers.SerializerMethodField()
    correct_answers = serializers.SerializerMethodField()

    class Meta(QuizListSerializer.Meta):
        fields = QuizListSerializer.Meta.fields + [
            "earned_score",
            "max_score",
            "total_answers",
            "correct_answers",
        ]

    def _answers_list(self, obj):
        if not hasattr(obj, "_answers_cache"):
            obj._answers_cache = list(obj.answers.all())
        return obj._answers_cache

    def get_total_answers(self, obj) -> int:
        return len(self._answers_list(obj))

    def get_correct_answers(self, obj) -> int:
        return sum(1 for a in self._answers_list(obj) if a.is_correct)

    def get_earned_score(self, obj) -> float:
        return sum(a.earned_score for a in self._answers_list(obj))

    def get_max_score(self, obj) -> float:
        return sum(a.max_score for a in self._answers_list(obj))


class QuizUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = [
            "domain",
            "quiz_template",
            "user",
            "started_at",
            "ended_at",
            "active",
        ]


class QuizPartialUpdateSerializer(QuizUpdateSerializer):
    domain = serializers.PrimaryKeyRelatedField(queryset=Quiz._meta.get_field("domain").remote_field.model.objects.all(), required=False, allow_null=True)
    quiz_template = serializers.PrimaryKeyRelatedField(queryset=QuizTemplate.objects.all(), required=False)
    user = serializers.PrimaryKeyRelatedField(queryset=Quiz._meta.get_field("user").remote_field.model.objects.all(), required=False, allow_null=True)
    started_at = serializers.DateTimeField(required=False, allow_null=True)
    ended_at = serializers.DateTimeField(required=False, allow_null=True)
    active = serializers.BooleanField(required=False)


class QuizQuestionAnswerWriteSerializer(serializers.ModelSerializer):
    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        required=False,
        write_only=True,
        help_text="ID de la Question (optionnel)",
    )

    question_order = serializers.IntegerField(
        required=False,
        help_text="Ordre de la question dans le template (optionnel)",
    )
    selected_options = serializers.PrimaryKeyRelatedField(
        queryset=AnswerOption.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = QuizQuestionAnswer
        fields = ["question_id", "question_order", "selected_options"]

    def _validate_selected_options_for_quizquestion(self, selected_options, quizquestion):
        if selected_options is None:
            return
        allowed_option_ids = set(
            quizquestion.question.answer_options.values_list("id", flat=True)
        )
        selected_option_ids = {option.id for option in selected_options}
        if not selected_option_ids.issubset(allowed_option_ids):
            raise serializers.ValidationError(
                {
                    "selected_options": (
                        "Toutes les options sélectionnées doivent appartenir à la question répondue."
                    )
                }
            )

    def validate(self, attrs):
        quiz = self.context.get("quiz")
        if not quiz:
            raise serializers.ValidationError("Quiz manquant dans le contexte.")

        if not quiz.can_answer:
            raise serializers.ValidationError({"detail": "Ce quiz n'est plus disponible pour rÃ©pondre."})

        if self.instance:
            if self.instance.quiz_id != quiz.id:
                raise serializers.ValidationError("RÃ©ponse hors du quiz courant.")
            if "selected_options" in attrs:
                self._validate_selected_options_for_quizquestion(
                    attrs.get("selected_options"),
                    self.instance.quizquestion,
                )
            return attrs

        has_qid = attrs.get("question_id") is not None
        has_order = attrs.get("question_order") is not None

        if not has_qid and not has_order:
            raise serializers.ValidationError(
                "Fournis au moins un des deux champs: 'question_id' et/ou 'question_order'."
            )

        qq_by_id = None
        qq_by_order = None

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

        if has_order:
            order = attrs["question_order"]
            if order <= 0:
                raise serializers.ValidationError({"question_order": "Doit Ãªtre un entier positif."})
            try:
                qq_by_order = QuizQuestion.objects.get(
                    quiz=quiz.quiz_template,
                    sort_order=order,
                )
            except QuizQuestion.DoesNotExist:
                raise serializers.ValidationError(
                    {"question_order": "Aucune question Ã  cet ordre dans le template de ce quiz."}
                )

        if qq_by_id and qq_by_order and qq_by_id.pk != qq_by_order.pk:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "question_id et question_order ne sont pas cohÃ©rents pour ce quiz."
                    ]
                }
            )

        qq = qq_by_id or qq_by_order
        self._validate_selected_options_for_quizquestion(
            attrs.get("selected_options", []),
            qq,
        )
        attrs["quizquestion"] = qq
        attrs["question_order"] = qq.sort_order
        return attrs

    def create(self, validated_data):
        quiz = self.context["quiz"]

        selected = validated_data.pop("selected_options", [])
        validated_data.pop("question_id", None)
        qq = validated_data.pop("quizquestion")

        with transaction.atomic():
            type(quiz).objects.select_for_update().filter(pk=quiz.pk).exists()
            try:
                instance = (
                    QuizQuestionAnswer.objects.select_for_update()
                    .get(quiz=quiz, quizquestion=qq)
                )
                if instance.question_order != qq.sort_order:
                    instance.question_order = qq.sort_order
                    instance.save(update_fields=["question_order"])
            except QuizQuestionAnswer.DoesNotExist:
                try:
                    instance = QuizQuestionAnswer.objects.create(
                        quiz=quiz,
                        quizquestion=qq,
                        question_order=qq.sort_order,
                    )
                except IntegrityError:
                    instance = (
                        QuizQuestionAnswer.objects.select_for_update()
                        .get(quiz=quiz, quizquestion=qq)
                    )
            instance.selected_options.set(selected)
        return instance

    def update(self, instance, validated_data):
        selected = validated_data.pop("selected_options", None)
        validated_data.pop("question_id", None)
        validated_data.pop("question_order", None)
        validated_data.pop("quizquestion", None)

        with transaction.atomic():
            locked_instance = QuizQuestionAnswer.objects.select_for_update().get(pk=instance.pk)

            if validated_data:
                for attr, value in validated_data.items():
                    setattr(locked_instance, attr, value)
                locked_instance.save(update_fields=list(validated_data.keys()))

            if selected is not None:
                locked_instance.selected_options.set(selected)

        return locked_instance


class QuizQuestionAnswerPartialSerializer(QuizQuestionAnswerWriteSerializer):
    pass


class QuizAlertMessageSerializer(RequestUserMixin, serializers.ModelSerializer):
    author_summary = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    is_unread = serializers.SerializerMethodField()

    class Meta:
        model = QuizAlertMessage
        fields = [
            "id",
            "author",
            "author_summary",
            "body",
            "created_at",
            "is_mine",
            "is_unread",
        ]
        read_only_fields = fields

    @extend_schema_field(UserSummarySerializer(allow_null=True))
    def get_author_summary(self, obj) -> dict | None:
        if obj.author_id is None:
            return None
        return {
            "id": obj.author_id,
            "username": obj.author.username,
        }

    def get_is_mine(self, obj) -> bool:
        return message_is_mine(obj, self.request_user())

    def get_is_unread(self, obj) -> bool:
        return message_is_unread_for_user(obj, self.request_user())


class QuizAlertThreadListSerializer(RequestUserMixin, serializers.ModelSerializer):
    kind = serializers.CharField(read_only=True)
    unread = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message_preview = serializers.SerializerMethodField()
    counterpart_username = serializers.SerializerMethodField()
    question_id = serializers.IntegerField(read_only=True, allow_null=True)
    question_order = serializers.IntegerField(read_only=True, allow_null=True)
    question_title = serializers.CharField(read_only=True, allow_blank=True)
    quiz_template_title = serializers.SerializerMethodField()

    class Meta:
        model = QuizAlertThread
        fields = [
            "id",
            "quiz",
            "kind",
            "question_id",
            "question_order",
            "question_title",
            "quiz_template_title",
            "reported_language",
            "status",
            "reporter_reply_allowed",
            "last_message_at",
            "created_at",
            "unread",
            "unread_count",
            "last_message_preview",
            "counterpart_username",
        ]
        read_only_fields = fields

    def get_unread(self, obj) -> bool:
        user = self.request_user()
        return bool(user and user.is_authenticated and is_alert_unread(obj, user))

    def get_unread_count(self, obj) -> int:
        user = self.request_user()
        return unread_count_for_alert(obj, user) if user and user.is_authenticated else 0

    def get_last_message_preview(self, obj) -> str:
        return alert_last_message_preview(obj)

    def get_counterpart_username(self, obj) -> str:
        user = self.request_user()
        if not user or not user.is_authenticated:
            return ""
        if obj.owner_id == user.id:
            return getattr(obj.reporter, "username", "") or ""
        return getattr(obj.owner, "username", "") or ""

    def get_quiz_template_title(self, obj) -> str:
        language = obj.reported_language or self.preferred_language()
        return obj.quiz.quiz_template.get_localized_content(language).get("title", "") or obj.quiz.quiz_template.title


class QuizAlertThreadDetailSerializer(QuizAlertThreadListSerializer):
    reporter_summary = serializers.SerializerMethodField()
    owner_summary = serializers.SerializerMethodField()
    messages = QuizAlertMessageSerializer(many=True, read_only=True)
    can_reply = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()

    class Meta(QuizAlertThreadListSerializer.Meta):
        fields = QuizAlertThreadListSerializer.Meta.fields + [
            "reporter",
            "reporter_summary",
            "owner",
            "owner_summary",
            "closed_at",
            "closed_by",
            "messages",
            "can_reply",
            "can_manage",
        ]
        read_only_fields = fields

    @extend_schema_field(UserSummarySerializer(allow_null=True))
    def get_reporter_summary(self, obj) -> dict | None:
        if obj.reporter_id is None:
            return None
        return {
            "id": obj.reporter_id,
            "username": obj.reporter.username,
        }

    @extend_schema_field(UserSummarySerializer(allow_null=True))
    def get_owner_summary(self, obj) -> dict | None:
        if obj.owner_id is None:
            return None
        return {
            "id": obj.owner_id,
            "username": obj.owner.username,
        }

    def get_can_reply(self, obj) -> bool:
        user = self.request_user()
        return bool(user and user.is_authenticated and can_reply_to_alert(obj, user))

    def get_can_manage(self, obj) -> bool:
        user = self.request_user()
        return bool(user and user.is_authenticated and can_manage_alert(obj, user))


class QuizAlertThreadCreateSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    body = serializers.CharField(trim_whitespace=True, min_length=3, max_length=4000)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        quiz_id = attrs["quiz_id"]
        question_id = attrs["question_id"]

        try:
            quiz = Quiz.objects.select_related("quiz_template", "user").get(pk=quiz_id)
        except Quiz.DoesNotExist:
            raise serializers.ValidationError({"quiz_id": "Quiz introuvable."})

        if not (user.is_staff or user.is_superuser) and quiz.user_id != user.id:
            raise serializers.ValidationError({"quiz_id": "Ce quiz ne vous appartient pas."})

        try:
            quizquestion = QuizQuestion.objects.select_related("question", "quiz").get(
                quiz=quiz.quiz_template,
                question_id=question_id,
            )
        except QuizQuestion.DoesNotExist:
            raise serializers.ValidationError({"question_id": "Cette question n'appartient pas à ce quiz."})

        owner = quiz.quiz_template.created_by
        if owner is None:
            raise serializers.ValidationError({"quiz_id": "Ce quiz n'a pas de propriétaire contactable."})

        attrs["quiz"] = quiz
        attrs["quizquestion"] = quizquestion
        attrs["owner"] = owner
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        now = self.context.get("now")
        language = getattr(user, "language", None) or getattr(request, "LANGUAGE_CODE", None) or "en"
        return create_alert_thread(
            reporter=user,
            quiz=validated_data["quiz"],
            quizquestion=validated_data["quizquestion"],
            owner=validated_data["owner"],
            body=validated_data["body"],
            language=str(language),
            now=now,
        )


class QuizAlertMessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(trim_whitespace=True, min_length=1, max_length=4000)

    def validate(self, attrs):
        thread: QuizAlertThread = self.context["thread"]
        user = self.context["request"].user

        if not thread.can_user_reply(user):
            raise serializers.ValidationError({"detail": "Vous ne pouvez pas répondre à cette conversation."})

        attrs["body"] = attrs["body"].strip()
        return attrs

    def create(self, validated_data):
        thread: QuizAlertThread = self.context["thread"]
        user = self.context["request"].user
        now = self.context.get("now")
        return append_alert_message(
            thread=thread,
            author=user,
            body=validated_data["body"],
            now=now,
        )


class QuizAlertThreadPartialSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAlertThread
        fields = ["reporter_reply_allowed"]

    def validate(self, attrs):
        thread: QuizAlertThread = self.instance
        user = self.context["request"].user
        if thread is None or not thread.is_owner_user(user):
            raise serializers.ValidationError({"detail": "Seul le créateur du quiz peut modifier cette conversation."})
        return attrs
