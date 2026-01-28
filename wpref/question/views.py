import logging

from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.http import QueryDict
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
)
from rest_framework import status, serializers
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from wpref.tools import ErrorDetailSerializer
from wpref.tools import MyModelViewSet

from .models import Question, MediaAsset
from .serializers import QuestionReadSerializer, QuestionWriteSerializer, MediaAssetSerializer, \
    MediaAssetUploadSerializer, _infer_kind_from_upload, _sha256_file

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=["Question"],
        summary="Lister les questions",
        description=(
                "Liste paginée des questions.\n\n"
                "Supporte :\n"
                "- `search` (filtre title__icontains)\n"
        ),
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Recherche simple (title__icontains).",
            ),
        ],
        responses={
            200: QuestionReadSerializer(many=True),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    retrieve=extend_schema(
        tags=["Question"],
        summary="Récupérer une question",
        parameters=[
            OpenApiParameter(
                name="question_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID de la question (question_id).",
            )
        ],
        responses={
            200: QuestionReadSerializer,
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    create=extend_schema(
        tags=["Question"],
        summary="Créer une question (multipart ou JSON)",
        description=(
                "Crée une question.\n\n"
                "⚠️ Les médias NE sont PAS uploadés ici.\n\n"
                "Workflow recommandé :\n"
                "1. POST /api/question/media/ → upload fichier ou URL externe\n"
                "2. Récupérer les `id` des MediaAsset retournés\n"
                "3. POST /api/question/ avec `media_asset_ids: [1, 2, 3]`\n\n"
                "Payload supporté : JSON ou multipart/form-data.\n"
                "- `subject_ids`: liste d'IDs\n"
                "- `answer_options`: JSON (liste)\n"
                "- `media_asset_ids`: liste d'IDs MediaAsset\n"
        ),
        request=QuestionWriteSerializer,
        responses={
            201: QuestionReadSerializer,
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Validation error"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    update=extend_schema(
        tags=["Question"],
        summary="Mettre à jour une question (PUT)",
        description=(
                "Met à jour une question.\n\n"
                "Les médias sont gérés via `/api/question/media/`.\n"
                "Utiliser `media_asset_ids` pour lier/délier les médias.\n"
        ),
        parameters=[
            OpenApiParameter(
                name="question_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID de la question (question_id).",
            )
        ],
        request=QuestionWriteSerializer,
        responses={
            200: QuestionReadSerializer,
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Validation error"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    partial_update=extend_schema(
        tags=["Question"],
        summary="Mettre à jour une question (PATCH)",
        description=(
                "Met à jour une question.\n\n"
                "Les médias sont gérés via `/api/question/media/`.\n"
                "Utiliser `media_asset_ids` pour lier/délier les médias.\n"
        ),
        parameters=[
            OpenApiParameter(
                name="question_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID de la question (question_id).",
            )
        ],
        request=QuestionWriteSerializer,
        responses={
            200: QuestionReadSerializer,
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Validation error"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    destroy=extend_schema(
        tags=["Question"],
        summary="Supprimer une question",
        parameters=[
            OpenApiParameter(
                name="question_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID de la question (question_id).",
            )
        ],
        responses={
            204: OpenApiResponse(description="No Content"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    media= extend_schema(
        tags=["Question"],
        summary="Uploader un média (dédup sha256) ou enregistrer un média externe",
        description=(
                "Upload un fichier (multipart) ou enregistre une URL externe.\n"
                "- multipart: envoyer `file`\n"
                "- json/form: envoyer `external_url`\n\n"
                "Retourne un `MediaAsset` (id à réutiliser dans `media_asset_ids` lors de la création/màj d'une Question)."
        ),
        request=MediaAssetUploadSerializer,
        responses={
            201: MediaAssetSerializer,
            200: MediaAssetSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
    ),
)
class QuestionViewSet(MyModelViewSet):
    queryset = (
        Question.objects
        .all()
        .select_related("domain")
        .prefetch_related("subjects", "translations", "answer_options__translations", "media__asset", )
    )
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["domain", "active", "is_mode_practice", "is_mode_exam"]
    lookup_field = "pk"
    lookup_url_kwarg = "question_id"

    def get_parsers(self):
        action = getattr(self, "action", None)
        if action in ["create","update"]:
            return [JSONParser()]
        return super().get_parsers()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        user = getattr(self.request, "user", None)
        ctx["show_correct"] = bool(
            user
            and user.is_authenticated
            and (user.is_staff or user.is_superuser)
        )
        return ctx

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return QuestionReadSerializer
        return QuestionWriteSerializer

    # ==========================================================
    # Permissions (explicites même si redondantes)
    # ==========================================================

    def get_permissions(self):
        return [IsAdminUser()]

    # ==========================================================
    # coercion JSON fields
    # ==========================================================
    def _coerce_json_fields(self, data):
        if isinstance(data, QueryDict):
            mutable = {}
            for key in data.keys():
                if key in ("subject_ids", "media_asset_ids"):
                    raw = data.getlist(key)
                    ids: list[int] = []
                    for item in raw:
                        if not item:
                            continue
                        parts = [p.strip() for p in str(item).split(",") if p.strip()]
                        for p in parts:
                            ids.append(int(p))
                    mutable[key] = ids
                else:
                    mutable[key] = data.get(key)
            return mutable
        return dict(data)
    # ==========================================================
    # CRUD implicite : surcharges
    # ==========================================================
    def list(self, request, *args, **kwargs):
        self._log_call(
            method_name="list",
            endpoint="GET /api/question/",
            input_expected="query params (search?, title?, description?), body vide",
            output="200 + [QuestionSerializer] (paginé)",
        )
        qs = self.filter_queryset(self.get_queryset())
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(translations__title__icontains=search).distinct()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        self._log_call(
            method_name="retrieve",
            endpoint="GET /api/question/{id}/",
            input_expected="path pk, body vide",
            output="200 + QuestionSerializer | 404",
        )
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(request=QuestionWriteSerializer)
    def create(self, request, *args, **kwargs):
        self._log_call(
            method_name="create",
            endpoint="POST /api/question/",
            input_expected="multipart/JSON (Question + subject_ids + answer_options + media_asset_ids)",
            output="201 + QuestionSerializer | 400",
        )
        data = self._coerce_json_fields(request.data)
        serializer = self.get_serializer(data=data, context=self.get_serializer_context())
        if not serializer.is_valid():
            logger.warning("CREATE errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        question = serializer.save()
        logger.info("Question created id=%s", question.id)
        return Response(QuestionReadSerializer(question, context=self.get_serializer_context()).data,
                        status=status.HTTP_201_CREATED)

    @extend_schema(request=QuestionWriteSerializer)
    def update(self, request, *args, **kwargs):
        self._log_call(
            method_name="update",
            endpoint="PUT /api/question/{id}/",
            input_expected="path pk + body multipart/JSON complet",
            output="200 + QuestionSerializer | 400 | 404",
        )
        return self._update_internal(request, partial=False)

    @extend_schema(request=QuestionWriteSerializer)
    def partial_update(self, request, *args, **kwargs):
        self._log_call(
            method_name="partial_update",
            endpoint="PATCH /api/question/{question_id}/",
            input_expected="path question_id + body multipart/JSON partiel",
            output="200 + QuestionSerializer | 400 | 404",
        )
        return self._update_internal(request, partial=True)

    def destroy(self, request, *args, **kwargs):
        self._log_call(
            method_name="destroy",
            endpoint="DELETE /api/question/{question_id}/",
            input_expected="path question_id, body vide",
            output="204 | 404",
        )
        return super().destroy(request, *args, **kwargs)

    # ==========================================================
    # Factorisation update / partial_update (propre)
    # ==========================================================
    def _update_internal(self, request, *, partial: bool):
        instance = self.get_object()
        data = self._coerce_json_fields(request.data)

        serializer = QuestionWriteSerializer(instance, data=data, partial=partial,
                                             context=self.get_serializer_context())
        if not serializer.is_valid():
            logger.warning("UPDATE errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.save()

        logger.info("Question updated id=%s partial=%s", question.id, partial)
        return Response(QuestionReadSerializer(question, context=self.get_serializer_context()).data,
                        status=status.HTTP_200_OK)

    # ==========================================================
    # Gestion des médias
    # ==========================================================
    def _upsert_external_asset(self, external_url: str):
        external_url = external_url.strip()

        asset, created = MediaAsset.objects.get_or_create(
            kind=MediaAsset.EXTERNAL,
            external_url=external_url,
            defaults={"sha256": None, "file": None},
        )
        return asset, created

    def _upsert_file_asset(self, upload_file):
        inferred_kind = _infer_kind_from_upload(upload_file)
        digest = _sha256_file(upload_file)

        try:
            with transaction.atomic():
                asset = MediaAsset.objects.create(
                    kind=inferred_kind,
                    file=upload_file,
                    sha256=digest,
                )
            return asset, True
        except (IntegrityError, ValidationError):
            asset = MediaAsset.objects.get(kind=inferred_kind, sha256=digest)
            return asset, False

    @action(detail=False, methods=["post"], url_path="media",
            parser_classes=[MultiPartParser, FormParser, JSONParser])
    def media(self, request, *args, **kwargs):
        self._log_call(
            method_name="media",
            endpoint="POST /api/question/media/",
            input_expected="multipart(file) OU JSON(external_url)",
            output="200/201 + MediaAssetSerializer | 400",
        )

        s = MediaAssetUploadSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        upload_file = s.validated_data.get("file")
        external_url = s.validated_data.get("external_url")
        explicit_kind = s.validated_data.get("kind")

        if external_url:
            if explicit_kind and explicit_kind != MediaAsset.EXTERNAL:
                return Response(
                    {"kind": "For external_url, kind must be 'external'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            asset, created = self._upsert_external_asset(external_url)
            return Response(
                MediaAssetSerializer(asset, context=self.get_serializer_context()).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )

        # file upload
        try:
            inferred_kind = _infer_kind_from_upload(upload_file)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        if explicit_kind and explicit_kind != inferred_kind:
            return Response(
                {"kind": f"Provided kind '{explicit_kind}' does not match inferred '{inferred_kind}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        asset, created = self._upsert_file_asset(upload_file)
        return Response(
            MediaAssetSerializer(asset, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
