import hashlib
from typing import List, Any

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from domain.models import Domain
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import inline_serializer, extend_schema_field
from rest_framework import serializers
from subject.models import Subject
from subject.serializers import SubjectReadSerializer, SubjectWriteSerializer

from .models import Question, QuestionMedia, AnswerOption, MediaAsset
from wpref.serializers import JSONDictOrStringField, JSONListOrStringField

from domain.serializers import DomainReadSerializer


class QuestionLiteSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "title"]

    def get_title(self, obj: Question) -> str:
        return obj.safe_translation_getter("title", any_language=True) or ""


class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = ["id", "kind", "file", "external_url", "sha256", "created_at"]
        read_only_fields = fields


class QuestionMediaReadSerializer(serializers.ModelSerializer):
    asset = MediaAssetSerializer(read_only=True)

    class Meta:
        model = QuestionMedia
        fields = ["id", "sort_order", "asset"]
        read_only_fields = fields


class MediaAssetUploadSerializer(serializers.Serializer):
    # multipart: file=<...>
    file = serializers.FileField(required=False)
    # JSON or form: external_url="https://..."
    external_url = serializers.URLField(required=False)
    # optional explicit kind (otherwise inferred)
    kind = serializers.ChoiceField(
        choices=[MediaAsset.IMAGE, MediaAsset.VIDEO, MediaAsset.EXTERNAL],
        required=False,
    )

    def validate(self, attrs):
        f = attrs.get("file")
        url = attrs.get("external_url")
        if bool(f) == bool(url):
            raise serializers.ValidationError("Provide exactly one of: file OR external_url.")
        return attrs


def _sha256_file(f: UploadedFile) -> str:
    h = hashlib.sha256()
    for chunk in f.chunks():
        h.update(chunk)
    return h.hexdigest()


def _infer_kind_from_upload(f: UploadedFile) -> str:
    ct = (getattr(f, "content_type", "") or "").lower()
    if ct.startswith("image/"):
        return MediaAsset.IMAGE
    if ct.startswith("video/"):
        return MediaAsset.VIDEO
    # fallback: treat as VIDEO? better to reject unknown
    raise serializers.ValidationError({"file": f"Unsupported content_type '{ct}'. Only image/* or video/*."})


class QuestionAnswerOptionPublicReadSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    class Meta:
        model = AnswerOption
        fields = ["id", "content", "sort_order"]
        read_only_fields = ["id"]

    def get_content(self, obj) -> str:
        return obj.safe_translation_getter("content", any_language=True) or ""


class QuestionAnswerOptionReadSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    class Meta:
        model = AnswerOption  # adapte si ton modèle s'appelle autrement
        fields = ["id", "content", "is_correct", "sort_order"]
        read_only_fields = ["id"]

    def get_content(self, obj) -> str:
        return obj.safe_translation_getter("content", any_language=True) or ""


class QuestionAnswerOptionWriteSerializer(serializers.ModelSerializer):
    translations = JSONDictOrStringField(write_only=True)

    class Meta:
        model = AnswerOption
        fields = ["id", "is_correct", "sort_order", "translations"]
        read_only_fields = ["id"]

    def validate_translations(self, value: dict) -> dict:
        # (optionnel) contrôle minimal de forme
        if not isinstance(value, dict):
            raise serializers.ValidationError("translations must be an object keyed by language code.")
        for lang_code, payload in value.items():
            if not isinstance(payload, dict):
                raise serializers.ValidationError(f"translations['{lang_code}'] must be an object.")
        return value


class QuestionInQuizQuestionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="safe_translation_getter", read_only=True)
    answer_options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "title", "answer_options"]

    @extend_schema_field(QuestionAnswerOptionReadSerializer(many=True))
    def get_answer_options(self, obj) -> List[Any]:
        show_correct = bool(self.context.get("show_correct", False))
        swagger = bool(getattr(self.context.get("view"), "swagger_fake_view", False))

        qaors = QuestionAnswerOptionReadSerializer if (
                show_correct or swagger) else QuestionAnswerOptionPublicReadSerializer
        return qaors(obj.answer_options.all(), many=True, context=self.context).data


class QuestionReadSerializer(serializers.ModelSerializer):
    translations = serializers.SerializerMethodField()
    subjects = SubjectReadSerializer(many=True, read_only=True)
    answer_options = serializers.SerializerMethodField()
    media = QuestionMediaReadSerializer(many=True, read_only=True)
    domain = DomainReadSerializer(read_only=True)

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
            "answer_options",
            "media",
            "created_at",
        ]
        read_only_fields = fields

    def get_translations(self, obj: Question) -> dict:
        data = {}
        for t in obj.translations.all():
            data[t.language_code] = {
                "title": t.title or "",
                "description": t.description or "",
                "explanation": t.explanation or "",
            }
        return data


    @extend_schema_field(QuestionAnswerOptionReadSerializer(many=True))
    def get_answer_options(self, obj) -> List[Any]:
        show_correct = bool(self.context.get("show_correct", False))
        swagger = bool(getattr(self.context.get("view"), "swagger_fake_view", False))

        qaors = QuestionAnswerOptionReadSerializer if (
                show_correct or swagger) else QuestionAnswerOptionPublicReadSerializer
        return qaors(obj.answer_options.all(), many=True, context=self.context).data


class QuestionWriteSerializer(serializers.ModelSerializer):
    translations = JSONDictOrStringField(
        write_only=True,
        required=False,
        help_text="Object or JSON string (multipart). Dict keyed by language code."
    )
    answer_options = JSONListOrStringField(
        write_only=True,
        required=False,
        help_text="List or JSON string (multipart). Each item: {is_correct, sort_order, translations{lang:{content}}}"
    )
    media_asset_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text=(
            "IDs des MediaAsset uploadés au préalable. "
            "L'ordre dans la liste définit l'ordre d'affichage des médias."
        ),
    )

    subject_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

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
            "subject_ids",
            "answer_options",
            "media_asset_ids",
        ]
        read_only_fields = ["id"]

    def _set_media_assets(self, question: Question, asset_ids: list[int], *, replace: bool):
        if replace:
            QuestionMedia.objects.filter(question=question).delete()

        assets = list(MediaAsset.objects.filter(id__in=asset_ids))
        found = {a.id for a in assets}
        missing = set(asset_ids) - found
        if missing:
            raise serializers.ValidationError({"media_asset_ids": f"Assets inexistants: {sorted(missing)}"})
        seen = set()
        set_asset_ids = [x for x in asset_ids if not (x in seen or seen.add(x))]
        QuestionMedia.objects.bulk_create([
            QuestionMedia(question=question, asset_id=aid, sort_order=i)
            for i, aid in enumerate(set_asset_ids)
        ])

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

    def _recreate_answer_options(self, question: Question, answer_options_data: List, allowed_langs: set[str]):
        question.answer_options.all().delete()

        for i, ao in enumerate(answer_options_data):
            if not isinstance(ao, dict):
                raise serializers.ValidationError({f"answer_options[{i}]": "Each item must be an object."})

            ao_trans = ao.get("translations") or {}
            if not isinstance(ao_trans, dict):
                raise serializers.ValidationError(
                    {f"answer_options[{i}].translations": "Must be an object keyed by language code."})

            ao = dict(ao)
            ao.pop("translations", None)

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
        asset_ids = validated_data.pop("media_asset_ids", [])
        translations = validated_data.pop("translations", None)
        if not translations:
            raise serializers.ValidationError({"translations": "Au moins une traduction est requise."})

        # 1) Question
        question = Question.objects.create(**validated_data)
        # 2) sujets (M2M)
        if subject_ids:
            subjects = list(Subject.objects.filter(id__in=subject_ids))
            found = {s.id for s in subjects}
            missing = set(subject_ids) - found
            if missing:
                raise serializers.ValidationError({"subject_ids": f"Subjects inexistants: {sorted(missing)}"})
            question.subjects.set(subjects)

        self._apply_question_translations(question, translations)

        allowed = set(question.domain.allowed_languages.values_list("code", flat=True))
        if answer_options_data:
            self._recreate_answer_options(question, answer_options_data, allowed)
        if asset_ids:
            self._set_media_assets(question, asset_ids, replace=False)
        return question

    # ---------------------------
    # UPDATE
    # ---------------------------
    @transaction.atomic
    def update(self, instance, validated_data):
        translations = validated_data.pop("translations", None)
        subject_ids = validated_data.pop("subject_ids", None)
        asset_ids = validated_data.pop("media_asset_ids", None)
        answer_options_data = validated_data.pop("answer_options", None)
        # 1) champs simples
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # 2) sujets (M2M)
        if subject_ids is not None:
            subjects = list(Subject.objects.filter(id__in=subject_ids))
            found = {s.id for s in subjects}
            missing = set(subject_ids) - found
            if missing:
                raise serializers.ValidationError({"subject_ids": f"Subjects inexistants: {sorted(missing)}"})
            instance.subjects.set(subjects)
        # 3) réponses : stratégie simple = wipe + recreate
        if translations is not None:
            self._apply_question_translations(instance, translations)

        if answer_options_data is not None:
            allowed = set(instance.domain.allowed_languages.values_list("code", flat=True))
            self._recreate_answer_options(instance, answer_options_data, allowed)
        # les médias sont gérés dans le ViewSet via _handle_media_upload()
        if asset_ids is not None:
            self._set_media_assets(instance, asset_ids, replace=True)
        return instance

    def validate(self, attrs):
        domain: Domain = attrs.get("domain") or getattr(self.instance, "domain", None)
        if domain is None:
            raise serializers.ValidationError({"domain": "Champ requis."})
        allowed = set(domain.allowed_languages.values_list("code", flat=True))

        is_create = self.instance is None
        # is_partial = getattr(self, "partial", False)

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
                if not isinstance(ao, dict):
                    raise serializers.ValidationError({f"answer_options[{i}]": "Each item must be an object."})

                tr = ao.get("translations") or {}
                if not isinstance(tr, dict):
                    raise serializers.ValidationError(
                        {f"answer_options[{i}].translations": "Must be an object keyed by language code."})

                p = set(tr.keys())

                if allowed - p:
                    raise serializers.ValidationError(
                        {f"answer_options[{i}].translations": f"Langues manquantes: {sorted(allowed - p)}"}
                    )
                if p - allowed:
                    raise serializers.ValidationError(
                        {f"answer_options[{i}].translations": f"Langues non autorisées: {sorted(p - allowed)}"}
                    )

                correct_count += 1 if bool(ao.get("is_correct")) else 0

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
