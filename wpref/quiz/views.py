# quiz/api/views.py

from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status, permissions
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from customuser.permissions import IsSelfOrStaffOrSuperuser
from .models import Quiz, QuizQuestion, QuizSession, QuizAttempt
from .serializers import QuizAttemptSerializer, QuizSessionSerializer, QuizQuestionDetailSerializer, QuizSummarySerializer

class QuizStartView(GenericAPIView):
    """
    Démarre un quiz à partir de son slug.
    Endpoint : POST /api/quiz/<slug>/start/

    - Crée une QuizSession
    - started_at est rempli automatiquement (timezone.now)
    - max_duration = 30 minutes par défaut (défini dans le modèle)
    - is_closed = False par défaut
    """
    permission_classes = [IsAuthenticated] # À adapter (IsAuthenticated, etc.)
    serializer_class = QuizSessionSerializer
    queryset = QuizSession.objects.all()

    def post(self, request, slug):
        quiz = get_object_or_404(Quiz, slug=slug)

        session = QuizSession.objects.create(
            quiz=quiz,
            user=request.user if request.user.is_authenticated else None,
        )

        # Pour rester simple, on renvoie un JSON "manuel"
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
    Gère les réponses aux questions d'un quiz pour une session donnée.
    Endpoints :
      - POST /api/quiz/<quiz_id>/attempt/<question_order>/
          -> Enregistrer / modifier une réponse
      - GET  /api/quiz/<quiz_id>/attempt/<question_order>/
          -> Récupérer la réponse donnée à cette question
    """
    permission_classes = [IsSelfOrStaffOrSuperuser]  # À adapter
    serializer_class = QuizAttemptSerializer

    def get_session_and_quiz_question(self, quiz_id, question_order):
        """
        Helper pour récupérer la session et la question correspondante
        au question_order *dans ce quiz*.
        """
        session = get_object_or_404(QuizSession, pk=quiz_id)
        quiz_question = get_object_or_404(
            QuizQuestion,
            quiz=session.quiz,
            order=question_order,
        )
        return session, quiz_question

    def post(self, request, quiz_id, question_order):
        """
        Enregistre ou met à jour une réponse pour la question n°question_order
        dans la session de quiz <quiz_id>.
        """
        session, quiz_question = self.get_session_and_quiz_question(
            quiz_id, question_order
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

        # Ici tu peux rajouter ta logique de correction automatique
        # Exemple : is_correct = (given_answer == quiz_question.question.correct_answer)
        # Pour l'instant, on laisse is_correct = None
        attempt, created = QuizAttempt.objects.update_or_create(
            session=session,
            question_order=question_order,
            defaults={
                "question": quiz_question.question,
                "given_answer": given_answer,
                # "is_correct": is_correct,
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
        """
        Récupère la réponse donnée à la question n°question_order
        pour la session <quiz_id>.
        """
        session = get_object_or_404(QuizSession, pk=quiz_id)

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
    Clôture une session de quiz.
    Endpoint : POST /api/quiz/<quiz_id>/close/

    - Met is_closed = True
    - Ne supprime rien, ne modifie pas les réponses
    """
    permission_classes = [IsSelfOrStaffOrSuperuser]  # À sécuriser (souvent IsAuthenticated)
    serializer_class = QuizSessionSerializer

    def post(self, request, quiz_id):
        session = get_object_or_404(QuizSession, pk=quiz_id)

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
    Renvoie l'énoncé de la question et ses options pour une session de quiz.

    Endpoint : GET /api/quiz/<quiz_id>/question/<question_order>/

    - Vérifie que la session existe
    - Récupère la question n°question_order du quiz lié à cette session
    - Renvoie :
        - question_id
        - question_order
        - title
        - description
        - options (à adapter selon ton modèle)
    """
    permission_classes = [IsSelfOrStaffOrSuperuser]
    serializer_class = QuizQuestionDetailSerializer

    def get(self, request, quiz_id, question_order):
        session = get_object_or_404(QuizSession, pk=quiz_id)
        quiz_question = get_object_or_404(
            QuizQuestion,
            quiz=session.quiz,
            order=question_order,
        )
        question = quiz_question.question

        # À adapter selon ton modèle de Question / options (QCM, oui/non, etc.)
        # Ici on renvoie une structure minimale.
        data = {
            "quiz_id": str(session.id),
            "quiz_title": session.quiz.title,
            "question_id": question.id,
            "question_order": question_order,
            "title": getattr(question, "title", ""),
            "description": getattr(question, "description", ""),
            # TODO: adapter cette partie à ton modèle d'options si tu as un modèle Choice
            "options": [],
        }
        return Response(data, status=status.HTTP_200_OK)


class QuizSummaryView(GenericAPIView):
    """
    Renvoie un résumé d'une session de quiz.

    Endpoint : GET /api/quiz/<quiz_id>/summary/

    Contenu :
      - quiz_id
      - quiz_title
      - started_at
      - is_closed
      - is_expired
      - max_duration
      - expires_at
      - total_questions
      - answered_questions
      - correct_answers
    """
    permission_classes = [IsSelfOrStaffOrSuperuser]
    serializer_class = QuizSummarySerializer

    def get(self, request, quiz_id):
        session = get_object_or_404(QuizSession, pk=quiz_id)

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
