# question/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions

from .models import Subject
from .serializers import SubjectSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["slug", "name", "id"]
