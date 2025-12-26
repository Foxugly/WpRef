import logging

from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
)
from quiz.models import Quiz
from rest_framework import status, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from wpref.tools import ErrorDetailSerializer

from .permissions import IsSelfOrStaffOrSuperuser
from .serializers import *
from customuser.serializers import SetCurrentDomainSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


# ---------------------------------------------------------------------
# /api/user/  (GET admin-only, POST public)
# ---------------------------------------------------------------------

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
        request=CustomUserUpdateSerializer,
        responses={200: CustomUserReadSerializer},
    ),
    partial_update=extend_schema(
        tags=["User"],
        summary="Mettre à jour un utilisateur (PATCH)",
        request=CustomUserUpdateSerializer,
        responses={200: CustomUserReadSerializer},
    ),
)
class CustomUserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = CustomUser.objects.all().order_by("id")
    lookup_value_regex = r"\d+"  # ✅ empêche 'me' d'être capturé comme pk

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.action == "list":
            return [IsAdminUser()]
        # retrieve/update/partial_update
        return [IsSelfOrStaffOrSuperuser()]

    def get_serializer_class(self):
        if self.action == "create":
            return CustomUserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return CustomUserUpdateSerializer
        if self.action in ["me", "set_current_domain"]:
            return MeSerializer
        return CustomUserReadSerializer

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        serializer = MeSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ✅ /users/me/current-domain/
    @action(detail=False, methods=["post"], url_path="me/current-domain")
    def set_current_domain(self, request):
        serializer = SetCurrentDomainSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()  # met à jour request.user.current_domain

        # renvoyer le profil à jour
        out = MeSerializer(request.user, context={"request": request})
        return Response(out.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------
# /api/users/<id>/quizzes/   (GET)
# ---------------------------------------------------------------------

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
                name="pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="ID utilisateur (pk).",
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
    queryset = CustomUser.objects.none()

    @extend_schema(
        operation_id="user_quiz_list",
        description="Liste les quiz liés à un utilisateur donné.",
        responses={200: QuizSimpleSerializer(many=True)},
    )
    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)

        # sécurité basique : un user ne voit que ses quiz, sauf si staff
        if not request.user.is_staff and request.user != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous ne pouvez voir que vos propres quiz.")

        quiz = Quiz.objects.filter(sessions__user=user).distinct()

        serializer = QuizSimpleSerializer(quiz, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------
# /api/user/password/reset/  (POST)
# ---------------------------------------------------------------------

@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Demander un reset de mot de passe",
        description=(
                "Envoie un email avec un lien de réinitialisation.\n"
                "⚠️ Répond toujours 200 pour ne pas révéler si l'email existe."
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

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        form = PasswordResetForm(data={"email": email})
        if form.is_valid():
            # domain_override : ton frontend (SPA, etc.)
            # ou tu laisses Django construire une URL backend
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                email_template_name="password_reset_email.html",
                domain_override="frontend.example.com"
            )

        # On répond toujours 200 pour ne pas révéler si l'email existe
        return Response({"detail": "Si un compte existe avec cet email, un lien de réinitialisation a été envoyé."},
                        status=status.HTTP_200_OK)


# ---------------------------------------------------------------------
# /api/user/password/reset/confirm/  (POST)
# ---------------------------------------------------------------------

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

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password1"]

        try:
            uid_int = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_int)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"detail": "Lien invalide."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Lien ou token invalide ou expiré."},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Mot de passe mis à jour avec succès."},
                        status=status.HTTP_200_OK)


# ---------------------------------------------------------------------
# /api/user/password/change/  (POST)
# ---------------------------------------------------------------------

@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Changer son mot de passe",
        description="Utilisateur authentifié uniquement.",
        request=PasswordChangeSerializer,
        responses={
            200: PasswordResetOKSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer,
                                 description="Ancien mot de passe incorrect / validation"),
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

        if not user.check_password(old_password):
            return Response({"detail": "Ancien mot de passe incorrect."},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Mot de passe modifié avec succès."},
                        status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=["User"],
        summary="Profil courant",
        responses={
            200: MeSerializer,
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
        },
    ),
    put=extend_schema(
        tags=["User"],
        summary="Mettre à jour mon profil (PUT)",
        request=MeSerializer,
        responses={
            200: MeSerializer,
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Validation error"),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
        },
    ),
    patch=extend_schema(
        tags=["User"],
        summary="Mettre à jour mon profil (PATCH)",
        request=MeSerializer,
        responses={
            200: MeSerializer,
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Validation error"),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Unauthorized"),
        },
    ),
)
class MeView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True  # ✅ accepte PUT partiel
        return super().update(request, *args, **kwargs)
