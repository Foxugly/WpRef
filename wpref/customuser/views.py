# customuser/api/views.py

from django.shortcuts import get_object_or_404
from quiz.models import Quiz
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response

from .models import CustomUser
from .permissions import IsSelfOrStaffOrSuperuser
from .serializers import CustomUserSerializer, QuizSimpleSerializer


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
