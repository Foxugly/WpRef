# quiz/api/views.py

from django.shortcuts import get_object_or_404
from django.utils import timezone
from question.models import Question, AnswerOption
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import Quiz, QuizQuestion, QuizSession, QuizAttempt, QuizAnswer
from .serializers import (
    QuizAttemptSerializer,
    QuizSessionSerializer,
    QuizAttemptInputSerializer,
    QuizSummarySerializer,
    QuizSerializer,
    QuizQuestionInlineSerializer,
    QuizQuestionUpdateSerializer, QuizAttemptDetailSerializer
)


class QuizStartView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizSessionSerializer
    queryset = QuizSession.objects.all()

    def post(self, request, slug):
        quiz = get_object_or_404(Quiz, slug=slug)
        session = QuizSession.objects.create(
            quiz=quiz,
            user=request.user,
        )
        data = {
            "id": str(session.id),
            "quiz": session.quiz.id,
            "started_at": session.started_at,
            "is_closed": session.is_closed,
            "max_duration": session.max_duration,
            "n_questions": session.quiz.max_questions,
        }
        return Response(data, status=status.HTTP_201_CREATED)


class QuizAttemptView(GenericAPIView):
    """
    POST/GET /api/quiz/<quiz_id>/attempt/<question_order>/

    - POST : enregistre/modifie la réponse de l'utilisateur pour une question
      via selected_option_ids (MCQ).
    - GET  : renvoie la question + options + ce que l'utilisateur a coché
             (+ is_correct si mode practice ou session clôturée).

    Accès : propriétaire de la session OU admin/staff.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuizAttemptSerializer  # pour compatibilité, pas utilisé directement

    def get_session_and_quiz_question(self, quiz_id, question_order):
        session = get_object_or_404(QuizSession, pk=quiz_id)
        quiz_question = get_object_or_404(
            QuizQuestion,
            quiz=session.quiz,
            sort_order=question_order,
        )
        return session, quiz_question

    def post(self, request, quiz_id, question_order):
        session, quiz_question = self.get_session_and_quiz_question(
            quiz_id, question_order
        )

        # Règle d'accès : proprio ou admin
        if not (request.user.is_staff or session.user == request.user):
            return Response(
                {"detail": "Vous n'êtes pas autorisé à répondre à ce quiz."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Vérifie si on peut encore répondre (non clôturé et non expiré)
        if not session.can_answer():
            return Response(
                {"detail": "Ce quiz est clôturé ou a expiré."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Validation via serializer d'entrée
        input_serializer = QuizAttemptInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        selected_ids = input_serializer.validated_data["selected_option_ids"]

        # 1) on crée / met à jour QuizAttempt
        attempt, _ = QuizAttempt.objects.update_or_create(
            session=session,
            question_order=question_order,
            defaults={
                "question": quiz_question.question,
            },
        )

        # 2) on crée / met à jour QuizAnswer
        quiz_answer, _ = QuizAnswer.objects.get_or_create(
            attempt=attempt,
            question=quiz_question.question,
        )

        options_qs = AnswerOption.objects.filter(
            question=quiz_question.question,
            id__in=selected_ids,
        )
        quiz_answer.selected_options.set(options_qs)

        # 3) scoring
        earned, max_score = quiz_answer.compute_score(save=True)
        attempt.is_correct = (earned == max_score and max_score > 0)
        attempt.save(update_fields=["is_correct"])

        # 4) réponse
        data = {
            "session": str(attempt.session_id),
            "question": attempt.question_id,
            "question_order": attempt.question_order,
            "selected_option_ids": list(options_qs.values_list("id", flat=True)),
            "is_correct": attempt.is_correct,
            "answered_at": attempt.answered_at,
        }
        return Response(data, status=status.HTTP_200_OK)

    def get(self, request, quiz_id, question_order):
        """
        Renvoie :
        - question + options
        - is_selected pour chaque option
        - is_correct sur les options SI (mode practice OU quiz clôturé)
        """
        session = get_object_or_404(QuizSession, pk=quiz_id)

        if not (request.user.is_staff or session.user == request.user):
            return Response({"detail": "Vous n'êtes pas autorisé à accéder à ce quiz."},
                            status=status.HTTP_403_FORBIDDEN)

        quiz_question = get_object_or_404(
            QuizQuestion,
            quiz=session.quiz,
            sort_order=question_order,
        )
        question = quiz_question.question

        # récupérer éventuelle tentative + QuizAnswer
        attempt = QuizAttempt.objects.filter(
            session=session,
            question=question,
            question_order=question_order,
        ).first()

        selected_ids = set()
        if attempt:
            qa = QuizAnswer.objects.filter(attempt=attempt, question=question).first()
            if qa:
                selected_ids = set(qa.selected_options.values_list("id", flat=True))

        show_correct = (
            session.quiz.mode == Quiz.MODE_PRACTICE
            or session.is_closed
        )

        options = []
        for opt in question.answer_options.all().order_by("sort_order", "id"):
            o = {
                "id": opt.id,
                "content": opt.content,
                "is_selected": opt.id in selected_ids,
            }
            if show_correct:
                o["is_correct"] = opt.is_correct
            options.append(o)

        data = {
            "quiz_id": str(session.id),
            "quiz_title": session.quiz.title,
            "question_id": question.id,
            "question_order": question_order,
            "title": getattr(question, "title", ""),
            "description": getattr(question, "description", ""),
            "options": options,
        }
        serializer = QuizAttemptDetailSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, quiz_id, question_order):
        session = get_object_or_404(QuizSession, pk=quiz_id)
        if not (request.user.is_staff or session.user == request.user):
            return Response({"detail": "Non autorisé."}, status=status.HTTP_403_FORBIDDEN)

        deleted, _ = QuizAttempt.objects.filter(
            session=session,
            question_order=question_order,
        ).delete()

        if deleted == 0:
            return Response({"detail": "Aucune tentative à supprimer."}, status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)



class QuizCloseView(GenericAPIView):
    """
    POST /api/quiz/<quiz_id>/close/
    → Seuls proprio de la session + admin
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuizSessionSerializer

    def post(self, request, quiz_id):
        session = get_object_or_404(QuizSession, pk=quiz_id)

        # Règle d'accès : proprio ou admin
        if not (request.user.is_staff or session.user == request.user):
            return Response(
                {"detail": "Vous n'êtes pas autorisé à clôturer ce quiz."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if session.is_closed:
            return Response(
                {"detail": "Ce quiz est déjà clôturé."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session.is_closed = True
        session.save(update_fields=["is_closed"])

        return Response(
            {
                "detail": "Quiz clôturé avec succès.",
                "quiz_id": str(session.id),
                "closed_at": timezone.now(),
            },
            status=status.HTTP_200_OK,
        )


class QuizSummaryView(GenericAPIView):
    """
    GET /api/quiz/<quiz_id>/summary/
    → Seuls proprio de la session + admin.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuizSummarySerializer

    def get(self, request, quiz_id):
        session = get_object_or_404(QuizSession, pk=quiz_id)

        # Règle d'accès : proprio ou admin
        if not (request.user.is_staff or session.user == request.user):
            return Response(
                {"detail": "Vous n'êtes pas autorisé à accéder à ce quiz."},
                status=status.HTTP_403_FORBIDDEN,
            )

        total_questions = session.quiz.quiz_questions.count()
        attempts = session.attempts.all()
        answered_questions = attempts.count()
        correct_answers = attempts.filter(is_correct=True).count()

        data = {
            "quiz_id": str(session.id),
            "quiz_title": session.quiz.title,
            "started_at": session.started_at,
            "is_closed": session.is_closed,
            "is_expired": session.is_expired,
            "max_duration": session.max_duration,
            "expires_at": session.expires_at,
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "correct_answers": correct_answers,
        }
        return Response(data, status=status.HTTP_200_OK)


class QuizViewSet(viewsets.ModelViewSet):
    """
    Endpoints principaux (admin only) :

      - POST /api/quiz/           -> créer un quiz (renvoie le slug)
      - GET  /api/quiz/           -> lister les quiz
      - GET  /api/quiz/{slug}/    -> détail d'un quiz
      - PUT/PATCH/DELETE /api/quiz/{slug}/

    Gestion des questions d'un quiz :

      - GET    /api/quiz/{slug}/questions/
      - POST   /api/quiz/{slug}/add-question/
      - DELETE /api/quiz/{slug}/remove-question/{question_id}/
    """
    queryset = Quiz.objects.all().prefetch_related("quiz_questions__question")
    serializer_class = QuizSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    # ---------- GESTION DES QUESTIONS D'UN QUIZ ----------

    @action(detail=True, methods=["get"], url_path="questions", url_name="questions")
    def list_questions(self, request, slug=None):
        """
        GET /api/quiz/{slug}/questions/
        -> liste des questions liées à ce quiz.
        """
        quiz = self.get_object()
        qs = quiz.quiz_questions.select_related("question").all()
        serializer = QuizQuestionInlineSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="add-question")
    def add_question(self, request, slug=None):
        """
        POST /api/quiz/{slug}/add-question/

        Payload JSON :
        {
            "question_id": 123,
            "sort_order": 1,
            "weight": 2
        }
        """
        quiz = self.get_object()
        data_serializer = QuizQuestionUpdateSerializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)

        question_id = data_serializer.validated_data["question_id"]
        sort_order = data_serializer.validated_data["sort_order"]
        weight = data_serializer.validated_data["weight"]

        question = get_object_or_404(Question, pk=question_id)

        qq, created = QuizQuestion.objects.update_or_create(
            quiz=quiz,
            question=question,
            defaults={
                "sort_order": sort_order,
                "weight": weight,
            },
        )

        out = QuizQuestionInlineSerializer(qq)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(out.data, status=status_code)

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"remove-question/(?P<question_id>\d+)",
    )
    def remove_question(self, request, slug=None, question_id=None):
        """
        DELETE /api/quiz/{slug}/remove-question/{question_id}/
        -> retire une question du quiz.
        """
        quiz = self.get_object()
        question = get_object_or_404(Question, pk=question_id)

        deleted, _ = QuizQuestion.objects.filter(
            quiz=quiz, question=question
        ).delete()

        if deleted == 0:
            return Response(
                {"detail": "Cette question n'est pas liée à ce quiz."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"detail": "Question retirée du quiz."},
            status=status.HTTP_204_NO_CONTENT,
        )
