import logging

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from wpref.tools import MyModelViewSet, ErrorDetailSerializer

from .models import Subject
from .serializers import SubjectReadSerializer, SubjectWriteSerializer, SubjectDetailSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=["Subject"],
        summary="Lister les sujets",
        description=(
                "Liste paginée des sujets.\n\n"
                "Supporte :\n"
                "- `search` (filtre name__icontains)\n"
                "- `active`, `domain` via DjangoFilterBackend\n"
        ),
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Recherche simple (name__icontains).",
            ),
        ],
        responses={
            200: SubjectReadSerializer(many=True),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden"),
        },
    ),
    retrieve=extend_schema(
        tags=["Subject"],
        summary="Récupérer un sujet",
        parameters=[
            OpenApiParameter(
                name="subject_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID du sujet.",
            )
        ],
        responses={
            200: SubjectReadSerializer,
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
        },
    ),
    details=extend_schema(
        tags=["Subject"],
        summary="Récupérer un sujet avec détails",
        parameters=[
            OpenApiParameter(
                name="subject_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID du sujet.",
            )
        ],
        responses={
            200: SubjectDetailSerializer,
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
        },
    ),
    create=extend_schema(
        tags=["Subject"],
        summary="Créer un sujet",
        request=SubjectWriteSerializer,
        responses={
            201: SubjectReadSerializer,
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Validation error"),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    update=extend_schema(
        tags=["Subject"],
        summary="Mettre à jour un sujet (PUT)",
        parameters=[
            OpenApiParameter(
                name="subject_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID du sujet.",
            )
        ],
        request=SubjectWriteSerializer,
        responses={
            200: SubjectReadSerializer,
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Validation error"),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
        },
    ),
    partial_update=extend_schema(
        tags=["Subject"],
        summary="Mettre à jour un sujet (PATCH)",
        parameters=[
            OpenApiParameter(
                name="subject_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID du sujet.",
            )
        ],
        request=SubjectWriteSerializer,
        responses={
            200: SubjectReadSerializer,
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Validation error"),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
        },
    ),
    destroy=extend_schema(
        tags=["Subject"],
        summary="Supprimer un sujet",
        parameters=[
            OpenApiParameter(
                name="subject_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID du sujet.",
            )
        ],
        responses={
            204: OpenApiResponse(description="No Content"),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
        },
    ),
)
class SubjectViewSet(MyModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectReadSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["active", "domain"]
    lookup_field = "pk"
    lookup_url_kwarg = "subject_id"

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return SubjectReadSerializer
        elif self.action in ["details"]:
            return SubjectDetailSerializer
        return SubjectWriteSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "details"]:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    # ==========================================================
    # Queryset optimisations (optionnel mais conseillé)
    # ==========================================================

    def get_queryset(self):
        qs = Subject.objects.all().select_related("domain")

        if self.action in ["retrieve", "details"]:
            qs = qs.prefetch_related(
                "domain__translations",  # parler translations du Domain (pour domain_name)
                "questions",  # M2M via related_name="questions"
                "questions__translations",  # parler translations de Question (pour title)
            )
            # optionnel (si tu veux éviter N+1 si ailleurs tu enrichis):
            # qs = qs.prefetch_related("questions__answer_options", "questions__media")

        return qs

    # ==========================================================
    # CRUD implicite : surcharges
    # ==========================================================

    def list(self, request, *args, **kwargs):
        self._log_call(
            method_name="list",
            endpoint="GET /api/subject/",
            input_expected="query params (search?, active?, domain?), body vide",
            output="200 + [SubjectSerializer] (paginé si pagination activée)",
        )
        qs = self.filter_queryset(self.get_queryset())
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(translations__name__icontains=search).distinct()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        self._log_call(
            method_name="retrieve",
            endpoint="GET /api/subject/{subject_id}/",
            input_expected="path subject_id, body vide",
            output="200 + SubjectReadSerializer | 404",
        )
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=["get"], url_path="details")
    def details(self, request, *args, **kwargs):
        self._log_call(
            method_name="details",
            endpoint="GET /api/subject/{subject_id}/details/",
            input_expected="path subject_id, body vide",
            output="200 + SubjectDetailSerializer | 404",
        )
        instance = self.get_object()
        serializer = self.get_serializer(instance, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        self._log_call(
            method_name="create",
            endpoint="POST /api/subject/",
            input_expected="body JSON: SubjectSerializer (write fields)",
            output="201 + SubjectWriteSerializer | 400",
        )
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        instance = write_serializer.save()
        read_serializer = SubjectReadSerializer(instance, context=self.get_serializer_context())
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        self._log_call(
            method_name="update",
            endpoint="PUT /api/subject/{subject_id}/",
            input_expected="path subject_id + body JSON complet (SubjectWriteSerializer)",
            output="200 + SubjectReadSerializer | 400 | 404",
        )
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        write_serializer = self.get_serializer(instance, data=request.data, partial=partial)
        write_serializer.is_valid(raise_exception=True)
        self.perform_update(write_serializer)

        instance.refresh_from_db()
        data = SubjectReadSerializer(instance, context=self.get_serializer_context(), ).data
        return Response(data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        self._log_call(
            method_name="partial_update",
            endpoint="PATCH /api/subject/{subject_id}/",
            input_expected="path subject_id + body JSON partiel (SubjectSerializer)",
            output="200 + SubjectReadSerializer | 400 | 404",
        )
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._log_call(
            method_name="destroy",
            endpoint="DELETE /api/subject/{subject_id}/",
            input_expected="path subject_id, body vide",
            output="204 | 404",
        )
        return super().destroy(request, *args, **kwargs)
