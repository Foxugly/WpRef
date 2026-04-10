from django.db import transaction
from django.db.models import Count, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from config.tools import MyModelViewSet

from .models import Domain
from .permissions import IsDomainOwnerOrManager
from .serializers import (
    DomainReadSerializer,
    DomainWriteSerializer,
    DomainPartialSerializer,
    DomainDetailSerializer,
    DomainMemberRoleSerializer,
)
from config.tools import ErrorDetailSerializer
from django.contrib.auth import get_user_model


@extend_schema_view(
    list=extend_schema(
        tags=["Domain"],
        summary="Lister les domaines accessibles",
        description=(
                "Retourne la liste des domaines visibles par l'utilisateur courant.\n\n"
                "- **Superuser / staff global** : voit tous les domaines\n"
                "- **Utilisateur normal** : voit uniquement les domaines dont il est `owner` ou membre de `staff`"
        ),
        responses={status.HTTP_200_OK: DomainReadSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Domain"],
        summary="Récupérer un domaine",
        description=(
                "Retourne un domaine (par `domain_id`).\n\n"
                "⚠️ Si l'utilisateur n'a pas accès au domaine, l'API renvoie généralement **404** "
                "(car `get_queryset()` ne retourne pas l'objet)."
        ),
        parameters=[
            OpenApiParameter(
                name="domain_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Identifiant du domaine (correspond à `<int:domain_id>` dans l'URL).",
            ),
        ],
        responses={
            status.HTTP_200_OK: DomainReadSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description="Not found (domain non visible ou inexistant)."),
        },
    ),
    details=extend_schema(
        tags=["Domain"],
        summary="Récupérer un domaine avec détails",
        parameters=[
            OpenApiParameter(
                name="domain_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID du domaine.",
            )
        ],
        responses={
            200: DomainDetailSerializer,
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
        },
    ),
    create=extend_schema(
        tags=["Domain"],
        summary="Créer un domaine",
        description=(
                "Crée un nouveau domaine.\n\n"
                "- `owner` est forcé au user courant (même si fourni dans le payload).\n"
                "- Le user courant est ajouté à `staff` automatiquement.\n"
                "- `allowed_languages` doit être un sous-ensemble de `settings.LANGUAGES`."
        ),
        request=DomainWriteSerializer,
        responses={
            status.HTTP_201_CREATED: DomainReadSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(description="Validation error."),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description="Authentication required."),
        },
    ),
    update=extend_schema(
        tags=["Domain"],
        summary="Mettre à jour un domaine",
        description=(
                "Met à jour un domaine (PUT).\n\n"
                "- Réservé à : superuser / staff global / owner / staff du domaine.\n"
                "- `owner` est **read-only** (ne peut pas être modifié via l'API)."
        ),
        request=DomainWriteSerializer,
        parameters=[
            OpenApiParameter(
                name="domain_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Identifiant du domaine (correspond à `<int:domain_id>` dans l'URL).",
            ),
        ],
        responses={
            status.HTTP_200_OK: DomainReadSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(description="Validation error."),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description="Authentication required."),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(description="Forbidden."),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description="Not found (domain non visible ou inexistant)."),
        },
    ),
    partial_update=extend_schema(
        tags=["Domain"],
        summary="Modifier partiellement un domaine",
        description=(
                "Met à jour partiellement un domaine (PATCH).\n\n"
                "- Réservé à : superuser / staff global / owner / staff du domaine.\n"
                "- `owner` est **read-only** (ne peut pas être modifié via l'API)."
        ),
        request=DomainPartialSerializer,
        parameters=[
            OpenApiParameter(
                name="domain_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Identifiant du domaine (correspond à `<int:domain_id>` dans l'URL).",
            ),
        ],
        responses={
            status.HTTP_200_OK: DomainReadSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(description="Validation error."),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description="Authentication required."),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(description="Forbidden."),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description="Not found (domain non visible ou inexistant)."),
        },
    ),
    destroy=extend_schema(
        tags=["Domain"],
        summary="Supprimer un domaine",
        description=(
                "Supprime un domaine.\n\n"
                "- Réservé à : superuser / staff global / owner / staff du domaine.\n"
                "⚠️ La suppression peut échouer si le domaine est référencé ailleurs (FK en PROTECT côté modèles liés)."
        ),
        parameters=[
            OpenApiParameter(
                name="domain_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Identifiant du domaine (correspond à `<int:domain_id>` dans l'URL).",
            ),
        ],
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(description="Deleted."),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description="Authentication required."),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(description="Forbidden."),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description="Not found (domain non visible ou inexistant)."),
        },
    ),
)
class DomainViewSet(MyModelViewSet):
    ordering = ["id"]
    lookup_field = "pk"
    lookup_url_kwarg = "domain_id"

    def get_permissions(self):
        if self.action in ["list", "retrieve", "details"]:
            return [AllowAny()]
        if self.action == "available_for_linking":
            return [AllowAny()]
        return [IsAuthenticated(), IsDomainOwnerOrManager()]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return DomainReadSerializer
        elif self.action == "details":
            return DomainDetailSerializer
        elif self.action == "partial_update":
            return DomainPartialSerializer
        return DomainWriteSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Domain.objects.none()

        qs = (
            Domain.objects.all()
            .annotate(
                subjects_count=Count("subjects", filter=Q(subjects__active=True), distinct=True),
                questions_count=Count("questions", filter=Q(questions__active=True), distinct=True),
            )
            .select_related("owner")
            .prefetch_related("managers", "members", "allowed_languages", "translations")
            .order_by("id")
        )
        user = self.request.user
        if not user or user.is_anonymous:
            return qs.filter(active=True)
        if user.is_superuser:
            return qs
        return qs.filter(Q(owner=user) | Q(managers=user) | Q(members=user)).distinct()

    def perform_create(self, serializer):
        domain = serializer.save(created_by=self.request.user, updated_by=self.request.user)
        if self.request.user and not self.request.user.is_anonymous:
            domain.managers.add(self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def create(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        self.perform_create(write_serializer)
        instance = write_serializer.instance

        read_data = DomainReadSerializer(instance, context=self.get_serializer_context()).data
        headers = self.get_success_headers({"id": instance.pk})
        return Response(read_data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        write_serializer = self.get_serializer(instance, data=request.data, partial=partial)
        write_serializer.is_valid(raise_exception=True)
        self.perform_update(write_serializer)
        instance.refresh_from_db()

        read_data = DomainReadSerializer(instance, context=self.get_serializer_context()).data
        return Response(read_data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=["get"], url_path="details")
    def details(self, request, *args, **kwargs):
        self._log_call(
            method_name="details",
            endpoint="GET /api/domain/{domain_id}/details/",
            input_expected="path domain_id, body vide",
            output="200 + DomainDetailSerializer | 404",
        )
        instance = self.get_object()
        serializer = self.get_serializer(instance, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="available-for-linking")
    def available_for_linking(self, request, *args, **kwargs):
        queryset = (
            Domain.objects.filter(active=True)
            .select_related("owner")
            .prefetch_related("managers", "members", "allowed_languages", "translations")
            .order_by("id")
        )
        serializer = DomainReadSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="member-role")
    def member_role(self, request, *args, **kwargs):
        domain = self.get_object()
        serializer = DomainMemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_model = get_user_model()
        target = user_model.objects.filter(pk=serializer.validated_data["user_id"]).first()
        if not target:
            raise ValidationError({"user_id": "User not found."})

        if not domain.members.filter(pk=target.pk).exists() and domain.owner_id != target.pk:
            raise ValidationError({"user_id": "User must be linked to this domain first."})

        update_fields: list[str] = []

        with transaction.atomic():
            if "is_active" in serializer.validated_data:
                target.is_active = serializer.validated_data["is_active"]
                update_fields.append("is_active")

            if "is_domain_manager" in serializer.validated_data:
                make_manager = serializer.validated_data["is_domain_manager"]
                if make_manager:
                    domain.managers.add(target)
                    domain.members.add(target)
                    if request.user.is_superuser and not target.is_staff:
                        target.is_staff = True
                        update_fields.append("is_staff")
                else:
                    domain.managers.remove(target)
                    if (
                        request.user.is_superuser
                        and target.is_staff
                        and not target.is_superuser
                        and not target.managed_domains.exclude(pk=domain.pk).exists()
                    ):
                        target.is_staff = False
                        update_fields.append("is_staff")

            if update_fields:
                target.save(update_fields=update_fields)

        if "is_domain_manager" in serializer.validated_data:
            is_domain_manager = serializer.validated_data["is_domain_manager"]
        else:
            is_domain_manager = domain.managers.filter(pk=target.pk).exists()
        return Response(
            {
                "id": target.id,
                "username": target.username,
                "is_active": target.is_active,
                "is_staff": target.is_staff,
                "is_domain_manager": is_domain_manager,
            },
            status=status.HTTP_200_OK,
        )

