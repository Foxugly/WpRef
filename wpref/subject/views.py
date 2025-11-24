# question/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import Subject
from .serializers import SubjectSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["slug", "name", "id"]

    def get_permissions(self):
        return [IsAdminUser()]

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        print("list", request.query_params)
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
