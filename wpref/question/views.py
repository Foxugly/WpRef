import json
import logging

from django.http import QueryDict
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes, OpenApiRequest,
)
from rest_framework import status
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from wpref.tools import ErrorDetailSerializer
from wpref.tools import MyModelViewSet

from .models import Question, QuestionMedia
from .serializers import QuestionReadSerializer, QuestionWriteSerializer, QuestionMultipartWriteSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=["Question"],
        summary="Lister les questions",
        description=(
                "Liste paginée des questions.\n\n"
                "Supporte :\n"
                "- `search` (filtre title__icontains)\n"
                "- `title`, `description` via DjangoFilterBackend (si activé)\n"
        ),
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Recherche simple (title__icontains).",
            ),
            OpenApiParameter(
                name="title",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtre exact (via DjangoFilterBackend).",
            ),
            OpenApiParameter(
                name="description",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtre exact (via DjangoFilterBackend).",
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
                "Crée une question. Supporte multipart/form-data (recommandé pour upload médias) ou JSON.\n\n"
                "**Convention**:\n"
                "- `subject_ids`: envoyé comme liste multipart (subject_ids=1&subject_ids=2)\n"
                "- `answer_options`: JSON string (liste)\n"
                "- `media`: JSON string (liste) pour les external_url\n"
                "- fichiers : `media[0][file]`, `media[1][file]`, ...\n"
        ),
        request=QuestionMultipartWriteSerializer,
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
                "Mise à jour complète. Même payload que create.\n"
                "Supporte multipart/form-data ou JSON."
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
        request=QuestionMultipartWriteSerializer,
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
                "Mise à jour partielle. Même payload que create.\n"
                "Supporte multipart/form-data ou JSON."
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
        request=QuestionMultipartWriteSerializer,
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
)
class QuestionViewSet(MyModelViewSet):
    queryset = (
        Question.objects
        .all()
        .select_related("domain")
        .prefetch_related("subjects", "translations", "answer_options__translations")
    )
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = []
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = "pk"
    lookup_url_kwarg = "question_id"

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
        """
        Transforme request.data (QueryDict) en dict normal pour le serializer,
        en gérant correctement :
        - subject_ids     -> liste d'int
        - answer_options  -> liste de dicts (parse JSON)
        - media           -> liste de dicts (parse JSON) si envoyé en JSON
        """

        # 1) On sort de la QueryDict -> dict Python classique
        if isinstance(data, QueryDict):
            mutable = {}
            for key in data.keys():
                if key == "subject_ids":
                    mutable["subject_ids"] = [int(v) for v in data.getlist("subject_ids") if v.strip()]
                else:
                    mutable[key] = data.get(key)
        else:
            mutable = dict(data)

        raw_trans = mutable.get("translations")
        if isinstance(raw_trans, str):
            try:
                parsed_trans = json.loads(raw_trans)
                if isinstance(parsed_trans, dict):
                    mutable["translations"] = parsed_trans
            except json.JSONDecodeError:
                pass

        raw_answer_options = mutable.get("answer_options")
        if isinstance(raw_answer_options, str):
            try:
                parsed = json.loads(raw_answer_options)
                if isinstance(parsed, list):
                    mutable["answer_options"] = parsed
            except json.JSONDecodeError:
                pass

        raw_media = mutable.get("media")
        if isinstance(raw_media, str):
            try:
                parsed_media = json.loads(raw_media)
                if isinstance(parsed_media, list):
                    mutable["media"] = parsed_media
            except json.JSONDecodeError:
                pass
        return mutable

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
        qs = self.get_queryset()
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

    @extend_schema(
        request=OpenApiRequest(
            request=QuestionMultipartWriteSerializer,
            encoding={"media_files": {"style": "form", "explode": True}},
        )
    )
    def create(self, request, *args, **kwargs):
        self._log_call(
            method_name="create",
            endpoint="POST /api/question/",
            input_expected="multipart/JSON (Question + subject_ids + answer_options + media)",
            output="201 + QuestionSerializer | 400",
        )
        data = self._coerce_json_fields(request.data)
        media_data = data.get("media", [])
        serializer = self.get_serializer(data=data, context=self.get_serializer_context())
        if not serializer.is_valid():
            logger.warning("CREATE errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        question = serializer.save()
        self._handle_media_upload(request, question, media_data=media_data)
        logger.info("Question created id=%s", question.id)
        return Response(QuestionReadSerializer(question, context=self.get_serializer_context()).data,
                        status=status.HTTP_201_CREATED)

    @extend_schema(
        request=OpenApiRequest(
            request=QuestionMultipartWriteSerializer,
            encoding={"media_files": {"style": "form", "explode": True}},
        )
    )
    def update(self, request, *args, **kwargs):
        self._log_call(
            method_name="update",
            endpoint="PUT /api/question/{id}/",
            input_expected="path pk + body multipart/JSON complet",
            output="200 + QuestionSerializer | 400 | 404",
        )
        return self._update_internal(request, partial=False)

    @extend_schema(
        request=OpenApiRequest(
            request=QuestionMultipartWriteSerializer,
            encoding={"media_files": {"style": "form", "explode": True}},
        )
    )
    def partial_update(self, request, *args, **kwargs):
        self._log_call(
            method_name="partial_update",
            endpoint="PATCH /api/question/{queston_id}/",
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
        media_data = data.get("media", [])

        serializer = QuestionWriteSerializer(instance, data=data, partial=partial,
                                             context=self.get_serializer_context())
        if not serializer.is_valid():
            logger.warning("UPDATE errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.save()
        if (not partial) or ("media" in data) or request.FILES:
            self._handle_media_upload(request, question, media_data=media_data)

        logger.info("Question updated id=%s partial=%s", question.id, partial)
        return Response(QuestionReadSerializer(question, context=self.get_serializer_context()).data,
                        status=status.HTTP_200_OK)

    # ==========================================================
    # Ton code : gestion media
    # ==========================================================

    # ---------------------------
    # Gestion des médias
    # ---------------------------
    def _handle_media_upload(self, request, question: Question, media_data=None) -> None:

        question.media.all().delete()
        sort_index = 1
        media_data = media_data or []
        for key in request.FILES:
            for f in request.FILES.getlist(key):
                content_type = (getattr(f, "content_type", "") or "").lower()
                if content_type.startswith("image/"):
                    kind = QuestionMedia.IMAGE
                elif content_type.startswith("video/"):
                    kind = QuestionMedia.VIDEO
                else:
                    continue

                QuestionMedia.objects.create(
                    question=question,
                    kind=kind,
                    file=f,
                    sort_order=sort_index,
                )
                sort_index += 1

        for item in media_data:
            if not isinstance(item, dict):
                continue

            if item.get("kind") == QuestionMedia.EXTERNAL and item.get("external_url"):
                QuestionMedia.objects.create(
                    question=question,
                    kind=QuestionMedia.EXTERNAL,
                    external_url=item["external_url"],
                    sort_order=item.get("sort_order", sort_index),
                )
                sort_index += 1
