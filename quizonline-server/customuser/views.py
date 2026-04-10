import logging

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from quiz.models import Quiz
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from config.tools import ErrorDetailSerializer

from .permissions import IsSelf, IsSelfOrStaffOrSuperuser, IsSuperuserOnly
from .services import (
    change_password,
    confirm_email,
    confirm_password_reset,
    register_user,
    request_password_reset,
)
from .serializers import (
    CustomUserAdminUpdateSerializer,
    CustomUserCreateSerializer,
    CustomUserProfileUpdateSerializer,
    CustomUserReadSerializer,
    EmailConfirmationSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetOKSerializer,
    PasswordResetRequestSerializer,
    QuizSimpleSerializer,
    SetCurrentDomainSerializer,
)
from .throttling import PasswordResetRateThrottle
from .throttling import PasswordResetConfirmRateThrottle, EmailConfirmRateThrottle

logger = logging.getLogger(__name__)
User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        tags=["User"],
        summary="Lister les utilisateurs",
        description="Admin/staff uniquement.",
        responses={
            200: CustomUserReadSerializer(many=True),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden (admin only)"),
        },
    ),
    create=extend_schema(
        tags=["User"],
        summary="Créer un utilisateur",
        description="Création ouverte (AllowAny).",
        request=CustomUserCreateSerializer,
        responses={
            201: CustomUserReadSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
    ),
    retrieve=extend_schema(
        tags=["User"],
        summary="Récupérer un utilisateur",
        responses={
            200: CustomUserReadSerializer,
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
        },
    ),
    update=extend_schema(
        tags=["User"],
        summary="Mettre à jour un utilisateur (PUT)",
        request=CustomUserAdminUpdateSerializer,
        responses={200: CustomUserReadSerializer},
    ),
    partial_update=extend_schema(
        tags=["User"],
        summary="Mettre à jour un utilisateur (PATCH)",
        request=CustomUserAdminUpdateSerializer,
        responses={200: CustomUserReadSerializer},
    ),
    me=extend_schema(
        tags=["User"],
        summary="Récupérer et mettre à jour mon profil",
        description="Retourne le profil de l'utilisateur authentifié.",
        request=CustomUserProfileUpdateSerializer,
        responses={
            200: CustomUserReadSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Validation error"),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden"),
        },
    ),
    set_current_domain=extend_schema(
        tags=["User"],
        summary="Définir mon domaine courant",
        description="Met à jour `current_domain` sur l'utilisateur authentifié, puis renvoie le profil mis à jour.",
        request=SetCurrentDomainSerializer,
        responses={
            200: CustomUserReadSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden"),
        },
    ),
)
class CustomUserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "pk"
    lookup_url_kwarg = "user_id"
    queryset = User.objects.none()
    lookup_value_regex = r"\d+"

    @staticmethod
    def _user_queryset():
        return (
            User.objects
            .select_related("current_domain")
            .prefetch_related("owned_domains", "linked_domains", "managed_domains")
            .order_by("id")
        )

    def get_queryset(self):
        return self._user_queryset()

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.action == "list":
            return [IsAdminUser()]
        if self.action == "destroy":
            return [IsAuthenticated(), IsSuperuserOnly()]
        if self.action in ("me", "set_current_domain"):
            return [IsSelf()]
        return [IsSelfOrStaffOrSuperuser()]

    def perform_create(self, serializer):
        register_user(serializer)

    def get_serializer_class(self):
        if self.action == "create":
            return CustomUserCreateSerializer
        if self.action in ["update", "partial_update"]:
            if self.request.user.is_staff or self.request.user.is_superuser:
                return CustomUserAdminUpdateSerializer
            return CustomUserProfileUpdateSerializer
        return CustomUserReadSerializer

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        user = self.get_queryset().get(pk=request.user.pk)
        if request.method.lower() == "get":
            serializer = CustomUserReadSerializer(user, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = CustomUserProfileUpdateSerializer(
            user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = self.get_queryset().get(pk=user.pk)
        return Response(
            CustomUserReadSerializer(user, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="me/current-domain")
    def set_current_domain(self, request):
        serializer = SetCurrentDomainSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user = self.get_queryset().get(pk=request.user.pk)
        out = CustomUserReadSerializer(user, context={"request": request})
        return Response(out.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=["User"],
        summary="Lister les quizzes d’un utilisateur",
        description=(
            "Retourne la liste des quiz liés à un utilisateur.\n"
            "Accès: soi-même ou staff/superuser."
        ),
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID utilisateur.",
            )
        ],
        responses={
            200: QuizSimpleSerializer(many=True),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Forbidden"),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Not found"),
        },
    ),
)
class UserQuizListView(GenericAPIView):
    permission_classes = [IsSelfOrStaffOrSuperuser]
    serializer_class = QuizSimpleSerializer
    queryset = User.objects.none()
    lookup_field = "pk"
    lookup_url_kwarg = "user_id"

    @extend_schema(
        operation_id="user_quiz_list",
        description="Liste les quiz liés à un utilisateur donné.",
        responses={200: QuizSimpleSerializer(many=True)},
    )
    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)

        if not request.user.is_staff and request.user != user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Vous ne pouvez voir que vos propres quiz.")

        quiz = Quiz.objects.filter(user=user).select_related("quiz_template").order_by("-created_at")

        serializer = QuizSimpleSerializer(quiz, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Demander un reset de mot de passe",
        description=(
            "Envoie un email avec un lien de réinitialisation.\n"
            "Répond toujours 200 pour ne pas révéler si l'email existe."
        ),
        request=PasswordResetRequestSerializer,
        responses={
            200: PasswordResetOKSerializer,
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Validation error"),
        },
    ),
)
class PasswordResetRequestView(GenericAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        request_password_reset(email, request)

        return Response(
            {"detail": "Si un compte existe avec cet email, un lien de réinitialisation a été envoyé."},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Confirmer un reset de mot de passe",
        request=PasswordResetConfirmSerializer,
        responses={
            200: PasswordResetOKSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Lien invalide / token invalide"),
        },
    ),
)
class PasswordResetConfirmView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer
    throttle_classes = [PasswordResetConfirmRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password1"]

        user = confirm_password_reset(uid, token, new_password)
        if not user:
            return Response({"detail": "Lien invalide."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"detail": "Mot de passe mis à jour avec succès."},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Changer son mot de passe",
        description="Utilisateur authentifié uniquement.",
        request=PasswordChangeSerializer,
        responses={
            200: PasswordResetOKSerializer,
            400: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Ancien mot de passe incorrect / validation",
            ),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
        },
    ),
)
class PasswordChangeView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        user = request.user

        if not change_password(user, old_password, new_password):
            return Response({"detail": "Ancien mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"detail": "Mot de passe modifié avec succès."},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Confirmer une adresse email",
        request=EmailConfirmationSerializer,
        responses={
            200: PasswordResetOKSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Lien invalide / token invalide"),
        },
    ),
)
class EmailConfirmView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmailConfirmationSerializer
    throttle_classes = [EmailConfirmRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]

        user = confirm_email(uid, token)
        if not user:
            return Response({"detail": "Lien invalide."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"detail": "Adresse email confirmée avec succès."},
            status=status.HTTP_200_OK,
        )
