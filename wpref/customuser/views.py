# customuser/api/views.py

from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from quiz.models import Quiz
from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveUpdateAPIView, ListCreateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response

from .permissions import IsSelfOrStaffOrSuperuser
from .serializers import *

User = get_user_model()


class CustomUserListCreateView(ListCreateAPIView):
    """
    Créer un nouvel utilisateur.
    POST /api/user/
    """
    queryset = CustomUser.objects.all().order_by("id")
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]

    def get_permissions(self):
        """
        - POST /api/user/  -> AllowAny (création ouverte)
        - GET  /api/user/  -> IsAdminUser (seulement staff/admin)
        """
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAdminUser()]


class CustomUserDetailUpdateView(RetrieveUpdateAPIView):
    """
    Récupérer / modifier un utilisateur.
    GET /api/user/<id>/
    PUT/PATCH /api/user/<id>/
    """
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsSelfOrStaffOrSuperuser]


class UserQuizListView(GenericAPIView):
    """
    Liste les quiz liés à un utilisateur donné, via ses sessions de quiz.

    GET /api/users/<id>/quizzes/
    """
    permission_classes = [IsSelfOrStaffOrSuperuser]
    serializer_class = QuizSimpleSerializer

    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)

        # sécurité basique : un user ne voit que ses quiz, sauf si staff
        if not request.user.is_staff and request.user != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous ne pouvez voir que vos propres quiz.")

        quizzes = Quiz.objects.filter(sessions__user=user).distinct()

        serializer = QuizSimpleSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PasswordResetRequestView(GenericAPIView):
    """
    POST /api/user/password/reset/
    Body: { "email": "user@example.com" }

    -> Envoie un email avec un lien de reset (frontend).
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        # On utilise le mécanisme standard Django
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


class PasswordResetConfirmView(GenericAPIView):
    """
    POST /api/user/password/reset/confirm/
    Body: { "uid": "<uid_b64>", "token": "<token>", "new_password": "xxx" }

    -> Vérifie le uid + token, puis change le mot de passe.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

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


class PasswordChangeView(GenericAPIView):
    """
    POST /api/user/password/change/
    Body: { "old_password": "xxx", "new_password": "yyy" }

    -> Utilisateur authentifié change son mot de passe.
    """
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


class MeView(RetrieveUpdateAPIView):
    """
    GET /api/user/me/  -> infos utilisateur
    PUT/PATCH /api/user/me/ -> update profil
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user
