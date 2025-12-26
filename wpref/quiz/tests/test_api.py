import logging

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from question.models import Question, AnswerOption
from quiz.models import QuizTemplate, QuizQuestion, Quiz, QuizQuestionAnswer
from rest_framework import status
from rest_framework.test import APITestCase
from subject.models import Subject

User = get_user_model()

logger = logging.getLogger(__name__)


class QuizAPITestCase(APITestCase):
    """
    Tests API pour:
      - /api/quiz/
      - /api/quiz/{id}/start/
      - /api/quiz/{id}/close/
      - /api/quiz/{quiz_pk}/answer/
      - /api/quiz/template/
    """

    def setUp(self):
        # Users
        self.admin = User.objects.create_user(
            username="admin", password="adminpass", is_staff=True, is_superuser=True
        )
        self.u1 = User.objects.create_user(username="u1", password="u1pass")
        self.u2 = User.objects.create_user(username="u2", password="u2pass")

        # Data: quiz template + questions + options
        self.qt = QuizTemplate.objects.create(
            title="Template 1",
            mode=QuizTemplate.MODE_EXAM,  # important pour visibilités
            max_questions=2,
            permanent=True,
            active=True,
            with_duration=True,
            duration=10,
        )

        self.q1 = self._create_question("Q1")
        self.q2 = self._create_question("Q2")

        self.q1_o1, self.q1_o2 = list(self.q1.answer_options.all())
        self.q2_o1, self.q2_o2 = list(self.q2.answer_options.all())

        # QuizQuestions (ordre + poids)
        self.qq1 = QuizQuestion.objects.create(quiz=self.qt, question=self.q1, sort_order=1, weight=2)
        self.qq2 = QuizQuestion.objects.create(quiz=self.qt, question=self.q2, sort_order=2, weight=3)

        # URLs
        self.quiz_list_url = reverse("api:quiz-api:quiz-list")  # /api/quiz/
        self.template_list_url = reverse("api:quiz-api:quiz-template-list")  # /api/quiz/template/

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _create_question(self, title: str, *, subject: Subject | None = None) -> Question:
        """
        Crée une Question valide pour tes tests:
        - ajoute 2 AnswerOption dont 1 correcte (sinon Question.clean() râle)
        - lie un Subject via le M2M (through=QuestionSubject)
        """
        if subject is None:
            subject = Subject.objects.create(slug=f"subj-{title.lower()}", name=f"Subject {title}")

        q = Question.objects.create(
            title=title,
            description="desc",
            explanation="expl",
            allow_multiple_correct=False,
            active=True,
            is_mode_practice=True,
            is_mode_exam=True,
        )

        # M2M avec through: Django gère via add() (créera QuestionSubject)
        q.subjects.add(subject)

        # IMPORTANT: au moins 2 options, et exactement 1 correcte (allow_multiple_correct=False)
        AnswerOption.objects.create(question=q, content="Option A", is_correct=True, sort_order=1)
        AnswerOption.objects.create(question=q, content="Option B", is_correct=False, sort_order=2)

        return q

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _create_quiz_for(self, user, *, active=False) -> Quiz:
        return Quiz.objects.create(quiz_template=self.qt, user=user, active=active)

    # ---------------------------------------------------------------------
    # QuizTemplate endpoints
    # ---------------------------------------------------------------------
    def test_debug_template_list(self):
        self._auth(self.u1)
        res = self.client.get(self.template_list_url)
        self.assertNotEqual(res.status_code, 500)

    def test_template_list_as_user_returns_only_can_answer(self):
        """
        Ton QuizTemplateViewSet.list :
          - admin => tous
          - user  => seulement ceux dont can_answer == True
        """
        self._auth(self.u1)

        res = self.client.get(self.template_list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Ici template est permanent+active => cananswer True => présent
        ids = [item["id"] for item in res.data]
        self.assertIn(self.qt.id, ids)

        # Template non répondable => non listé côté user
        qt2 = QuizTemplate.objects.create(title="T2", permanent=False, active=True, started_at=None)
        res2 = self.client.get(self.template_list_url)
        ids2 = [item["id"] for item in res2.data]
        self.assertNotIn(qt2.id, ids2)

    # ---------------------------------------------------------------------
    # Quiz create
    # ---------------------------------------------------------------------
    def test_quiz_create_requires_auth(self):
        res = self.client.post(self.quiz_list_url, {"quiz_template_id": self.qt.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_quiz_create_for_current_user(self):
        self._auth(self.u1)
        res = self.client.post(self.quiz_list_url, {"quiz_template_id": self.qt.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quiz_id = res.data["id"]
        quiz = Quiz.objects.get(pk=quiz_id)
        self.assertEqual(quiz.user_id, self.u1.id)
        self.assertEqual(quiz.quiz_template_id, self.qt.id)
        self.assertFalse(quiz.active)  # create() force active=False

    def test_quiz_create_for_other_user_requires_admin(self):
        self._auth(self.u1)
        res = self.client.post(
            self.quiz_list_url,
            {"quiz_template_id": self.qt.id, "user_id": self.u2.id},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.admin)
        res2 = self.client.post(
            self.quiz_list_url,
            {"quiz_template_id": self.qt.id, "user_id": self.u2.id},
            format="json",
        )
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res2.data["user"], self.u2.id)

    # ---------------------------------------------------------------------
    # Quiz start + permissions
    # ---------------------------------------------------------------------
    def test_quiz_start_by_owner(self):
        self._auth(self.u1)
        quiz = self._create_quiz_for(self.u1, active=False)

        url = reverse("api:quiz-api:quiz-start", kwargs={"quiz_id": quiz.id})
        res = self.client.post(url, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        quiz.refresh_from_db()
        self.assertTrue(quiz.active)
        self.assertIsNotNone(quiz.started_at)
        # ended_at auto calculée dans Quiz.save() si with_duration=True
        self.assertIsNotNone(quiz.ended_at)

    def test_quiz_start_forbidden_for_other_user(self):
        quiz = self._create_quiz_for(self.u1, active=False)
        url = reverse("api:quiz-api:quiz-start", kwargs={"quiz_id": quiz.id})

        self._auth(self.u2)
        res = self.client.post(url, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)  # via get_queryset() filtré

        self._auth(self.admin)
        res2 = self.client.post(url, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

    # ---------------------------------------------------------------------
    # Answers (nested) create/upsert
    # ---------------------------------------------------------------------
    def test_answer_create_by_question_order(self):
        self._auth(self.u1)
        quiz = self._create_quiz_for(self.u1, active=True)
        quiz.started_at = timezone.now()
        quiz.save()

        url = reverse("api:quiz-api:quiz-answer-list", kwargs={"quiz_id": quiz.id})
        payload = {
            "question_order": 1,
            "selected_options": [self.q1_o1.id],  # correct
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        a = QuizQuestionAnswer.objects.get(quiz=quiz, quizquestion=self.qq1)
        self.assertEqual(a.question_order, 1)
        self.assertEqual(list(a.selected_options.values_list("id", flat=True)), [self.q1_o1.id])

    def test_answer_create_by_question_id(self):
        self._auth(self.u1)
        quiz = self._create_quiz_for(self.u1, active=True)
        quiz.started_at = timezone.now()
        quiz.save()

        url = reverse("api:quiz-api:quiz-answer-list", kwargs={"quiz_id": quiz.id})
        payload = {"question_id": self.q2.id, "selected_options": [self.q2_o2.id]}  # wrong
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        a = QuizQuestionAnswer.objects.get(quiz=quiz, quizquestion=self.qq2)
        self.assertEqual(a.question_order, 2)

    def test_answer_upsert_same_question(self):
        self._auth(self.u1)
        quiz = self._create_quiz_for(self.u1, active=True)
        quiz.started_at = timezone.now()
        quiz.save()

        url = reverse("api:quiz-api:quiz-answer-list", kwargs={"quiz_id": quiz.id})

        # 1) first create wrong
        res1 = self.client.post(
            url, {"question_order": 1, "selected_options": [self.q1_o2.id]}, format="json"
        )
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # 2) upsert correct (update_or_create)
        res2 = self.client.post(
            url, {"question_order": 1, "selected_options": [self.q1_o1.id]}, format="json"
        )
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

        self.assertEqual(QuizQuestionAnswer.objects.filter(quiz=quiz, quizquestion=self.qq1).count(), 1)
        a = QuizQuestionAnswer.objects.get(quiz=quiz, quizquestion=self.qq1)
        self.assertEqual(list(a.selected_options.values_list("id", flat=True)), [self.q1_o1.id])

    def test_answer_create_requires_quiz_can_answer(self):
        """
        QuizQuestionAnswer.clean() empêche d'enregistrer si quiz.can_answer=False.
        """
        self._auth(self.u1)
        quiz = self._create_quiz_for(self.u1, active=False)  # can_answer False

        url = reverse("api:quiz-api:quiz-answer-list", kwargs={"quiz_id": quiz.id})
        res = self.client.post(url, {"question_order": 1, "selected_options": [self.q1_o1.id]}, format="json")

        # selon comment DRF remonte ValidationError -> 400
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------------------------------------------------------------------
    # Close quiz + scoring
    # ---------------------------------------------------------------------
    def test_quiz_close_computes_scores(self):
        self._auth(self.u1)
        quiz = self._create_quiz_for(self.u1, active=True)
        quiz.started_at = timezone.now()
        quiz.save()

        # Réponse Q1 correcte (weight=2), Q2 incorrecte (weight=3)
        a1 = QuizQuestionAnswer.objects.create(quiz=quiz, quizquestion=self.qq1, question_order=1)
        a1.selected_options.set([self.q1_o1])
        a2 = QuizQuestionAnswer.objects.create(quiz=quiz, quizquestion=self.qq2, question_order=2)
        a2.selected_options.set([self.q2_o2])  # wrong

        url = reverse("api:quiz-api:quiz-close", kwargs={"quiz_id": quiz.id})
        res = self.client.post(url, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # DB: close() fait bulk_update earned_score/max_score/is_correct
        a1.refresh_from_db()
        a2.refresh_from_db()
        self.assertTrue(a1.is_correct)
        self.assertEqual(a1.earned_score, 2.0)
        self.assertEqual(a1.max_score, 2.0)

        self.assertFalse(a2.is_correct)
        self.assertEqual(a2.earned_score, 0.0)
        self.assertEqual(a2.max_score, 3.0)

        quiz.refresh_from_db()
        self.assertFalse(quiz.active)
        self.assertIsNotNone(quiz.ended_at)

        # Serializer: pour MODE_EXAM, visibilité dépend du template
        # (par défaut dans ton modèle: IMMEDIATE => ok)
        self.assertEqual(res.data["earned_score"], 2.0)
        self.assertEqual(res.data["max_score"], 5.0)
        self.assertEqual(res.data["correct_answers"], 1)
        self.assertEqual(res.data["total_answers"], 2)

    def test_quiz_close_conflict_if_never_started(self):
        self._auth(self.u1)
        quiz = self._create_quiz_for(self.u1, active=True)
        # started_at None -> 409
        url = reverse("api:quiz-api:quiz-close", kwargs={"quiz_id": quiz.id})
        res = self.client.post(url, format="json")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_quiz_close_conflict_if_already_closed(self):
        self._auth(self.u1)
        quiz = self._create_quiz_for(self.u1, active=False)
        quiz.started_at = timezone.now()
        quiz.ended_at = timezone.now()
        quiz.save()
        url = reverse("api:quiz-api:quiz-close", kwargs={"quiz_id": quiz.id})
        res = self.client.post(url, format="json")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)


class QuizTemplateViewSetAPITestCase(APITestCase):
    """
    Couvre:
      - permissions: list/retrieve + generate_from_subjects => IsAuthenticated
                    CRUD + add/update/delete question       => IsAdminUser
      - list() : admin voit tout, user voit seulement can_answer True
      - retrieve()
      - create/update/patch/delete
      - generate_from_subjects()
      - add_question(), update_question(), delete_question()
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="adminpass", is_staff=True, is_superuser=True
        )
        self.u1 = User.objects.create_user(username="u1", password="u1pass")

        # Subjects
        self.subj1 = Subject.objects.create(name="Physique", slug="physique")
        self.subj2 = Subject.objects.create(name="Math", slug="math")

        # Questions actives liées à des subjects
        self.q1 = self._create_question("Q1", subject=self.subj1, active=True)
        self.q2 = self._create_question("Q2", subject=self.subj1, active=True)
        self.q3 = self._create_question("Q3", subject=self.subj2, active=True)
        self.q_inactive = self._create_question("Q4", subject=self.subj1, active=False)

        # Templates :
        # - qt_ok : can_answer True (permanent=True + active=True)
        # - qt_no : can_answer False (active=False)
        self.qt_ok = QuizTemplate.objects.create(
            title="Template OK",
            mode=QuizTemplate.MODE_EXAM,
            permanent=True,
            active=True,
            max_questions=10,
        )
        self.qt_no = QuizTemplate.objects.create(
            title="Template NO",
            mode=QuizTemplate.MODE_EXAM,
            permanent=True,
            active=False,
            max_questions=10,
        )

        # Routes (adapte si besoin)
        self.template_list_url = reverse("api:quiz-api:quiz-template-list")  # /api/quiz/template/
        self.template_detail_url = lambda qt_id: reverse("api:quiz-api:quiz-template-detail", kwargs={"qt_id": qt_id})
        self.generate_url = reverse(
            "api:quiz-api:quiz-template-generate-from-subjects")  # /api/quiz/template/generate-from-subjects/

        # actions custom sur template detail
        self.add_question_url = lambda qt_id: reverse("api:quiz-api:quiz-template-add-question",
                                                      kwargs={"qt_id": qt_id})  # /{id}/question/
        self.update_question_url = lambda qt_id, qq_id: reverse(
            "api:quiz-api:quiz-template-update-question", kwargs={"qt_id": qt_id, "qq_id": qq_id}
        )
        self.delete_question_url = lambda qt_id, qq_id: reverse(
            "api:quiz-api:quiz-template-delete-question", kwargs={"qt_id": qt_id, "qq_id": qq_id}
        )

    # --------------------
    # Helpers
    # --------------------
    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _create_question(self, title: str, *, subject: Subject, active=True) -> Question:
        q = Question.objects.create(
            title=title,
            description="desc",
            explanation="expl",
            allow_multiple_correct=False,
            active=active,
            is_mode_practice=True,
            is_mode_exam=True,
        )
        q.subjects.add(subject)
        AnswerOption.objects.create(question=q, content="A", is_correct=True, sort_order=1)
        AnswerOption.objects.create(question=q, content="B", is_correct=False, sort_order=2)
        return q

    # ==========================================================
    # Permissions: list/retrieve
    # ==========================================================
    def test_list_requires_auth(self):
        res = self.client.get(self.template_list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_requires_auth(self):
        res = self.client.get(self.template_detail_url(self.qt_ok.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # ==========================================================
    # list(): admin voit tout / user voit seulement can_answer
    # ==========================================================
    def test_list_as_admin_returns_all(self):
        self._auth(self.admin)
        res = self.client.get(self.template_list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        items = res.data.get("results") if isinstance(res.data, dict) else res.data
        ids = {it["id"] for it in items}
        self.assertIn(self.qt_ok.id, ids)
        self.assertIn(self.qt_no.id, ids)

    def test_list_as_user_filters_can_answer(self):
        self._auth(self.u1)
        res = self.client.get(self.template_list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        items = res.data.get("results") if isinstance(res.data, dict) else res.data
        ids = {it["id"] for it in items}
        self.assertIn(self.qt_ok.id, ids)
        self.assertNotIn(self.qt_no.id, ids)

    # ==========================================================
    # CRUD : admin only
    # ==========================================================
    def test_create_requires_admin(self):
        payload = {"title": "New Template", "mode": QuizTemplate.MODE_EXAM, "max_questions": 5, "permanent": True}
        self._auth(self.u1)
        res = self.client.post(self.template_list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.admin)
        res2 = self.client.post(self.template_list_url, payload, format="json")
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

    def test_update_requires_admin(self):
        payload = {"title": "Template OK UPDATED"}
        self._auth(self.u1)
        res = self.client.put(self.template_detail_url(self.qt_ok.id), payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.admin)
        # PUT complet: selon ton serializer tu peux devoir fournir plus de champs.
        # On fait PATCH pour rester robuste.
        res2 = self.client.patch(self.template_detail_url(self.qt_ok.id), payload, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        self.qt_ok.refresh_from_db()
        self.assertEqual(self.qt_ok.title, "Template OK UPDATED")

    def test_delete_requires_admin(self):
        self._auth(self.u1)
        res = self.client.delete(self.template_detail_url(self.qt_ok.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.admin)
        res2 = self.client.delete(self.template_detail_url(self.qt_ok.id))
        self.assertEqual(res2.status_code, status.HTTP_204_NO_CONTENT)

    # ==========================================================
    # generate_from_subjects : IsAuthenticated
    # ==========================================================
    def test_generate_from_subjects_requires_auth(self):
        res = self.client.post(self.generate_url, {"title": "Gen", "subject_ids": [self.subj1.id]}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_generate_from_subjects_happy_path(self):
        self._auth(self.u1)
        payload = {"title": "Gen Physique", "subject_ids": [self.subj1.id], "max_questions": 2}
        res = self.client.post(self.generate_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)

        qt_id = res.data["id"]
        qt = QuizTemplate.objects.get(pk=qt_id)
        self.assertEqual(qt.title, "Gen Physique")
        self.assertEqual(qt.max_questions, 2)

        # vérifie qu'il y a bien des QuizQuestions créées
        self.assertEqual(qt.quiz_questions.count(), 2)

        # vérifie que seules questions actives prises (q_inactive exclue)
        picked_question_ids = set(qt.quiz_questions.values_list("question_id", flat=True))
        self.assertNotIn(self.q_inactive.id, picked_question_ids)

    def test_generate_from_subjects_missing_title_returns_400(self):
        self._auth(self.u1)
        res = self.client.post(self.generate_url, {"subject_ids": [self.subj1.id]}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_from_subjects_empty_subject_ids_returns_400(self):
        self._auth(self.u1)
        res = self.client.post(self.generate_url, {"title": "Gen", "subject_ids": []}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_from_subjects_no_questions_returns_400(self):
        self._auth(self.u1)
        # subj2 a q3 active => on crée un subj sans question
        subj_empty = Subject.objects.create(name="Vide", slug="vide")
        res = self.client.post(
            self.generate_url,
            {"title": "Gen vide", "subject_ids": [subj_empty.id]},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ==========================================================
    # add_question / update_question / delete_question : admin only
    # ==========================================================
    def test_add_question_requires_admin(self):
        self._auth(self.u1)
        res = self.client.post(self.add_question_url(self.qt_ok.id), {"question_id": self.q1.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_update_delete_question_happy_path(self):
        self._auth(self.admin)
        res = self.client.post(
            self.add_question_url(self.qt_ok.id),
            {"question_id": self.q1.id, "sort_order": 1, "weight": 2},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        qq_id = res.data["id"]
        qq = QuizQuestion.objects.get(pk=qq_id)
        self.assertEqual(qq.quiz_id, self.qt_ok.id)
        self.assertEqual(qq.question_id, self.q1.id)
        self.assertEqual(qq.sort_order, 1)
        self.assertEqual(qq.weight, 2)
        # update_question (PATCH)
        res2 = self.client.patch(
            self.update_question_url(self.qt_ok.id, qq_id),
            {"weight": 5},
            format="json",
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK, res2.data)

        qq.refresh_from_db()
        self.assertEqual(qq.weight, 5)

        # delete_question
        res3 = self.client.delete(self.delete_question_url(self.qt_ok.id, qq_id))
        self.assertEqual(res3.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(QuizQuestion.objects.filter(pk=qq_id).exists())

    def test_update_question_returns_404_if_quizquestion_not_in_template(self):
        self._auth(self.admin)

        other_qt = QuizTemplate.objects.create(title="Other", permanent=True, active=True)
        other_qq = QuizQuestion.objects.create(quiz=other_qt, question=self.q2, sort_order=1, weight=1)

        # on tente update via qt_ok mais qq appartient à other_qt
        res = self.client.patch(
            self.update_question_url(self.qt_ok.id, other_qq.id),
            {"weight": 99},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_question_returns_404_if_missing(self):
        self._auth(self.admin)
        res = self.client.delete(self.delete_question_url(self.qt_ok.id, 999999))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
