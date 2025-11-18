# quiz/api/views.py

from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Quiz, QuizQuestion, QuizSession, QuizAttempt
from .serializers import (
    QuizAttemptSerializer,
    QuizSessionSerializer,
    QuizQuestionDetailSerializer,
    QuizSummarySerializer,
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
        }
        return Response(data, status=status.HTTP_201_CREATED)


class QuizAttemptView(GenericAPIView):
    """
    POST/GET /api/quiz/<quiz_id>/attempt/<question_order>/
    → Seuls : user propriétaire de la session OU admin.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuizAttemptSerializer

    def get_session_and_quiz_question(self, quiz_id, question_order):
        session = get_object_or_404(QuizSession, pk=quiz_id)
        quiz_question = get_object_or_404(
            QuizQuestion,
            quiz=session.quiz,
            sort_order=question_order,   # <-- IMPORTANT : sort_order
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

        given_answer = request.data.get("given_answer")
        if given_answer is None:
            return Response(
                {"detail": "Le champ 'given_answer' est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attempt, created = QuizAttempt.objects.update_or_create(
            session=session,
            question_order=question_order,
            defaults={
                "question": quiz_question.question,
                "given_answer": given_answer,
            },
        )

        data = {
            "session": str(attempt.session_id),
            "question": attempt.question_id,
            "question_order": attempt.question_order,
            "given_answer": attempt.given_answer,
            "is_correct": attempt.is_correct,
            "answered_at": attempt.answered_at,
        }
        return Response(data, status=status.HTTP_200_OK)

    def get(self, request, quiz_id, question_order):
        session = get_object_or_404(QuizSession, pk=quiz_id)

        # Règle d'accès : proprio ou admin
        if not (request.user.is_staff or session.user == request.user):
            return Response(
                {"detail": "Vous n'êtes pas autorisé à accéder à ce quiz."},
                status=status.HTTP_403_FORBIDDEN,
            )

        attempt = get_object_or_404(
            QuizAttempt,
            session=session,
            question_order=question_order,
        )

        data = {
            "session": str(attempt.session_id),
            "question": attempt.question_id,
            "question_order": attempt.question_order,
            "given_answer": attempt.given_answer,
            "is_correct": attempt.is_correct,
            "answered_at": attempt.answered_at,
        }
        return Response(data, status=status.HTTP_200_OK)


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


class QuizQuestionDetailView(GenericAPIView):
    """
    GET /api/quiz/<quiz_id>/question/<question_order>/
    → Seuls proprio de la session + admin.

    Règle is_correct :
      - mode EXAM + quiz non clôturé → pas de is_correct
      - sinon (mode PRACTICE ou quiz clôturé) → is_correct présent
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuizQuestionDetailSerializer

    def get(self, request, quiz_id, question_order):
        session = get_object_or_404(QuizSession, pk=quiz_id)

        # Règle d'accès : proprio ou admin
        if not (request.user.is_staff or session.user == request.user):
            return Response(
                {"detail": "Vous n'êtes pas autorisé à accéder à ce quiz."},
                status=status.HTTP_403_FORBIDDEN,
            )

        quiz_question = get_object_or_404(
            QuizQuestion,
            quiz=session.quiz,
            sort_order=question_order,  # <-- FIX : sort_order
        )
        question = quiz_question.question

        # is_correct visible si mode practice OU session clôturée
        show_correct = (
            session.quiz.mode == Quiz.MODE_PRACTICE
            or session.is_closed
        )

        options = []
        for opt in question.answer_options.all().order_by("sort_order", "id"):
            o = {
                "id": opt.id,
                "content": opt.content,
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
        return Response(data, status=status.HTTP_200_OK)


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
