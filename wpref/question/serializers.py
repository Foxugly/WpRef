from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import inline_serializer, extend_schema_field
from rest_framework import serializers
from subject.models import Subject
from subject.serializers import SubjectSerializer

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
        "title": serializers.CharField(required=False),
        "description": serializers.CharField(required=False, allow_blank=True),

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
                "JSON string (liste) ex: "
                '[{"text":"A","is_correct":true},{"text":"B","is_correct":false}]'
            )
        ),
        # ✅ meta média (externals + ordre + kind)
        "media": serializers.CharField(
            required=False,
            help_text='JSON string (liste) ex: [{"kind":"external","external_url":"https://...", "sort_order":1}]'
        ),

        # ✅ fichiers uploadés (N)
        "media_files": serializers.ListField(
            child=BinaryFileField(),
            required=False,
            help_text="Envoyer en multipart avec la même clé répétée: media_files=<file1>, media_files=<file2>, ..."
        ),
    },
)


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


class QuestionInQuizQuestionSerializer(serializers.ModelSerializer):
    answer_options = QuestionAnswerOptionSerializer(many=True, read_only=True)

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

    def __init__(self, *args, **kwargs):
        show_correct = kwargs.pop("show_correct", False)
        super().__init__(*args, **kwargs)

        view = self.context.get("view")
        swagger = getattr(view, "swagger_fake_view", False)

        # Important: ne pas masquer is_correct pendant la génération OpenAPI
        if not show_correct and not swagger:
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

    def validate(self, attrs):
        # PATCH: si answer_options n'est pas envoyé, on ne valide pas cette partie
        if "answer_options" not in attrs:
            return attrs

        answer_options = attrs.get("answer_options") or []
        if len(answer_options) < 2:
            raise serializers.ValidationError({
                "answer_options": "Une question doit avoir au moins 2 réponses possibles."
            })

        correct_count = sum(1 for opt in answer_options if opt.get("is_correct"))

        allow_multiple = attrs.get(
            "allow_multiple_correct",
            getattr(self.instance, "allow_multiple_correct", False),
        )

        if correct_count == 0:
            raise serializers.ValidationError({"answer_options": "Indique au moins une réponse correcte."})

        if not allow_multiple and correct_count != 1:
            raise serializers.ValidationError({"answer_options": "Une seule réponse correcte est autorisée."})

        return attrs
