from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
)
from rest_framework import filters
from rest_framework.permissions import IsAdminUser
from wpref.tools import ErrorDetailSerializer, MyModelViewSet

from .models import Language
from .serializers import LanguageReadSerializer, LanguageWriteSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Language"],
        summary="Lister les langues",
        description=(
                "Liste paginée des langues.\n\n"
                "Supporte :\n"
                "- `search` (DRF SearchFilter sur `code`, `name`)\n"
                "- `ordering` (DRF OrderingFilter sur `code`, `name`, `id`)\n"
        ),
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Recherche simple sur code/name.",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Tri (ex: "code", "-name", "id").',
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Numéro de page (si pagination activée).",
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Taille de page (si PageNumberPagination configurée).",
            ),
        ],
        responses={
            200: LanguageReadSerializer(many=True),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    retrieve=extend_schema(
        tags=["Language"],
        summary="Récupérer une langue",
        parameters=[
            OpenApiParameter(
                name="lang_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID de la langue.",
            )
        ],
        responses={
            200: LanguageReadSerializer,
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    create=extend_schema(
        tags=["Language"],
        summary="Créer une langue",
        request=LanguageWriteSerializer,
        responses={
            201: LanguageReadSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    update=extend_schema(
        tags=["Language"],
        summary="Mettre à jour une langue (PUT)",
        parameters=[
            OpenApiParameter(
                name="lang_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID de la langue.",
            )
        ],
        request=LanguageWriteSerializer,
        responses={
            200: LanguageReadSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    partial_update=extend_schema(
        tags=["Language"],
        summary="Mettre à jour une langue (PATCH)",
        parameters=[
            OpenApiParameter(
                name="lang_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID de la langue.",
            )
        ],
        request=LanguageWriteSerializer,
        responses={
            200: LanguageReadSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    destroy=extend_schema(
        tags=["Language"],
        summary="Supprimer une langue",
        parameters=[
            OpenApiParameter(
                name="lang_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID de la langue.",
            )
        ],
        responses={
            204: OpenApiResponse(description="No Content"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
)
class LanguageViewSet(MyModelViewSet):
    queryset = Language.objects.all().order_by("code")
    permission_classes = [IsAdminUser]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["code", "name"]
    ordering_fields = ["code", "name", "id"]
    ordering = ["code"]
    lookup_field = "pk"
    lookup_url_kwarg = "lang_id"

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return LanguageReadSerializer
        return LanguageWriteSerializer
