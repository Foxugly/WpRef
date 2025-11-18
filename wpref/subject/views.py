# question/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated, IsAdminUser, SAFE_METHODS

from .models import Subject
from .serializers import SubjectSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["slug", "name", "id"]

    def get_permissions(self):
        """
        - Non authentifié : rien (401)
        - Utilisateur authentifié non admin : seulement GET (liste + detail)
        - Admin/staff : tous les droits (CRUD)
        """
        if self.request.method in SAFE_METHODS:
            # GET, HEAD, OPTIONS → user doit être authentifié
            return [IsAuthenticated()]
        # POST, PUT, PATCH, DELETE → admin/staff only
        return [IsAdminUser()]
