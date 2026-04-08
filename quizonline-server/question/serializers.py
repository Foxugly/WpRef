import hashlib
import os
from typing import List, Any

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import translation
from domain.models import Domain
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from subject.models import Subject
from subject.serializers import SubjectReadSerializer

from .answer_option_sync import sync_question_answer_options
from .models import Question, QuestionMedia, AnswerOption, MediaAsset
from config.serializers import (
    LocalizedAnswerOptionTranslationSerializer,
    LocalizedTranslationsJSONField,
    LocalizedQuestionTranslationSerializer,
    SerializerListJSONField,
    localized_translations_map_schema,
)

from domain.serializers import DomainReadSerializer


def _translated_value(obj, field: str) -> str:
    language_code = translation.get_language() or settings.LANGUAGE_CODE
    fallback = None
    for t in obj.translations.all():  # uses prefetch cache when available
        val = getattr(t, field, None) or ""
        if t.language_code == language_code and val:
            return val
        if fallback is None and val:
            fallback = val
    return fallback or ""


def _serialized_translations(obj, fields: list[str]) -> dict:
    data = {}
    for translation_obj in obj.translations.all():
        data[translation_obj.language_code] = {
            field: getattr(translation_obj, field, "") or ""
            for field in fields
        }
    return data


def _upsert_translations(obj, translations: dict, *, fields: list[str]) -> None:
    translation_model = obj._parler_meta.root_model
    for language_code, payload in translations.items():
        defaults = {
            field: payload.get(field, "")
            for field in fields
            if field in payload
        }
        translation_model.objects.update_or_create(
            master_id=obj.pk,
            language_code=language_code,
            defaults=defaults,
        )


class QuestionLiteSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "title"]

    def get_title(self, obj: Question) -> str:
        return _translated_value(obj, "title")


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
    file = serializers.FileField(required=False)
    external_url = serializers.URLField(required=False)
    kind = serializers.ChoiceField(
        choices=[MediaAsset.IMAGE, MediaAsset.VIDEO, MediaAsset.EXTERNAL],
        required=False,
    )

    def validate(self, attrs):
        f = attrs.get("file")
        url = attrs.get("external_url")
        if bool(f) == bool(url):
            raise serializers.ValidationError("Provide exactly one of: file OR external_url.")
        if f is not None and f.size > settings.MAX_UPLOAD_FILE_SIZE:
            max_size_mb = settings.MAX_UPLOAD_FILE_SIZE / (1024 * 1024)
            raise serializers.ValidationError(
                {"file": f"File too large. Maximum allowed size is {max_size_mb:.0f} MB."}
            )
        return attrs


def _sha256_file(f: UploadedFile) -> str:
    h = hashlib.sha256()
    for chunk in f.chunks():
        h.update(chunk)
    return h.hexdigest()


def _infer_kind_from_upload(f: UploadedFile) -> str:
    ct = (getattr(f, "content_type", "") or "").lower()
    extension = os.path.splitext(getattr(f, "name", "") or "")[1].lower()

    allowed_image_types = {"image/png", "image/jpeg", "image/webp", "image/gif"}
    allowed_video_types = {"video/mp4", "video/webm", "video/ogg", "video/quicktime"}
    allowed_image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    allowed_video_extensions = {".mp4", ".webm", ".ogv", ".ogg", ".mov"}

    if ct in allowed_image_types and extension in allowed_image_extensions:
        return MediaAsset.IMAGE
    if ct in allowed_video_types and extension in allowed_video_extensions:
        return MediaAsset.VIDEO
    raise serializers.ValidationError(
        {
            "file": (
                f"Unsupported file type '{ct}' / '{extension}'. "
                "Only png, jpg, jpeg, webp, gif, mp4, webm, ogg and mov are allowed."
            )
        }
    )


class QuestionAnswerOptionPublicReadSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    class Meta:
        model = AnswerOption
        fields = ["id", "content", "sort_order"]
        read_only_fields = ["id"]

    def get_content(self, obj) -> str:
        return _translated_value(obj, "content")


class QuestionAnswerOptionReadSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()
    is_correct = serializers.SerializerMethodField()

    class Meta:
        model = AnswerOption  # adapte si ton modèle s'appelle autrement
        fields = ["id", "content", "translations", "is_correct", "sort_order"]
        read_only_fields = ["id"]

    def get_content(self, obj) -> str:
        return _translated_value(obj, "content")

    @extend_schema_field(serializers.BooleanField(allow_null=True))
    def get_is_correct(self, obj) -> bool | None:
        state = _correctness_state(self.context)

        if state == "unknown":
            return None

        if state == "full":
            return bool(obj.is_correct)

        return None

    @extend_schema_field(
        localized_translations_map_schema(
            LocalizedAnswerOptionTranslationSerializer,
            "LocalizedAnswerOptionTranslations",
        )
    )
    def get_translations(self, obj) -> dict:
        return _serialized_translations(obj, ["content"])


class QuestionAnswerOptionWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    translations = LocalizedTranslationsJSONField(
        value_serializer=LocalizedAnswerOptionTranslationSerializer,
        write_only=True,
    )

    class Meta:
        model = AnswerOption
        fields = ["id", "is_correct", "sort_order", "translations"]

    def validate_translations(self, value: dict) -> dict:
        # (optionnel) contrôle minimal de forme
        if not isinstance(value, dict):
            raise serializers.ValidationError("translations must be an object keyed by language code.")
        for lang_code, payload in value.items():
            if not isinstance(payload, dict):
                raise serializers.ValidationError(f"translations['{lang_code}'] must be an object.")
        return value


def _correctness_state(context: dict) -> str:
    state = context.get("show_correct_state")
    if state is not None:
        return state
    if "show_correct" in context:
        return "full" if bool(context.get("show_correct", False)) else "hidden"
    return "hidden"


def _option_read_serializer(context: dict, swagger: bool):
    state = _correctness_state(context)
    return QuestionAnswerOptionReadSerializer if (state in {"full", "unknown"} or swagger) else QuestionAnswerOptionPublicReadSerializer


class QuestionInQuizQuestionSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    answer_options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "title", "answer_options"]

    def get_title(self, obj: Question) -> str:
        return _translated_value(obj, "title")

    @extend_schema_field(QuestionAnswerOptionReadSerializer(many=True))
    def get_answer_options(self, obj) -> List[Any]:
        swagger = bool(getattr(self.context.get("view"), "swagger_fake_view", False))
        qaors = _option_read_serializer(self.context, swagger)
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

    @extend_schema_field(
        localized_translations_map_schema(
            LocalizedQuestionTranslationSerializer,
            "LocalizedQuestionTranslations",
        )
    )
    def get_translations(self, obj: Question) -> dict:
        return _serialized_translations(obj, ["title", "description", "explanation"])


    @extend_schema_field(QuestionAnswerOptionReadSerializer(many=True))
    def get_answer_options(self, obj) -> List[Any]:
        swagger = bool(getattr(self.context.get("view"), "swagger_fake_view", False))
        qaors = _option_read_serializer(self.context, swagger)
        return qaors(obj.answer_options.all(), many=True, context=self.context).data


class QuestionWriteSerializer(serializers.ModelSerializer):
    translations = LocalizedTranslationsJSONField(
        value_serializer=LocalizedQuestionTranslationSerializer,
        write_only=True,
        required=False,
        help_text="Object or JSON string (multipart). Dict keyed by language code."
    )
    answer_options = SerializerListJSONField(
        item_serializer=QuestionAnswerOptionWriteSerializer,
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

    def _validate_subject_ids_for_domain(self, domain: Domain, subject_ids: list[int]) -> None:
        if not subject_ids:
            return

        subjects = list(Subject.objects.filter(id__in=subject_ids).only("id", "domain_id"))
        found = {subject.id for subject in subjects}
        missing = set(subject_ids) - found
        if missing:
            raise serializers.ValidationError({"subject_ids": f"Subjects inexistants: {sorted(missing)}"})

        invalid = sorted(subject.id for subject in subjects if subject.domain_id != domain.id)
        if invalid:
            raise serializers.ValidationError({"subject_ids": f"Subjects hors domain {domain.id}: {invalid}"})

    def _validate_existing_subjects_for_domain(self, question: Question, domain: Domain) -> None:
        invalid = sorted(question.subjects.exclude(domain=domain).values_list("id", flat=True))
        if invalid:
            raise serializers.ValidationError({
                "subject_ids": (
                    "Les subjects déjà liés à la question ne correspondent pas au nouveau domain. "
                    f"Subjects invalides: {invalid}"
                )
            })

    # ---------- helpers ----------
    def _apply_question_translations(self, question: Question, translations: dict):
        _upsert_translations(
            question,
            translations,
            fields=["title", "description", "explanation"],
        )
        question.refresh_from_db()

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
            question.subjects.set(subjects)

        self._apply_question_translations(question, translations)

        allowed = set(question.domain.allowed_languages.values_list("code", flat=True))
        if answer_options_data:
            sync_question_answer_options(
                question=question,
                answer_options_data=answer_options_data,
                allowed_langs=allowed,
                upsert_translations=_upsert_translations,
            )
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
            instance.subjects.set(subjects)
        # 3) réponses : stratégie simple = wipe + recreate
        if translations is not None:
            self._apply_question_translations(instance, translations)

        if answer_options_data is not None:
            allowed = set(instance.domain.allowed_languages.values_list("code", flat=True))
            sync_question_answer_options(
                question=instance,
                answer_options_data=answer_options_data,
                allowed_langs=allowed,
                upsert_translations=_upsert_translations,
            )
        # les médias sont gérés dans le ViewSet via _handle_media_upload()
        if asset_ids is not None:
            self._set_media_assets(instance, asset_ids, replace=True)
        return instance

    def validate(self, attrs):
        domain: Domain = attrs.get("domain") or getattr(self.instance, "domain", None)
        if domain is None:
            raise serializers.ValidationError({"domain": "Champ requis."})
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            if not getattr(user, "is_superuser", False) and not user.can_manage_domain(domain):
                raise serializers.ValidationError({"domain": "Vous ne pouvez pas gerer ce domaine."})
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

        if "subject_ids" in attrs:
            self._validate_subject_ids_for_domain(domain, attrs.get("subject_ids") or [])
        elif self.instance is not None and "domain" in attrs:
            self._validate_existing_subjects_for_domain(self.instance, domain)

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
