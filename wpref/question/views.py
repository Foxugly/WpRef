# question/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import Question
from .serializers import QuestionSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.prefetch_related("media", "answer_options", "subjects")
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]

    filterset_fields = ["title", "description"]

    def get_permissions(self):
        """
        - Non authentifié : rien (401)
        - Utilisateur authentifié non admin : rien (403)
        - Admin/staff : tous les droits (CRUD)
        """
        return [IsAdminUser()]

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(title__icontains=search)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
