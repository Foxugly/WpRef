from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated

from .models import Domain
from .permissions import IsDomainOwnerOrStaff
from .serializers import DomainSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Domain"],
        summary="Lister les domaines accessibles",
        description=(
                "Retourne la liste des domaines visibles par l'utilisateur courant.\n\n"
                "- **Superuser / staff global** : voit tous les domaines\n"
                "- **Utilisateur normal** : voit uniquement les domaines dont il est `owner` ou membre de `staff`"
        ),
        responses={status.HTTP_200_OK: DomainSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Domain"],
        summary="Récupérer un domaine",
        description=(
                "Retourne un domaine (par `id`).\n\n"
                "⚠️ Si l'utilisateur n'a pas accès au domaine, l'API renvoie généralement **404** "
                "(car `get_queryset()` ne retourne pas l'objet)."
        ),
        parameters=[
            OpenApiParameter(
                name="domain_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Identifiant du domaine (correspond à `<int:pk>` dans l'URL).",
            ),
        ],
        responses={
            status.HTTP_200_OK: DomainSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description="Not found (domain non visible ou inexistant)."),
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
        request=DomainSerializer,
        responses={
            status.HTTP_201_CREATED: DomainSerializer,
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
        request=DomainSerializer,
        parameters=[
            OpenApiParameter(
                name="domain_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Identifiant du domaine (correspond à `<int:pk>` dans l'URL).",
            ),
        ],
        responses={
            status.HTTP_200_OK: DomainSerializer,
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
        request=DomainSerializer,
        parameters=[
            OpenApiParameter(
                name="domain_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Identifiant du domaine (correspond à `<int:pk>` dans l'URL).",
            ),
        ],
        responses={
            status.HTTP_200_OK: DomainSerializer,
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
                description="Identifiant du domaine (correspond à `<int:pk>` dans l'URL).",
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
class DomainViewSet(viewsets.ModelViewSet):
    serializer_class = DomainSerializer
    permission_classes = [IsAuthenticated, IsDomainOwnerOrStaff]
    lookup_field = "pk"
    lookup_url_kwarg = "domain_id"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Domain.objects.none()
        qs = Domain.objects.all().select_related("owner").prefetch_related("staff")

        user = self.request.user
        if user.is_superuser or user.is_staff:
            return qs

        # user normal : ne voit que ce qu'il possède ou gère
        return qs.filter(Q(owner=user) | Q(staff=user)).distinct()

    def perform_create(self, serializer):
        # owner = user courant
        domain = serializer.save(owner=self.request.user)

        # Optionnel mais souvent pratique : le owner fait partie du staff.
        # (tu peux le retirer si tu veux vraiment séparer owner vs staff)
        domain.staff.add(self.request.user)
