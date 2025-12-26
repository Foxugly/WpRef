import logging
import random

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
)
from question.models import Question
from question.serializers import QuestionSerializer
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from subject.models import Subject
from wpref.tools import MyModelViewSet

from .models import QuizTemplate, QuizQuestion, Quiz, QuizQuestionAnswer
from .permissions import IsOwnerOrStaff
from .serializers import (
    QuizTemplateSerializer,  # QuizQuestionSerializer,
    QuizSerializer, QuizQuestionAnswerSerializer, QuizQuestionReadSerializer, QuizQuestionWriteSerializer,
    QuizQuestionAnswerWriteSerializer, GenerateFromSubjectsInputSerializer, BulkCreateFromTemplateInputSerializer,
    CreateQuizInputSerializer
)

logger = logging.getLogger(__name__)


# ---------- QuizTemplate ----------
@extend_schema_view(
    list=extend_schema(
        tags=["QuizTemplate"],
        summary="Lister les templates de quiz",
        responses={200: QuizTemplateSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["QuizTemplate"],
        summary="Détail d’un template de quiz",
        responses={200: QuizTemplateSerializer},
    ),
    create=extend_schema(
        tags=["QuizTemplate"],
        summary="Créer un template de quiz",
        request=QuizTemplateSerializer,
        responses={201: QuizTemplateSerializer},
    ),
    update=extend_schema(
        tags=["QuizTemplate"],
        summary="Mettre à jour un template de quiz",
        request=QuizTemplateSerializer,
        responses={200: QuizTemplateSerializer},

    ),
    partial_update=extend_schema(
        tags=["QuizTemplate"],
        summary="Mettre à jour partiellement un template de quiz",
        request=QuizTemplateSerializer,
        responses={200: QuizTemplateSerializer},
    ),
    destroy=extend_schema(
        tags=["QuizTemplate"],
        summary="Supprimer un template de quiz",
        responses={204: OpenApiResponse(description="No Content")},
    ),
)
class QuizTemplateViewSet(MyModelViewSet):
    queryset = QuizTemplate.objects.all().prefetch_related("quiz_questions__question")
    serializer_class = QuizTemplateSerializer
    lookup_field = "pk"
    lookup_url_kwarg = "qt_id"

    def get_permissions(self):
        """
        Permissions:
          - generate_from_subjects, available : user authentifié
          - tout le reste (CRUD, questions)   : staff uniquement
        """
        if self.action in ["generate_from_subjects", "list", "retrieve", ]:
            return [IsAuthenticated()]

        return [IsAdminUser()]

    # ==========================================================
    # CRUD NATIF : SURCHARGES
    # ==========================================================

    def list(self, request, *args, **kwargs):
        self._log_call(
            method_name="list",
            endpoint="GET /api/quiz/template/",
            input_expected="query params (optionnels), body vide",
            output="200 + [QuizTemplateSerializer] (paginé si pagination activée)",
        )
        if request.user.is_staff or request.user.is_superuser:
            return super().list(request, *args, **kwargs)
        else:
            qs = list(self.get_queryset())
            qs = [qt for qt in qs if qt.can_answer]

            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        self._log_call(
            method_name="retrieve",
            endpoint="GET /api/quiz/template/{qt_id}/",
            input_expected="path param: id (qt_id)",
            output="200 + QuizTemplateSerializer | 404",
            extra={"pk": kwargs.get("qt_id")},
        )
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        self._log_call(
            method_name="create",
            endpoint="POST /api/quiz/template/",
            input_expected="body JSON: QuizTemplateSerializer (champs write)",
            output="201 + QuizTemplateSerializer | 400",
        )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._log_call(
            method_name="update",
            endpoint="PUT /api/quiz/template/{qt_id}/",
            input_expected="path qt_id + body JSON complet (QuizTemplateSerializer)",
            output="200 + QuizTemplateSerializer | 400 | 404",
            extra={"pk": kwargs.get("qt_id")},
        )
        print("update")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._log_call(
            method_name="partial_update",
            endpoint="PATCH /api/quiz/template/{qt_id}/",
            input_expected="path pk + body JSON partiel (QuizTemplateSerializer)",
            output="200 + QuizTemplateSerializer | 400 | 404",
            extra={"pk": kwargs.get("qt_id")},
        )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._log_call(
            method_name="destroy",
            endpoint="DELETE /api/quiz/template/{id}/",
            input_expected="path pk, body vide",
            output="204 | 404",
            extra={"pk": kwargs.get("pk")},
        )
        return super().destroy(request, *args, **kwargs)

    # ==========================================================
    # ACTIONS CUSTOM (je garde les tiennes, avec logging amélioré)
    # ==========================================================
    @extend_schema(
        tags=["QuizTemplate"],
        summary="Générer un template depuis des sujets",
        request=GenerateFromSubjectsInputSerializer,
        responses={
            201: QuizTemplateSerializer,
            400: OpenApiResponse(description="Input invalide / aucune question trouvée"),
        },
    )
    @action(detail=False, methods=["post"], url_path="generate-from-subjects")
    def generate_from_subjects(self, request, *args, **kwargs):
        self._log_call(
            method_name="generate_from_subjects",
            endpoint="POST /api/quiz/template/generate-from-subjects/",
            input_expected="body: {title, subject_ids[], max_questions?}",
            output="201 + QuizTemplateSerializer | 400",
        )
        title = request.data.get("title")
        subject_ids = request.data.get("subject_ids", [])
        max_questions = int(request.data.get("max_questions", 10))

        if not title:
            logger.warning("generate_from_subjects: missing title")
            return Response({"detail": "Le champ 'title' est requis."}, status=status.HTTP_400_BAD_REQUEST, )

        if not isinstance(subject_ids, list) or not subject_ids:
            logger.warning("generate_from_subjects: subject_ids invalid")
            return Response({"detail": "subject_ids doit être une liste non vide."},
                            status=status.HTTP_400_BAD_REQUEST, )

        ids = list(
            Question.objects.filter(
                subjects__id__in=subject_ids,
                active=True,
            )
            .distinct()
            .values_list("id", flat=True)
        )
        if not ids:
            return Response({"detail": "Aucune question trouvée pour ces sujets."},
                            status=status.HTTP_400_BAD_REQUEST)

        n_questions = min(len(ids), max_questions)
        picked_ids = random.sample(ids, n_questions)
        questions_qs = Question.objects.filter(id__in=picked_ids)

        if not questions_qs.exists():
            logger.warning("generate_from_subjects: no questions found subject_ids=%s", subject_ids)
            return Response({"detail": "Aucune question trouvée pour ces sujets."},
                            status=status.HTTP_400_BAD_REQUEST, )

        quiz_template = QuizTemplate.objects.create(title=title, max_questions=n_questions, permanent=True,
                                                    active=True, )
        quiz_questions = []
        for index, question in enumerate(questions_qs, start=1):
            quiz_questions.append(QuizQuestion(quiz=quiz_template, question=question, sort_order=index, weight=1, ))
        QuizQuestion.objects.bulk_create(quiz_questions)
        serializer = self.get_serializer(quiz_template)
        logger.info("generate_from_subjects: created quiz_template_id=%s nb_questions=%s", quiz_template.id,
                    len(quiz_questions))
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ----- Gestion des QuizQuestion pour un template -----
    @extend_schema(
        tags=["QuizTemplate"],
        summary="Ajouter une question à un template",
        request=QuizQuestionWriteSerializer,
        responses={
            201: QuizQuestionReadSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Template introuvable"),
        },
    )
    @action(detail=True, methods=["post"], url_path="question")
    def add_question(self, request, pk=None, *args, **kwargs):
        self._log_call(
            method_name="add_question",
            endpoint="POST /api/quiz/template/{id}/question/",
            input_expected="body: QuizQuestionSerializer fields (question_id, sort_order?, weight?)",
            output="201 + QuizQuestionSerializer | 400 | 404",
            extra={"pk": pk},
        )
        quiz_template = self.get_object()
        serializer = QuizQuestionWriteSerializer(data=request.data, context={"quiz_template": quiz_template})
        serializer.is_valid(raise_exception=True)
        quizquestion = serializer.save()
        out = QuizQuestionReadSerializer(
            quizquestion,
            context=self.get_serializer_context(),
        )
        logger.info("add_question: created quizquestion_id=%s quiz_template_id=%s", quizquestion.id, quiz_template.id)
        return Response(out.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["QuizTemplate"],
        summary="Mettre à jour une question (QuizQuestion) d’un template",
        request=QuizQuestionWriteSerializer,
        responses={
            200: QuizQuestionReadSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Template ou QuizQuestion introuvable"),
        },
        parameters=[
            OpenApiParameter("quizquestion_id", OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
    )
    @action(detail=True, methods=["patch", "put"], url_path=r"question/(?P<quizquestion_id>\d+)")
    def update_question(self, request, pk=None, quizquestion_id=None, *args, **kwargs):
        self._log_call(
            method_name="update_question",
            endpoint="PUT/PATCH /api/quiz/template/{id}/question/{quizquestion_id}/",
            input_expected="path pk + quizquestion_id + body (QuizQuestionSerializer)",
            output="200 + QuizQuestionSerializer | 400 | 404",
            extra={"pk": pk, "quizquestion_id": quizquestion_id},
        )
        quiz_template = self.get_object()
        try:
            quizquestion = quiz_template.quiz_questions.get(pk=quizquestion_id)
        except QuizQuestion.DoesNotExist:
            return Response(
                {"detail": "QuizQuestion introuvable pour ce template."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = QuizQuestionWriteSerializer(quizquestion, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("update_question: updated quizquestion_id=%s", quizquestion.id)
        out = QuizQuestionReadSerializer(
            quizquestion,
            context=self.get_serializer_context(),
        )
        return Response(out.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["QuizTemplate"],
        summary="Supprimer une question (QuizQuestion) d’un template",
        responses={
            204: OpenApiResponse(description="No Content"),
            404: OpenApiResponse(description="Template ou QuizQuestion introuvable"),
        },
        parameters=[
            OpenApiParameter("quizquestion_id", OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
    )
    @action(detail=True, methods=["delete"], url_path=r"question/(?P<quizquestion_id>[^/.]+)")
    def delete_question(self, request, pk=None, quizquestion_id=None, *args, **kwargs):
        self._log_call(
            method_name="delete_question",
            endpoint="DELETE /api/quiz/template/{id}/question/{quizquestion_id}/",
            input_expected="path pk + quizquestion_id, body vide",
            output="204 | 404",
            extra={"pk": pk, "quizquestion_id": quizquestion_id},
        )
        quiz_template = self.get_object()
        try:
            quizquestion = quiz_template.quiz_questions.get(pk=quizquestion_id)
        except QuizQuestion.DoesNotExist:
            logger.warning("delete_question: quizquestion not found quiz_template_id=%s quizquestion_id=%s",
                           quiz_template.id, quizquestion_id)
            return Response(
                {"detail": "QuizQuestion introuvable pour ce template."},
                status=status.HTTP_404_NOT_FOUND,
            )
        quizquestion.delete()
        logger.info("delete_question: deleted quizquestion_id=%s", quizquestion_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Quiz (sessions) ----------

@extend_schema_view(
    list=extend_schema(
        tags=["QuizTemplate"],
        summary="Lister les QuizQuestion d’un template (nested)",
        responses={200: QuizQuestionReadSerializer(many=True)},
        parameters=[
            OpenApiParameter("qt_id", OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
    ),
    retrieve=extend_schema(
        tags=["QuizTemplate"],
        summary="Détail d’une QuizQuestion d’un template (nested)",
        responses={200: QuizQuestionReadSerializer},
        parameters=[
            OpenApiParameter("qt_id", OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
    ),
    create=extend_schema(
        tags=["QuizTemplate"],
        summary="Créer une QuizQuestion dans un template (nested)",
        request=QuizQuestionWriteSerializer,
        responses={
            201: QuizQuestionWriteSerializer,  # ou ReadSerializer si tu préfères renvoyer le READ
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Template introuvable"),
        },
        parameters=[
            OpenApiParameter("qt_id", OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
    ), update=extend_schema(
        tags=["QuizTemplate"],
        summary="Mettre à jour une QuizQuestion (nested)",
        request=QuizQuestionWriteSerializer,
        responses={200: QuizQuestionWriteSerializer},
        parameters=[
            OpenApiParameter("qt_id", OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
    ),
    partial_update=extend_schema(
        tags=["QuizTemplate"],
        summary="Mettre à jour partiellement une QuizQuestion (nested)",
        request=QuizQuestionWriteSerializer,
        responses={200: QuizQuestionWriteSerializer},
        parameters=[
            OpenApiParameter("qt.id", OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
    ),
    destroy=extend_schema(
        tags=["QuizTemplate"],
        summary="Supprimer une QuizQuestion (nested)",
        responses={204: OpenApiResponse(description="No Content")},
        parameters=[
            OpenApiParameter("qt_id", OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
    ),
)
class QuizTemplateQuizQuestionViewSet(MyModelViewSet):
    permission_classes = [IsAdminUser]
    lookup_field = "pk"
    lookup_url_kwarg = "qq_id"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return QuizQuestion.objects.none()

        qt_id = self.kwargs.get("qt_id")
        if not qt_id:
            # sécurité: évite KeyError si jamais appelé sans kwargs
            return QuizQuestion.objects.none()
        return (
            QuizQuestion.objects
            .filter(quiz_id=self.kwargs["qt_id"])
            .select_related("question", "quiz")
        )

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return QuizQuestionReadSerializer
        return QuizQuestionWriteSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["quiz_template"] = get_object_or_404(QuizTemplate, pk=self.kwargs["qt_id"])
        return ctx

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        out = QuizQuestionReadSerializer(instance, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        out = QuizQuestionReadSerializer(instance, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        write = QuizQuestionWriteSerializer(
            instance,
            data=request.data,
            partial=False,
            context=self.get_serializer_context(),
        )
        write.is_valid(raise_exception=True)
        instance = write.save()
        out = QuizQuestionReadSerializer(instance, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        write = QuizQuestionWriteSerializer(
            instance,
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        write.is_valid(raise_exception=True)
        instance = write.save()

        out = QuizQuestionReadSerializer(instance, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        tags=["Quiz"],
        summary="Lister les quizzes (sessions)",
        responses={200: QuizSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Quiz"],
        summary="Détail d’un quiz (session)",
        responses={200: QuizSerializer},
    ),
    create=extend_schema(
        tags=["Quiz"],
        summary="Créer un quiz à partir d'un template de quiz",
        request=QuizSerializer,
        responses={201: QuizSerializer},
    ),
    update=extend_schema(
        tags=["Quiz"],
        summary="Mettre à jour un quiz",
        request=QuizSerializer,
        responses={200: QuizSerializer},
    ),
    partial_update=extend_schema(
        tags=["Quiz"],
        summary="Mettre à jour partiellement un quiz",
        request=QuizSerializer,
        responses={200: QuizSerializer},
    ),
    destroy=extend_schema(
        tags=["Quiz"],
        summary="Supprimer un quiz",
        responses={204: OpenApiResponse(description="No Content")},
    ),
)
class QuizViewSet(MyModelViewSet):
    serializer_class = QuizSerializer
    permission_classes = [IsOwnerOrStaff]
    lookup_field = "pk"
    lookup_url_kwarg = "quiz_id"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Quiz.objects.none()
        qs = (Quiz.objects.select_related("quiz_template", "user")
              .prefetch_related("quiz_template__quiz_questions__question__answer_options"))
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return qs
        return qs.filter(user=user)

    def get_permissions(self):
        """
        Permissions:
          - bulk_create_from_template : admin only
          - autres actions            : IsOwnerOrStaff
        """
        if self.action == "bulk_create_from_template":
            return [IsAdminUser()]

        return super().get_permissions()

    # ==========================================================
    # CRUD NATIF : SURCHARGES
    # ==========================================================

    def list(self, request, *args, **kwargs):
        self._log_call(
            method_name="list",
            endpoint="GET /api/quiz/",
            input_expected="query params optionnels, body vide",
            output="200 + [QuizSerializer] (paginé si pagination activée)",
        )
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self._log_call(
            method_name="retrieve",
            endpoint="GET /api/quiz/{quiz_id}/",
            input_expected="path param: quiz_id",
            output="200 + QuizSerializer | 404",
            extra={"pk": kwargs.get("quiz_id")},
        )
        quiz = self.get_object()
        serializer = self.get_serializer(quiz)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        self._log_call(
            method_name="create",
            endpoint="POST /api/quiz/",
            input_expected="body: {quiz_template_id:int, user_id?:int}",
            output="201 + QuizSerializer  | 400 | 403 | 404",
        )
        quiz_template_id = request.data.get("quiz_template_id")
        if not quiz_template_id:
            logger.warning("create: missing quiz_template_id")
            return Response(
                {"detail": "quiz_template_id est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            qt = QuizTemplate.objects.get(pk=quiz_template_id)
        except QuizTemplate.DoesNotExist:
            logger.warning("create: QuizTemplate not found id=%s", quiz_template_id)
            return Response(
                {"detail": "QuizTemplate introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not qt.can_answer:
            logger.warning("create: template not available qt_id=%s", qt.id)
            return Response(
                {"detail": "Ce quiz n'est pas disponible actuellement."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_user = request.user
        user_id = request.data.get("user_id")
        if user_id is not None:
            if not (request.user.is_staff or request.user.is_superuser):
                raise PermissionDenied("Seul un admin peut créer un quiz pour un autre utilisateur.")
            target_user = get_object_or_404(get_user_model(), pk=user_id)

        quiz = Quiz.objects.create(
            quiz_template=qt,
            user=target_user,
            active=False,
        )
        logger.info("create: created quiz_id=%s user_id=%s qt_id=%s", quiz.id, request.user.id,
                    qt.id)
        serializer = self.get_serializer(quiz)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        self._log_call(
            method_name="update",
            endpoint="PUT /api/quiz/{quiz_id}/",
            input_expected="path pk + body JSON complet (QuizSerializer)",
            output="200 + QuizSerializer | 400 | 404",
            extra={"pk": kwargs.get("quiz_id")},
        )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._log_call(
            method_name="partial_update",
            endpoint="PATCH /api/quiz/{quiz_id}/",
            input_expected="path pk + body JSON partiel (QuizSerializer)",
            output="200 + QuizSerializer | 400 | 404",
            extra={"pk": kwargs.get("quiz_id")},
        )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._log_call(
            method_name="destroy",
            endpoint="DELETE /api/quiz/{quiz_id}/",
            input_expected="path pk, body vide",
            output="204 | 404",
            extra={"pk": kwargs.get("quiz_id")},
        )
        return super().destroy(request, *args, **kwargs)

    # ==========================================================
    # ACTIONS CUSTOM : avec endpoint/input/output/logging
    # ==========================================================
    @extend_schema(
        tags=["Quiz"],
        summary="Créer des quizzes depuis un template (bulk)",
        request=BulkCreateFromTemplateInputSerializer,
        responses={
            201: QuizSerializer(many=True),
            400: OpenApiResponse(description="Input invalide"),
            404: OpenApiResponse(description="QuizTemplate introuvable"),
        },
    )
    @action(detail=False, methods=["post"], url_path="bulk-create-from-template",
            permission_classes=[IsAdminUser])
    def bulk_create_from_template(self, request, *args, **kwargs):
        quiz_template_id = request.data.get("quiz_template_id")
        user_ids = request.data.get("user_ids", [])

        if not quiz_template_id or not isinstance(user_ids, list) or not user_ids:
            logger.warning("bulk_create_from_template: invalid input quiz_template_id=%s user_ids=%s", quiz_template_id,
                           user_ids)
            return Response(
                {"detail": "quiz_template_id et une liste user_ids sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            qt = QuizTemplate.objects.get(pk=quiz_template_id)
        except QuizTemplate.DoesNotExist:
            logger.warning("bulk_create_from_template: QuizTemplate not found id=%s", quiz_template_id)
            return Response(
                {"detail": "QuizTemplate introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        users = get_user_model().objects.filter(id__in=user_ids)
        created = []
        with transaction.atomic():
            for u in users:
                created.append(
                    Quiz.objects.create(
                        quiz_template=qt,
                        user=u,
                        active=False,
                    )
                )
        logger.info(
            "bulk_create_from_template: created=%s quiz_template_id=%s users_count=%s",
            len(created),
            qt.id,
            users.count(),
        )
        serializer = self.get_serializer(created, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Quiz"],
        summary="Créer un quiz pour l’utilisateur courant",
        request=CreateQuizInputSerializer,
        responses={
            201: QuizSerializer,
            400: OpenApiResponse(description="Input invalide / quiz non disponible"),
            404: OpenApiResponse(description="QuizTemplate introuvable"),
        },
    )
    @action(detail=True, methods=["post"], url_path="start", permission_classes=[IsOwnerOrStaff])
    def start(self, request, quiz_id=None, *args, **kwargs):
        self._log_call(
            method_name="start",
            endpoint="POST /api/quiz/{quiz_id}/start/",
            input_expected="path pk, body vide",
            output="200 + QuizSerializer | 400 | 404",
            extra={"pk": quiz_id},
        )
        quiz = self.get_object()
        if not quiz.quiz_template.can_answer:
            logger.warning("start: template not available quiz_id=%s qt_id=%s", quiz.id, quiz.quiz_template_id)
            return Response(
                {"detail": "Ce quiz n'est pas disponible actuellement."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        quiz.started_at = timezone.now()
        quiz.active = True
        quiz.save()
        logger.info("start: started quiz_id=%s", quiz.id)
        serializer = self.get_serializer(quiz)
        return Response(serializer.data)

    @extend_schema(
        tags=["Quiz"],
        summary="Clôturer un quiz (calcule les scores)",
        request=None,
        responses={
            200: QuizSerializer,
            404: OpenApiResponse(description="Quiz introuvable"),
            409: OpenApiResponse(description="Quiz jamais démarré ou déjà clôturé"),
        },
    )
    @action(detail=True, methods=["post"], url_path="close", permission_classes=[IsOwnerOrStaff])
    def close(self, request, quiz_id=None, *args, **kwargs):
        self._log_call(
            method_name="close",
            endpoint="POST /api/quiz/{quiz_id}/close/",
            input_expected="path quiz_id, body vide",
            output="200 + QuizSerializer | 404",
            extra={"quiz_id": quiz_id},
        )

        with transaction.atomic():
            quiz = get_object_or_404(self.get_queryset().select_for_update(), pk=quiz_id)

            if quiz.started_at is None:
                return Response(
                    {"detail": "Impossible de clôturer : le quiz n'a jamais été démarré."},
                    status=status.HTTP_409_CONFLICT,
                )

            if quiz.active is False:
                return Response(
                    {"detail": "Impossible de clôturer : le quiz est déjà clôturé."},
                    status=status.HTTP_409_CONFLICT,
                )
            quiz.active = False
            if not quiz.ended_at:
                quiz.ended_at = timezone.now()
            quiz.save(update_fields=["active", "ended_at"])

            # 3) calcule les scores des réponses
            answers = (
                quiz.answers
                .select_related("quizquestion__question")
                .prefetch_related(
                    "selected_options",
                    "quizquestion__question__answer_options",
                )
            )

            to_update = []
            for a in answers:
                # correct options (depuis le prefetch)
                correct_ids = {
                    opt.id for opt in a.quizquestion.question.answer_options.all()
                    if opt.is_correct
                }
                selected_ids = {opt.id for opt in a.selected_options.all()}
                weight = float(a.quizquestion.weight or 0)
                a.max_score = weight

                if correct_ids and selected_ids == correct_ids:
                    a.earned_score = weight
                    a.is_correct = True
                else:
                    a.earned_score = 0.0
                    a.is_correct = False

                to_update.append(a)

            if to_update:
                QuizQuestionAnswer.objects.bulk_update(
                    to_update,
                    ["earned_score", "max_score", "is_correct"]
                )
        logger.info("close: closed quiz_id=%s ended_at=%s", quiz.id, quiz.ended_at)
        return self.retrieve(request, *args, **kwargs)


# ---------- QuizQuestionAnswer (nested sous /quiz/{quiz_id}/answer/) ----------
@extend_schema_view(
    list=extend_schema(
        tags=["QuizAnswer"],
        summary="Lister les réponses d’un quiz",
        responses={200: QuizQuestionAnswerSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["QuizAnswer"],
        summary="Détail d’une réponse",
        responses={200: QuizQuestionAnswerSerializer},
    ),
    create=extend_schema(
        tags=["QuizAnswer"],
        summary="Créer / enregistrer une réponse à une question (upsert)",
        request=QuizQuestionAnswerWriteSerializer,
        responses={
            201: QuizQuestionAnswerSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Quiz introuvable"),
        },
    ),
    update=extend_schema(
        tags=["QuizAnswer"],
        summary="Mettre à jour une réponse",
        request=QuizQuestionAnswerWriteSerializer,
        responses={200: QuizQuestionAnswerSerializer},
    ), partial_update=extend_schema(
        tags=["QuizAnswer"],
        summary="Mettre à jour partiellement une réponse",
        request=QuizQuestionAnswerWriteSerializer,
        responses={200: QuizQuestionAnswerSerializer},
    ),
    destroy=extend_schema(
        tags=["QuizAnswer"],
        summary="Supprimer une réponse",
        responses={204: OpenApiResponse(description="No Content")},
    ),
)
class QuizQuestionAnswerViewSet(MyModelViewSet):
    permission_classes = [IsOwnerOrStaff]
    lookup_field = "pk"
    lookup_url_kwarg = "answer_id"

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return QuizQuestionAnswerWriteSerializer
        return QuizQuestionAnswerSerializer

    def get_quiz(self):
        if hasattr(self, "_quiz_cache"):
            return self._quiz_cache

        qs = Quiz.objects.select_related("quiz_template", "user")
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(user=user)

        self._quiz_cache = get_object_or_404(qs, pk=self.kwargs["quiz_id"])
        return self._quiz_cache

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if not getattr(self, "swagger_fake_view", False):
            ctx["quiz"] = self.get_quiz()
        return ctx

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return QuizQuestionAnswer.objects.none()
        quiz = self.get_quiz()

        qs = (
            QuizQuestionAnswer.objects
            .select_related("quiz", "quizquestion__question")  # ✅ typo fixed
            .prefetch_related("selected_options")
            .filter(quiz_id=quiz.id)
        )
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return qs
        return qs.filter(quiz__user=user)

    def get_permissions(self):
        """
        Permissions:
          - toutes les actions : IsOwnerOrStaff
          - le filtrage réel se fait dans get_queryset()
        """
        return super().get_permissions()

    # ==========================================================
    # CRUD NATIF : SURCHARGES
    # ==========================================================

    def list(self, request, *args, **kwargs):
        self._log_call(
            method_name="list",
            endpoint="GET /api/quiz/{quiz_id}/answer/",
            input_expected="path quiz_id, query params optionnels, body vide",
            output="200 + [QuizQuestionAnswerSerializer] (paginé)",
        )
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self._log_call(
            method_name="retrieve",
            endpoint="GET /api/quiz/{quiz_id}/answer/{answer_id}/",
            input_expected="path quiz_id + answer_id, body vide",
            output="200 + QuizQuestionAnswerSerializer | 404",
            extra={"answer_id": kwargs.get("answer_id")}
        )
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        self._log_call(
            method_name="create",
            endpoint="POST /api/quiz/{quiz_id}/answer/",
            input_expected="path quiz_id + body JSON (QuizQuestionAnswerSerializer write fields). Quiz imposé par URL.",
            output="201 + QuizQuestionAnswerSerializer | 400 | 404",
        )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        out = QuizQuestionAnswerSerializer(
            instance,
            context=self.get_serializer_context(),
        )
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        self._log_call(
            method_name="update",
            endpoint="PUT /api/quiz/{quiz_id}/answer/{answer_id}/",
            input_expected="path quiz_id + answer_id + body JSON complet (QuizQuestionAnswerSerializer)",
            output="200 + QuizQuestionAnswerSerializer | 400 | 404",
            extra={"answer_id": kwargs.get("answer_id")}
        )
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        inp = self.get_serializer(instance, data=request.data, partial=partial)
        inp.is_valid(raise_exception=True)
        instance = inp.save()
        out = QuizQuestionAnswerSerializer(instance, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        self._log_call(
            method_name="partial_update",
            endpoint="PATCH /api/quiz/{quiz_id}/answer/{answer_id}/",
            input_expected="path quiz_id + answer_id + body JSON partiel (QuizQuestionAnswerSerializer)",
            output="200 + QuizQuestionAnswerSerializer | 400 | 404",
            extra={"answer_id": kwargs.get("answer_id")}
        )
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._log_call(
            method_name="destroy",
            endpoint="DELETE /api/quiz/{quiz_id}/answer/{answer_id}/",
            input_expected="path quiz_id + answer_id, body vide",
            output="204 | 404",
            extra={"answer_id": kwargs.get("answer_id")}
        )
        return super().destroy(request, *args, **kwargs)
