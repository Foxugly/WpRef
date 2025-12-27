from django.db import transaction
from domain.models import Domain
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import inline_serializer, extend_schema_field
from rest_framework import serializers
from subject.models import Subject
from subject.serializers import SubjectReadSerializer, SubjectWriteSerializer

from .models import Question, QuestionMedia, AnswerOption


@extend_schema_field(OpenApiTypes.BINARY)
class BinaryFileField(serializers.FileField):
    pass


# -----------------------------
# Schémas "input" adaptés à ton endpoint
# -----------------------------

# 1) Payload multipart : tu reçois des STRINGS pour answer_options/media (JSON string),
#    et subject_ids comme liste (subject_ids=1&subject_ids=2)
QuestionMultipartWriteSerializer = inline_serializer(
    name="QuestionMultipartWrite",
    fields={
        # champs Question (mets ici ceux qui sont réellement write côté QuestionSerializer)
        "translations": serializers.CharField(
            required=True,
            help_text='JSON string ex: {"fr":{"title":"...","description":"","explanation":""},"nl":{...}}'
        ),

        # convention frontend
        "subject_ids": serializers.ListField(
            child=serializers.IntegerField(),
            required=False,
            help_text="Envoyer en multipart comme subject_ids=1&subject_ids=2 (QueryDict.getlist)."
        ),

        # JSON string qui sera parsé par _coerce_json_fields()
        "answer_options": serializers.CharField(
            required=False,
            help_text=(
                'JSON string (liste) ex: '
                '[{"is_correct": true, "sort_order": 1, '
                '"translations": {"fr": {"content": "A"}, "nl": {"content": "A"}}}, '
                '{"is_correct": false, "sort_order": 2, '
                '"translations": {"fr": {"content": "B"}, "nl": {"content": "B"}}}]'
            )
        ),

        "media": serializers.CharField(
            required=False,
            help_text='JSON string (liste) ex: [{"kind":"external","external_url":"https://...", "sort_order":1}]'
        ),

        "media_files": serializers.ListField(
            child=BinaryFileField(),
            required=False,
            help_text="Envoyer en multipart avec la même clé répétée: media_files=<file1>, media_files=<file2>, ..."
        ),
    },
)


class QuestionLiteSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    class Meta:
        model = Question
        fields = ["id", "title"]  # tu peux ajouter d'autres champs si tu veux

    def get_title(self, obj: Question) -> str:
        return obj.safe_translation_getter("title", any_language=True) or ""


class QuestionMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionMedia
        fields = ["id", "kind", "file", "external_url", "sort_order"]
        read_only_fields = ["id", "file", "external_url", "kind"]


class QuestionAnswerOptionReadSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    class Meta:
        model = AnswerOption  # adapte si ton modèle s'appelle autrement
        fields = ["id", "content", "is_correct", "sort_order"]
        read_only_fields = ["id"]

    def get_content(self, obj):
        return obj.safe_translation_getter("content", any_language=True) or ""


class QuestionAnswerOptionWriteSerializer(serializers.ModelSerializer):
    translations = serializers.DictField(
        child=serializers.DictField(),
        write_only=True
    )

    class Meta:
        model = AnswerOption
        fields = ["id", "is_correct", "sort_order", "translations"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        translations = validated_data.pop("translations")
        option = AnswerOption.objects.create(**validated_data)

        for lang_code, data in translations.items():
            option.set_current_language(lang_code)
            option.content = data.get("content", "")
            option.save()

        return option

    def update(self, instance, validated_data):
        translations = validated_data.pop("translations", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if translations:
            for lang_code, data in translations.items():
                instance.set_current_language(lang_code)
                instance.content = data.get("content", "")
                instance.save()

        return instance

    # def validate(self, attrs):
    #     question = self.context.get("question")
    #     domain = question.domain
    #
    #     allowed = set(domain.allowed_languages.values_list("code", flat=True))
    #     provided = set(attrs.get("translations", {}).keys())
    #
    #     missing = allowed - provided
    #     extra = provided - allowed
    #
    #     if missing:
    #         raise serializers.ValidationError(
    #             {"translations": f"Langues manquantes: {sorted(missing)}"}
    #         )
    #     if extra:
    #         raise serializers.ValidationError(
    #             {"translations": f"Langues non autorisées: {sorted(extra)}"}
    #         )
    #     return attrs


class QuestionInQuizQuestionSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    answer_options = QuestionAnswerOptionReadSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        show_correct = kwargs.pop("show_correct", False)
        super().__init__(*args, **kwargs)
        view = self.context.get("view")
        swagger = getattr(view, "swagger_fake_view", False)

        if not show_correct and not swagger:
            self.fields["answer_options"].child.fields.pop("is_correct", None)

    class Meta:
        model = Question
        fields = ["id", "title", "answer_options"]

    def get_title(self, obj):
        return obj.safe_translation_getter("title", any_language=True) or ""

class QuestionReadSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    explanation = serializers.SerializerMethodField()
    subjects = SubjectReadSerializer(many=True, read_only=True)
    answer_options = QuestionAnswerOptionReadSerializer(many=True, read_only=True)
    media = QuestionMediaSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        show_correct = kwargs.pop("show_correct", False)
        super().__init__(*args, **kwargs)

        view = self.context.get("view")
        swagger = getattr(view, "swagger_fake_view", False)

        if not show_correct and not swagger:
            # masque is_correct uniquement à l’output normal
            self.fields["answer_options"].child.fields.pop("is_correct", None)

    class Meta:
        model = Question
        fields = [
            "id",
            "domain",
            "title",
            "description",
            "explanation",
            "allow_multiple_correct",
            "active",
            "is_mode_practice",
            "is_mode_exam",
            "subjects",
            "answer_options",
            "media",
            "created_at",
        ]
        read_only_fields = fields

    def get_title(self, obj):
        return obj.safe_translation_getter("title", any_language=True) or ""

    def get_description(self, obj):
        return obj.safe_translation_getter("description", any_language=True) or ""

    def get_explanation(self, obj):
        return obj.safe_translation_getter("explanation", any_language=True) or ""


class QuestionWriteSerializer(serializers.ModelSerializer):
    # sujets en lecture
    subjects = SubjectReadSerializer(many=True, read_only=True)
    translations = serializers.DictField(child=serializers.DictField(), write_only=True, required=False, )

    # réponses
    answer_options = QuestionAnswerOptionWriteSerializer(many=True, required=False)

    # médias : read_only, gérés par la vue
    media = QuestionMediaSerializer(many=True, read_only=True)

    subject_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        show_correct = kwargs.pop("show_correct", False)
        super().__init__(*args, **kwargs)

        view = self.context.get("view")
        swagger = getattr(view, "swagger_fake_view", False)

        # Important: ne pas masquer is_correct pendant la génération OpenAPI
        #if not show_correct and not swagger:
        #    self.fields["answer_options"].child.fields.pop("is_correct", None)

    class Meta:
        model = Question
        fields = [
            "id",
            "domain",
            "translations",
            "allow_multiple_correct",
            "active",
            "is_mode_practice",
            "is_mode_exam",
            "subjects",
            "subject_ids",
            "answer_options",
            "media",
            "created_at",
        ]
        read_only_fields = ["id", "subjects", "media", "created_at"]

    # ---------- helpers ----------
    def _apply_question_translations(self, question: Question, translations: dict):
        for lang_code, data in translations.items():
            question.set_current_language(lang_code)
            if "title" in data:
                question.title = data["title"]
            if "description" in data:
                question.description = data["description"]
            if "explanation" in data:
                question.explanation = data["explanation"]
            question.save()

    def _recreate_answer_options(self, question: Question, answer_options_data: list, allowed_langs: set[str]):
        question.answer_options.all().delete()

        for ao in answer_options_data:
            ao_trans = ao.pop("translations", {})
            opt = AnswerOption.objects.create(question=question, **ao)

            for lang_code in allowed_langs:
                data = ao_trans.get(lang_code, {})
                opt.set_current_language(lang_code)
                opt.content = data.get("content", "")
                opt.save()

    # ---------------------------
    # CREATE
    # ---------------------------
    @transaction.atomic
    def create(self, validated_data):
        subject_ids = validated_data.pop("subject_ids", [])
        answer_options_data = validated_data.pop("answer_options", [])
        translations = validated_data.pop("translations", None)
        if not translations:
            raise serializers.ValidationError({"translations": "Au moins une traduction est requise."})
        # 1) Question
        question = Question.objects.create(**validated_data)
        # 2) sujets (M2M)
        if subject_ids:
            question.subjects.set(Subject.objects.filter(id__in=subject_ids))

        self._apply_question_translations(question, translations)

        allowed = set(question.domain.allowed_languages.values_list("code", flat=True))
        if answer_options_data:
            self._recreate_answer_options(question, answer_options_data, allowed)
        return question

    # ---------------------------
    # UPDATE
    # ---------------------------
    @transaction.atomic
    def update(self, instance, validated_data):
        translations = validated_data.pop("translations", None)
        subject_ids = validated_data.pop("subject_ids", None)
        answer_options_data = validated_data.pop("answer_options", None)
        # 1) champs simples
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # 2) sujets (M2M)
        if subject_ids is not None:
            instance.subjects.set(Subject.objects.filter(id__in=subject_ids))
        # 3) réponses : stratégie simple = wipe + recreate
        if translations is not None:
            self._apply_question_translations(instance, translations)

        if answer_options_data is not None:
            allowed = set(instance.domain.allowed_languages.values_list("code", flat=True))
            self._recreate_answer_options(instance, answer_options_data, allowed)
        # les médias sont gérés dans le ViewSet via _handle_media_upload()
        return instance

    def validate(self, attrs):
        domain: Domain = attrs.get("domain") or getattr(self.instance, "domain", None)
        if domain is None:
            raise serializers.ValidationError({"domain": "Champ requis."})
        allowed = set(domain.allowed_languages.values_list("code", flat=True))

        is_create = self.instance is None
        #is_partial = getattr(self, "partial", False)

        if is_create and not attrs.get("translations"):
            raise serializers.ValidationError({"translations": "Au moins une traduction est requise."})

        if "translations" in attrs:
            provided = set((attrs.get("translations") or {}).keys())
            missing = allowed - provided
            extra = provided - allowed
            if missing and is_create:
                raise serializers.ValidationError({"translations": f"Langues manquantes: {sorted(missing)}"})
            if extra:
                raise serializers.ValidationError({"translations": f"Langues non autorisées: {sorted(extra)}"})

        # ---- answer_options rules ----
        allow_multiple = attrs.get(
            "allow_multiple_correct",
            getattr(self.instance, "allow_multiple_correct", False),
        )
        if "answer_options" in attrs:
            aos = attrs.get("answer_options") or []

            # règle "au moins 2" seulement en create
            if is_create and len(aos) < 2:
                raise serializers.ValidationError({"answer_options": "Au moins 2 réponses sont requises."})

            correct_count = 0
            for i, ao in enumerate(aos):
                p = set((ao.get("translations") or {}).keys())
                if allowed - p:
                    raise serializers.ValidationError(
                        {f"answer_options[{i}].translations": f"Langues manquantes: {sorted(allowed - p)}"})
                if p - allowed:
                    raise serializers.ValidationError(
                        {f"answer_options[{i}].translations": f"Langues non autorisées: {sorted(p - allowed)}"})
                correct_count += 1 if ao.get("is_correct") else 0

            if correct_count == 0:
                raise serializers.ValidationError({"answer_options": "Indique au moins une réponse correcte."})

            if not allow_multiple and correct_count != 1:
                raise serializers.ValidationError({"answer_options": "Une seule réponse correcte est autorisée."})
        elif (self.instance is not None) and ("allow_multiple_correct" in attrs):
            correct_in_db = self.instance.answer_options.filter(is_correct=True).count()
            if correct_in_db == 0:
                raise serializers.ValidationError({"answer_options": "Indique au moins une réponse correcte."})
            if not allow_multiple and correct_in_db != 1:
                raise serializers.ValidationError({"answer_options": "Une seule réponse correcte est autorisée."})

        return attrs

