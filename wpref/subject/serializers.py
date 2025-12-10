from rest_framework import serializers
from .models import Subject

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "slug", "description"]


class SubjectDetailSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ["id", "name", "description", "questions"]

    def get_questions(self, obj):
        # import ici pour éviter l'import circulaire
        from question.serializers import QuestionLiteSerializer

        qs = obj.question_set.all()  # ou obj.questions.all() selon ton related_name
        return QuestionLiteSerializer(qs, many=True).data