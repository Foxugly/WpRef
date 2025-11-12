# question/views.py
from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Subject, Question
from .serializers import SubjectSerializer, QuestionSerializer

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["slug", "name", "id"]

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.prefetch_related("media", "answer_options", "subjects")
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    # ?subjects=1  | ?subjects__in=1,2 | ?subjects__slug=reglement | ?subjects__slug__in=a,b
    filterset_fields = {
        "subjects": ["exact", "in"],
        "subjects__slug": ["exact", "in"],
        "allow_multiple_correct": ["exact"],
    }
