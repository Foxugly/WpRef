import logging

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from wpref.tools import MyModelViewSet, ErrorDetailSerializer

from .models import Subject
from .serializers import SubjectReadSerializer, SubjectWriteSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=["Subject"],
        summary="Lister les sujets",
        description=(
                "Liste paginée des sujets.\n\n"
                "Supporte :\n"
                "- `search` (filtre name__icontains)\n"
                "- `name`, `subject_id` via DjangoFilterBackend\n"
        ),
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Recherche simple (name__icontains).",
            ),
            OpenApiParameter(
                name="name",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtre exact (via DjangoFilterBackend).",
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
    filterset_fields = []
    lookup_field = "pk"
    lookup_url_kwarg = "subject_id"

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return SubjectReadSerializer
        return SubjectWriteSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    # ==========================================================
    # Queryset optimisations (optionnel mais conseillé)
    # ==========================================================

    def get_queryset(self):
        """
        Optimisation:
        - Si retrieve => on précharge les relations utiles au detail serializer
        - Sinon => queryset simple
        """
        qs = Subject.objects.all()

        if self.action == "retrieve":
            # ⚠️ adapte les prefetch/select_related en fonction de tes relations réelles
            # Exemple si Subject -> questions (m2m ou reverse FK) et Question -> answer_options/media
            qs = qs.prefetch_related(
                "questions",
                "questions__answer_options",
                "questions__media",
            )
        return qs

    # ==========================================================
    # CRUD implicite : surcharges
    # ==========================================================

    def list(self, request, *args, **kwargs):
        self._log_call(
            method_name="list",
            endpoint="GET /api/subject/",
            input_expected="query params (search?, name?), body vide",
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
            input_expected="path pk, body vide",
            output="200 + SubjectDetailSerializer | 404",
        )
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        self._log_call(
            method_name="create",
            endpoint="POST /api/subject/",
            input_expected="body JSON: SubjectSerializer (write fields)",
            output="201 + SubjectSerializer | 400",
        )
        response = super().create(request, *args, **kwargs)
        instance = Subject.objects.get(pk=response.data["id"])
        response.data = SubjectReadSerializer(instance, context=self.get_serializer_context(),).data
        return response

    def update(self, request, *args, **kwargs):
        self._log_call(
            method_name="update",
            endpoint="PUT /api/subject/{subject_id}/",
            input_expected="path subject_id + body JSON complet (SubjectSerializer)",
            output="200 + SubjectSerializer | 400 | 404",
        )
        response = super().update(request, *args, **kwargs)
        instance = Subject.objects.get(pk=response.data["id"])
        response.data = SubjectReadSerializer(instance, context=self.get_serializer_context(), ).data
        return response


    def partial_update(self, request, *args, **kwargs):
        self._log_call(
            method_name="partial_update",
            endpoint="PATCH /api/subject/{subject_id}/",
            input_expected="path subject_id + body JSON partiel (SubjectSerializer)",
            output="200 + SubjectSerializer | 400 | 404",
        )
        response =  super().partial_update(request, *args, **kwargs)
        instance = Subject.objects.get(pk=response.data["id"])
        response.data = SubjectReadSerializer(instance, context=self.get_serializer_context(), ).data
        return response

    def destroy(self, request, *args, **kwargs):
        self._log_call(
            method_name="destroy",
            endpoint="DELETE /api/subject/{subject_id}/",
            input_expected="path subject_id, body vide",
            output="204 | 404",
        )
        return super().destroy(request, *args, **kwargs)
