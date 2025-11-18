# question/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .models import Question
from .serializers import QuestionSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.prefetch_related("media", "answer_options", "subjects")
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    # ?subjects=1  | ?subjects__in=1,2 | ?subjects__slug=reglement | ?subjects__slug__in=a,b
    filterset_fields = {
        "subjects": ["exact", "in"],
        "subjects__slug": ["exact", "in"],
        "allow_multiple_correct": ["exact"],
    }
    def get_permissions(self):
        """
        - Non authentifié : rien (401)
        - Utilisateur authentifié non admin : rien (403)
        - Admin/staff : tous les droits (CRUD)
        """
        return [IsAdminUser()]
