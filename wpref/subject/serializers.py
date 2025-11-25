from rest_framework import serializers

from .models import Subject
from question.serializers import QuestionLiteSerializer

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "slug", "description"]

class SubjectDetailSerializer(serializers.ModelSerializer):
    questions = QuestionLiteSerializer(many=True, read_only=True)

    class Meta:
        model = Subject
        fields = ["id", "name", "description", "questions"]