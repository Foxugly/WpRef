# wpref/quiz/tests/test_views_api.py
from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from question.models import Question, AnswerOption
from quiz.models import QuizTemplate, QuizQuestion, Quiz, QuizQuestionAnswer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
from subject.models import Subject

from quiz.views import QuizTemplateQuizQuestionViewSet, QuizQuestionAnswerViewSet, QuizViewSet

User = get_user_model()


class _ReverseMixin:
    """
    Helper: reverse robuste si tu changes ton app_name/namespace.
    Garde UNIQUEMENT le nom qui marche chez toi, et supprime les autres.
    """

    def _rev(self, *candidates: str, **kwargs):
        last = None
        for name in candidates:
            try:
                return reverse(name, kwargs=kwargs)
            except Exception as e:  # noqa
                last = e
        raise last  # type: ignore[misc]


class QuizViewsAPITestCase(_ReverseMixin, APITestCase):
    """
    Couvre:
      - QuizTemplateViewSet (CRUD + generate_from_subjects + question CRUD custom)
      - QuizTemplateQuizQuestionViewSet (nested /template/{pk}/question/)
      - QuizViewSet (CRUD + create + bulk + start + close)
      - QuizQuestionAnswerViewSet (nested /quiz/{quiz_pk}/answer/)
    """

    # ---------------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------------
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="adminpass", is_staff=True, is_superuser=True
        )
        self.staff = User.objects.create_user(
            username="staff", password="staffpass", is_staff=True, is_superuser=False
        )
        self.u1 = User.objects.create_user(username="u1", password="u1pass")
        self.u2 = User.objects.create_user(username="u2", password="u2pass")

        self.subj1 = Subject.objects.create(name="Math")
        self.subj2 = Subject.objects.create(name="History")

        self.q1 = self._make_question("Q1", subjects=[self.subj1], active=True)
        self.q2 = self._make_question("Q2", subjects=[self.subj2], active=True)
        self.q3_inactive = self._make_question("Q3", subjects=[self.subj1], active=False)

        # Template "répondable"
        self.qt_ok = QuizTemplate.objects.create(title="T_OK", permanent=True, active=True, max_questions=10)
        self.qq1 = QuizQuestion.objects.create(quiz=self.qt_ok, question=self.q1, sort_order=1, weight=1)
        self.qq2 = QuizQuestion.objects.create(quiz=self.qt_ok, question=self.q2, sort_order=2, weight=2)

        # Template "non répondable" (active=False => can_answer False)
        self.qt_no = QuizTemplate.objects.create(title="T_NO", permanent=True, active=False, max_questions=10)

        # URLs (candidates)
        self.qt_list_url = self._rev(
            "api:quiz_api:quiz-template-list",
            "api:quiz-api:quiz-template-list",
            "quiz_api:quiz-template-list",
            "quiz-api:quiz-template-list",
        )
        self.quiz_list_url = self._rev(
            "api:quiz_api:quiz-list",
            "api:quiz-api:quiz-list",
            "quiz_api:quiz-list",
            "quiz-api:quiz-list",
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _make_question(self, title: str, subjects=None, active=True) -> Question:
        subjects = subjects or []
        q = Question.objects.create(
            title=title,
            description="desc",
            explanation="expl",
            allow_multiple_correct=False,
            active=active,
            is_mode_practice=True,
            is_mode_exam=True,
        )
        if subjects:
            q.subjects.set(subjects)

        # 2 options minimum + 1 correcte (sinon ton clean() serait invalide si full_clean appelé)
        AnswerOption.objects.create(question=q, content="A", is_correct=True, sort_order=1)
        AnswerOption.objects.create(question=q, content="B", is_correct=False, sort_order=2)
        return q

    # ---------------------------------------------------------------------
    # QuizTemplateViewSet: permissions + list filtering
    # ---------------------------------------------------------------------
    def test_quiztemplate_list_requires_auth(self):
        res = self.client.get(self.qt_list_url)
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_quiztemplate_list_as_user_filters_can_answer(self):
        self._auth(self.u1)
        res = self.client.get(self.qt_list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get("results") if isinstance(res.data, dict) else res.data
        ids = [x["id"] for x in data]
        self.assertIn(self.qt_ok.id, ids)
        self.assertNotIn(self.qt_no.id, ids)

    def test_quiztemplate_list_as_admin_returns_all(self):
        self._auth(self.admin)
        res = self.client.get(self.qt_list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get("results") if isinstance(res.data, dict) else res.data
        ids = [x["id"] for x in data]
        self.assertIn(self.qt_ok.id, ids)
        self.assertIn(self.qt_no.id, ids)

    def test_quiztemplate_create_requires_admin(self):
        payload = {"title": "NEW_T", "permanent": True, "active": True, "max_questions": 5}

        self._auth(self.u1)
        res = self.client.post(self.qt_list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.admin)
        res2 = self.client.post(self.qt_list_url, payload, format="json")
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

    def test_quiztemplate_retrieve_requires_auth(self):
        detail_url = self._rev(
            "api:quiz_api:quiz-template-detail",
            "api:quiz-api:quiz-template-detail",
            "quiz_api:quiz-template-detail",
            "quiz-api:quiz-template-detail",
            qt_id=self.qt_ok.id,
        )
        res = self.client.get(detail_url)
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        self._auth(self.u1)
        res2 = self.client.get(detail_url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

    def test_quiztemplate_update_requires_admin(self):
        detail_url = self._rev(
            "api:quiz_api:quiz-template-detail",
            "api:quiz-api:quiz-template-detail",
            "quiz_api:quiz-template-detail",
            "quiz-api:quiz-template-detail",
            qt_id=self.qt_ok.id,
        )

        self._auth(self.u1)
        res = self.client.put(detail_url, {"title": "X", "permanent": True, "active": True, "max_questions": 10},
                              format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.admin)
        res2 = self.client.patch(detail_url, {"description": "hello"}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

    def test_quiztemplate_destroy_requires_admin(self):
        qt = QuizTemplate.objects.create(title="T_DEL", permanent=True, active=True, max_questions=1)
        detail_url = self._rev(
            "api:quiz_api:quiz-template-detail",
            "api:quiz-api:quiz-template-detail",
            "quiz_api:quiz-template-detail",
            "quiz-api:quiz-template-detail",
            qt_id=qt.id,
        )

        self._auth(self.u1)
        res = self.client.delete(detail_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.admin)
        res2 = self.client.delete(detail_url)
        self.assertEqual(res2.status_code, status.HTTP_204_NO_CONTENT)

    # ---------------------------------------------------------------------
    # QuizTemplateViewSet: generate_from_subjects
    # ---------------------------------------------------------------------
    def test_generate_from_subjects_requires_auth(self):
        url = self._rev(
            "api:quiz_api:quiz-template-generate-from-subjects",
            "api:quiz-api:quiz-template-generate-from-subjects",
            "quiz_api:quiz-template-generate-from-subjects",
            "quiz-api:quiz-template-generate-from-subjects",
        )
        res = self.client.post(url, {"title": "X", "subject_ids": [self.subj1.id]}, format="json")
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_generate_from_subjects_missing_title_400(self):
        self._auth(self.u1)
        url = self._rev(
            "api:quiz_api:quiz-template-generate-from-subjects",
            "api:quiz-api:quiz-template-generate-from-subjects",
            "quiz_api:quiz-template-generate-from-subjects",
            "quiz-api:quiz-template-generate-from-subjects",
        )
        res = self.client.post(url, {"subject_ids": [self.subj1.id]}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_from_subjects_invalid_subject_ids_400(self):
        self._auth(self.u1)
        url = self._rev(
            "api:quiz_api:quiz-template-generate-from-subjects",
            "api:quiz-api:quiz-template-generate-from-subjects",
            "quiz_api:quiz-template-generate-from-subjects",
            "quiz-api:quiz-template-generate-from-subjects",
        )
        res = self.client.post(url, {"title": "X", "subject_ids": "nope"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_from_subjects_no_questions_400(self):
        self._auth(self.u1)
        subj_empty = Subject.objects.create(name="Empty")
        url = self._rev(
            "api:quiz_api:quiz-template-generate-from-subjects",
            "api:quiz-api:quiz-template-generate-from-subjects",
            "quiz_api:quiz-template-generate-from-subjects",
            "quiz-api:quiz-template-generate-from-subjects",
        )
        res = self.client.post(url, {"title": "X", "subject_ids": [subj_empty.id]}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_from_subjects_happy_path_201_creates_template_and_quizquestions(self):
        self._auth(self.u1)
        url = self._rev(
            "api:quiz_api:quiz-template-generate-from-subjects",
            "api:quiz-api:quiz-template-generate-from-subjects",
            "quiz_api:quiz-template-generate-from-subjects",
            "quiz-api:quiz-template-generate-from-subjects",
        )
        res = self.client.post(
            url,
            {"title": "GEN", "subject_ids": [self.subj1.id, self.subj2.id], "max_questions": 2},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        qt_id = res.data["id"]
        qt = QuizTemplate.objects.get(pk=qt_id)
        self.assertEqual(qt.quiz_questions.count(), 2)

    # ---------------------------------------------------------------------
    # QuizTemplateViewSet: add/update/delete question via custom actions
    # ---------------------------------------------------------------------
    def test_add_question_requires_admin(self):
        url = self._rev(
            "api:quiz_api:quiz-template-add-question",
            "api:quiz-api:quiz-template-add-question",
            "quiz_api:quiz-template-add-question",
            "quiz-api:quiz-template-add-question",
            qt_id=self.qt_ok.id,
        )
        payload = {"question_id": self.q1.id, "sort_order": 10, "weight": 1}

        self._auth(self.u1)
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.admin)
        # q1 déjà dans template => ValidationError attendue (400)
        res2 = self.client.post(url, payload, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

        # ajout d'une vraie nouvelle question
        q_new = self._make_question("Q_NEW", subjects=[self.subj1], active=True)
        res3 = self.client.post(url, {"question_id": q_new.id, "sort_order": 99, "weight": 3}, format="json")
        self.assertEqual(res3.status_code, status.HTTP_201_CREATED)

    def test_update_question_custom_action_patch(self):
        url = self._rev(
            "api:quiz_api:quiz-template-update-question",
            "api:quiz-api:quiz-template-update-question",
            "quiz_api:quiz-template-update-question",
            "quiz-api:quiz-template-update-question",
            qt_id=self.qt_ok.id,
            qq_id=self.qq1.id,
        )
        self._auth(self.admin)
        res = self.client.patch(url, {"weight": 5}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.qq1.refresh_from_db()
        self.assertEqual(self.qq1.weight, 5)

    def test_update_question_custom_action_404_if_not_in_template(self):
        other_qt = QuizTemplate.objects.create(title="OTHER_T", permanent=True, active=True, max_questions=10)
        other_qq = QuizQuestion.objects.create(quiz=other_qt, question=self.q1, sort_order=1, weight=1)

        url = self._rev(
            "api:quiz_api:quiz-template-update-question",
            "api:quiz-api:quiz-template-update-question",
            "quiz_api:quiz-template-update-question",
            "quiz-api:quiz-template-update-question",
            qt_id=self.qt_ok.id,
            qq_id=other_qq.id,
        )
        self._auth(self.admin)
        res = self.client.patch(url, {"weight": 2}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_question_custom_action(self):
        url = self._rev(
            "api:quiz_api:quiz-template-delete-question",
            "api:quiz-api:quiz-template-delete-question",
            "quiz_api:quiz-template-delete-question",
            "quiz-api:quiz-template-delete-question",
            qt_id=self.qt_ok.id,
            qq_id=self.qq2.id,
        )
        self._auth(self.admin)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(QuizQuestion.objects.filter(pk=self.qq2.id).exists())

    # ---------------------------------------------------------------------
    # QuizTemplateQuizQuestionViewSet (nested): /template/{quiz_template_pk}/question/
    # ---------------------------------------------------------------------
    def test_nested_quizquestion_crud_admin_only(self):
        list_url = self._rev(
            "api:quiz_api:quiz-template-question-list",
            "api:quiz-api:quiz-template-question-list",
            "quiz_api:quiz-template-question-list",
            "quiz-api:quiz-template-question-list",
            qt_id=self.qt_ok.id,
        )

        self._auth(self.u1)
        res = self.client.get(list_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.admin)
        res2 = self.client.get(list_url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        # create
        q_new = self._make_question("Q_NEST", subjects=[self.subj1], active=True)
        res3 = self.client.post(list_url, {"question_id": q_new.id, "sort_order": 5, "weight": 2}, format="json")
        self.assertEqual(res3.status_code, status.HTTP_201_CREATED)
        created_id = res3.data["id"]

        # retrieve
        detail_url = self._rev(
            "api:quiz_api:quiz-template-question-detail",
            "api:quiz-api:quiz-template-question-detail",
            "quiz_api:quiz-template-question-detail",
            "quiz-api:quiz-template-question-detail",
            qt_id=self.qt_ok.id,
            qq_id=created_id,
        )
        res4 = self.client.get(detail_url)
        self.assertEqual(res4.status_code, status.HTTP_200_OK)

        # update (PUT)
        res5 = self.client.put(detail_url, {"question_id": q_new.id, "sort_order": 7, "weight": 9}, format="json")
        self.assertEqual(res5.status_code, status.HTTP_200_OK)

        # patch
        res6 = self.client.patch(detail_url, {"weight": 1}, format="json")
        self.assertEqual(res6.status_code, status.HTTP_200_OK)

        # delete
        res7 = self.client.delete(detail_url)
        self.assertEqual(res7.status_code, status.HTTP_204_NO_CONTENT)

    # ---------------------------------------------------------------------
    # QuizViewSet: list/retrieve filtering + create logic
    # ---------------------------------------------------------------------
    def _create_quiz(self, qt: QuizTemplate, user: User, active=False, started_at=None, ended_at=None) -> Quiz:
        return Quiz.objects.create(
            quiz_template=qt,
            user=user,
            active=active,
            started_at=started_at,
            ended_at=ended_at,
        )

    def test_quiz_list_filters_owner_for_non_staff(self):
        quiz_u1 = self._create_quiz(self.qt_ok, self.u1)
        quiz_u2 = self._create_quiz(self.qt_ok, self.u2)

        self._auth(self.u1)
        res = self.client.get(self.quiz_list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data
        ids = [x["id"] for x in data]
        self.assertIn(quiz_u1.id, ids)
        self.assertNotIn(quiz_u2.id, ids)

        self._auth(self.staff)
        res2 = self.client.get(self.quiz_list_url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        data2 = res2.data
        ids2 = [x["id"] for x in data2]
        self.assertIn(quiz_u1.id, ids2)
        self.assertIn(quiz_u2.id, ids2)

    def test_quiz_create_missing_template_id_400(self):
        self._auth(self.u1)
        res = self.client.post(self.quiz_list_url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quiz_create_template_not_found_404(self):
        self._auth(self.u1)
        res = self.client.post(self.quiz_list_url, {"quiz_template_id": 999999}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_quiz_create_template_not_available_400(self):
        self._auth(self.u1)
        res = self.client.post(self.quiz_list_url, {"quiz_template_id": self.qt_no.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quiz_create_for_other_user_forbidden_if_not_admin(self):
        self._auth(self.u1)
        res = self.client.post(
            self.quiz_list_url,
            {"quiz_template_id": self.qt_ok.id, "user_id": self.u2.id},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_quiz_create_for_other_user_allowed_for_admin(self):
        self._auth(self.admin)
        res = self.client.post(
            self.quiz_list_url,
            {"quiz_template_id": self.qt_ok.id, "user_id": self.u2.id},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["user"], self.u2.id)

    # ---------------------------------------------------------------------
    # QuizViewSet: bulk_create_from_template (admin only)
    # ---------------------------------------------------------------------
    def test_bulk_create_from_template_admin_only(self):
        url = self._rev(
            "api:quiz_api:quiz-bulk-create-from-template",
            "api:quiz-api:quiz-bulk-create-from-template",
            "quiz_api:quiz-bulk-create-from-template",
            "quiz-api:quiz-bulk-create-from-template",
        )
        payload = {"quiz_template_id": self.qt_ok.id, "user_ids": [self.u1.id, self.u2.id]}

        self._auth(self.u1)
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.admin)
        res2 = self.client.post(url, payload, format="json")
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(res2.data), 2)

    # ---------------------------------------------------------------------
    # QuizViewSet: start / close
    # ---------------------------------------------------------------------
    def test_start_quiz_sets_started_at_and_active(self):
        quiz = self._create_quiz(self.qt_ok, self.u1, active=False, started_at=None)

        url = self._rev(
            "api:quiz_api:quiz-start",
            "api:quiz-api:quiz-start",
            "quiz_api:quiz-start",
            "quiz-api:quiz-start",
            quiz_id=quiz.id,
        )
        self._auth(self.u1)
        res = self.client.post(url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        quiz.refresh_from_db()
        self.assertTrue(quiz.active)
        self.assertIsNotNone(quiz.started_at)

    def test_start_quiz_returns_400_if_template_not_available(self):
        quiz = self._create_quiz(self.qt_no, self.u1, active=False, started_at=None)

        url = self._rev(
            "api:quiz_api:quiz-start",
            "api:quiz-api:quiz-start",
            "quiz_api:quiz-start",
            "quiz-api:quiz-start",
            quiz_id=quiz.id,
        )
        self._auth(self.u1)
        res = self.client.post(url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def _make_answer(self, quiz: Quiz, qq: QuizQuestion, selected_correct=True, order=1) -> QuizQuestionAnswer:
        ans = QuizQuestionAnswer.objects.create(
            quiz=quiz,
            quizquestion=qq,
            question_order=order,
            given_answer="x",
        )
        correct_opts = list(qq.question.answer_options.filter(is_correct=True))
        wrong_opts = list(qq.question.answer_options.filter(is_correct=False))
        if selected_correct and correct_opts:
            ans.selected_options.set(correct_opts)
        elif wrong_opts:
            ans.selected_options.set([wrong_opts[0]])
        return ans

    def test_close_quiz_409_if_never_started(self):
        quiz = self._create_quiz(self.qt_ok, self.u1, active=True, started_at=None)

        url = self._rev(
            "api:quiz_api:quiz-close",
            "api:quiz-api:quiz-close",
            "quiz_api:quiz-close",
            "quiz-api:quiz-close",
            quiz_id=quiz.id,
        )
        self._auth(self.u1)
        res = self.client.post(url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_close_quiz_409_if_already_closed(self):
        quiz = self._create_quiz(self.qt_ok, self.u1, active=False, started_at=timezone.now())

        url = self._rev(
            "api:quiz_api:quiz-close",
            "api:quiz-api:quiz-close",
            "quiz_api:quiz-close",
            "quiz-api:quiz-close",
            quiz_id=quiz.id,
        )
        self._auth(self.u1)
        res = self.client.post(url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_close_quiz_computes_scores_and_deactivates(self):
        quiz = self._create_quiz(self.qt_ok, self.u1, active=True, started_at=timezone.now())
        # réponses : qq1 (weight=1) correct, qq2 (weight=2) wrong
        self._make_answer(quiz, self.qq1, selected_correct=True, order=1)
        self._make_answer(quiz, self.qq2, selected_correct=False, order=2)

        url = self._rev(
            "api:quiz_api:quiz-close",
            "api:quiz-api:quiz-close",
            "quiz_api:quiz-close",
            "quiz-api:quiz-close",
            quiz_id=quiz.id,
        )
        self._auth(self.u1)
        res = self.client.post(url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        quiz.refresh_from_db()
        self.assertFalse(quiz.active)
        self.assertIsNotNone(quiz.ended_at)

        a1 = QuizQuestionAnswer.objects.get(quiz=quiz, quizquestion=self.qq1)
        a2 = QuizQuestionAnswer.objects.get(quiz=quiz, quizquestion=self.qq2)

        self.assertEqual(float(a1.max_score), 1.0)
        self.assertEqual(float(a1.earned_score), 1.0)
        self.assertTrue(a1.is_correct)

        self.assertEqual(float(a2.max_score), 2.0)
        self.assertEqual(float(a2.earned_score), 0.0)
        self.assertFalse(a2.is_correct)

    # ---------------------------------------------------------------------
    # QuizQuestionAnswerViewSet (nested): /quiz/{quiz_pk}/answer/
    # ---------------------------------------------------------------------
    def _answers_list_url(self, quiz: Quiz):
        return self._rev(
            "api:quiz_api:quiz-answer-list",
            "api:quiz-api:quiz-answer-list",
            "quiz_api:quiz-answer-list",
            "quiz-api:quiz-answer-list",
            quiz_id=quiz.id,
        )

    def _answers_detail_url(self, quiz: Quiz, answer_id: int):
        return self._rev(
            "api:quiz_api:quiz-answer-detail",
            "api:quiz-api:quiz-answer-detail",
            "quiz_api:quiz-answer-detail",
            "quiz-api:quiz-answer-detail",
            quiz_id=quiz.id,
            answer_id=answer_id,
        )

    def test_answers_list_only_owner_unless_staff(self):
        quiz_u1 = self._create_quiz(self.qt_ok, self.u1, active=True, started_at=timezone.now())
        quiz_u2 = self._create_quiz(self.qt_ok, self.u2, active=True, started_at=timezone.now())

        a1 = self._make_answer(quiz_u1, self.qq1, True, 1)
        self._make_answer(quiz_u2, self.qq1, True, 1)

        self._auth(self.u1)
        res = self.client.get(self._answers_list_url(quiz_u1))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get("results") if isinstance(res.data, dict) else res.data
        ids = [x["id"] for x in data]
        self.assertIn(a1.id, ids)

        # u1 ne peut pas lister answers d'un quiz qui ne lui appartient pas -> 404 (get_quiz filtre)
        res2 = self.client.get(self._answers_list_url(quiz_u2))
        self.assertEqual(res2.status_code, status.HTTP_404_NOT_FOUND)

        # staff peut
        self._auth(self.staff)
        res3 = self.client.get(self._answers_list_url(quiz_u2))
        self.assertEqual(res3.status_code, status.HTTP_200_OK)

    def test_answer_create_update_patch_delete(self):
        quiz = self._create_quiz(self.qt_ok, self.u1, active=True, started_at=timezone.now())

        self._auth(self.u1)
        list_url = self._answers_list_url(quiz)

        # create (write serializer)
        payload = {
            # adapte selon ton QuizQuestionAnswerWriteSerializer:
            # typiquement quizquestion_id / question_order / selected_options...
            "quizquestion_id": self.qq1.id,
            "question_order": 1,
            "selected_options": [self.qq1.question.answer_options.filter(is_correct=True).first().id],
        }
        res = self.client.post(list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ans_id = res.data["id"]

        # update (PUT) -> modif selected
        detail_url = self._answers_detail_url(quiz, ans_id)
        wrong = self.qq1.question.answer_options.filter(is_correct=False).first()
        res2 = self.client.put(detail_url, {
            "quizquestion_id": self.qq1.id,
            "question_order": 1,
            "selected_option_ids": [wrong.id] if wrong else [],
        }, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        # patch
        res3 = self.client.patch(detail_url, {"given_answer": "free text"}, format="json")
        self.assertEqual(res3.status_code, status.HTTP_200_OK)

        # delete
        res4 = self.client.delete(detail_url)
        self.assertEqual(res4.status_code, status.HTTP_204_NO_CONTENT)

    # ---------------------------------------------------------------------
    # QuizTemplateViewSet: list -> branche "page is not None"
    # ---------------------------------------------------------------------
    def test_quiztemplate_list_as_user_pagination_branch_page_not_none(self):
        """
        Force la branche:
            page = self.paginate_queryset(qs)
            if page is not None: ...
        Même si ta pagination DRF n'est pas activée globalement.
        """
        self._auth(self.u1)

        # On force paginate_queryset() à renvoyer une "page"
        with patch("quiz.views.QuizTemplateViewSet.paginate_queryset", return_value=[self.qt_ok]) as _pg, \
             patch("quiz.views.QuizTemplateViewSet.get_paginated_response",
                   side_effect=lambda data: Response({"results": data})) as _gpr:

            res = self.client.get(self.qt_list_url)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn("results", res.data)
            ids = [x["id"] for x in res.data["results"]]
            self.assertIn(self.qt_ok.id, ids)

    # ---------------------------------------------------------------------
    # QuizTemplateViewSet: generate_from_subjects -> branche "if not questions_qs.exists()"
    # ---------------------------------------------------------------------
    def test_generate_from_subjects_questions_qs_exists_false_400(self):
        """
        Cette branche est très difficile à atteindre "naturellement" car ids vient de la DB,
        puis questions_qs = Question.objects.filter(id__in=picked_ids).
        Donc on simule le cas via mocks:
          - 1er filter(...subjects__id__in=...) renvoie ids non vides
          - 2e filter(id__in=...) renvoie un queryset dont exists() est False
        """
        self._auth(self.u1)

        url = self._rev(
            "api:quiz_api:quiz-template-generate-from-subjects",
            "api:quiz-api:quiz-template-generate-from-subjects",
            "quiz_api:quiz-template-generate-from-subjects",
            "quiz-api:quiz-template-generate-from-subjects",
        )

        # Mock QS #1 (celui qui produit ids)
        qs1 = MagicMock()
        qs1.distinct.return_value = qs1
        qs1.values_list.return_value = [self.q1.id]  # ids non vides

        # Mock QS #2 (questions_qs) -> exists False
        qs2 = MagicMock()
        qs2.exists.return_value = False

        # Question.objects.filter est appelé 2 fois dans la vue
        with patch("quiz.views.Question.objects.filter", side_effect=[qs1, qs2]):
            res = self.client.post(url, {"title": "GENX", "subject_ids": [self.subj1.id]}, format="json")
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("detail", res.data)

    # ---------------------------------------------------------------------
    # QuizTemplateQuizQuestionViewSet: get_queryset -> 2 retours .none()
    # ---------------------------------------------------------------------
    def test_templatequizquestion_get_queryset_swagger_fake_view_returns_none(self):

        view = QuizTemplateQuizQuestionViewSet()
        view.swagger_fake_view = True
        view.kwargs = {"qt_id": self.qt_ok.id}

        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    def test_templatequizquestion_get_queryset_missing_qt_id_returns_none(self):

        view = QuizTemplateQuizQuestionViewSet()
        view.swagger_fake_view = False
        view.kwargs = {}  # pas de qt_id

        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    # ---------------------------------------------------------------------
    # QuizViewSet: get_queryset swagger_fake_view -> return Quiz.objects.none()
    # ---------------------------------------------------------------------
    def test_quiz_get_queryset_swagger_fake_view_returns_none(self):
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        req = factory.get("/api/quiz/")
        req.user = self.admin

        view = QuizViewSet()
        view.swagger_fake_view = True
        view.request = req

        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    # ---------------------------------------------------------------------
    # QuizViewSet: update / partial_update / destroy
    # ---------------------------------------------------------------------
    def test_quiz_update_put(self):
        quiz = self._create_quiz(self.qt_ok, self.u1, active=False, started_at=None, ended_at=None)
        url = self._rev(
            "api:quiz_api:quiz-detail",
            "api:quiz-api:quiz-detail",
            "quiz_api:quiz-detail",
            "quiz-api:quiz-detail",
            quiz_id=quiz.id,
        )

        self._auth(self.u1)
        payload = {
            "quiz_template": self.qt_ok.id,
            "active": False,
            "started_at": None,
            "ended_at": None,
        }
        res = self.client.put(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_quiz_partial_update_patch(self):
        quiz = self._create_quiz(self.qt_ok, self.u1, active=False, started_at=None, ended_at=None)
        url = self._rev(
            "api:quiz_api:quiz-detail",
            "api:quiz-api:quiz-detail",
            "quiz_api:quiz-detail",
            "quiz-api:quiz-detail",
            quiz_id=quiz.id,
        )

        self._auth(self.u1)
        res = self.client.patch(url, {"active": True}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        quiz.refresh_from_db()
        self.assertTrue(quiz.active)

    def test_quiz_destroy(self):
        quiz = self._create_quiz(self.qt_ok, self.u1)
        url = self._rev(
            "api:quiz_api:quiz-detail",
            "api:quiz-api:quiz-detail",
            "quiz_api:quiz-detail",
            "quiz-api:quiz-detail",
            quiz_id=quiz.id,
        )

        self._auth(self.u1)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(pk=quiz.id).exists())

    # ---------------------------------------------------------------------
    # QuizViewSet: bulk_create_from_template -> invalid input + except (template not found)
    # ---------------------------------------------------------------------
    def test_bulk_create_from_template_invalid_input_400(self):
        url = self._rev(
            "api:quiz_api:quiz-bulk-create-from-template",
            "api:quiz-api:quiz-bulk-create-from-template",
            "quiz_api:quiz-bulk-create-from-template",
            "quiz-api:quiz-bulk-create-from-template",
        )
        self._auth(self.admin)

        # manque user_ids
        res = self.client.post(url, {"quiz_template_id": self.qt_ok.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # user_ids pas une liste
        res2 = self.client.post(url, {"quiz_template_id": self.qt_ok.id, "user_ids": "nope"}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

        # user_ids liste vide
        res3 = self.client.post(url, {"quiz_template_id": self.qt_ok.id, "user_ids": []}, format="json")
        self.assertEqual(res3.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_create_from_template_template_not_found_404(self):
        url = self._rev(
            "api:quiz_api:quiz-bulk-create-from-template",
            "api:quiz-api:quiz-bulk-create-from-template",
            "quiz_api:quiz-bulk-create-from-template",
            "quiz-api:quiz-bulk-create-from-template",
        )
        self._auth(self.admin)

        res = self.client.post(url, {"quiz_template_id": 999999, "user_ids": [self.u1.id]}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # ---------------------------------------------------------------------
    # QuizViewSet: close -> branche "if not quiz.ended_at" + cas ended_at déjà set (ne pas écraser)
    # ---------------------------------------------------------------------
    def test_close_quiz_does_not_override_existing_ended_at(self):
        ended = timezone.now() - timezone.timedelta(days=1)
        quiz = self._create_quiz(self.qt_ok, self.u1, active=True, started_at=timezone.now(), ended_at=ended)

        url = self._rev(
            "api:quiz_api:quiz-close",
            "api:quiz-api:quiz-close",
            "quiz_api:quiz-close",
            "quiz-api:quiz-close",
            quiz_id=quiz.id,
        )

        self._auth(self.u1)
        res = self.client.post(url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        quiz.refresh_from_db()
        self.assertEqual(quiz.ended_at, ended)  # non écrasé
        self.assertFalse(quiz.active)

    # ---------------------------------------------------------------------
    # QuizQuestionAnswerViewSet: get_queryset swagger_fake_view -> .none()
    # ---------------------------------------------------------------------
    def test_answers_get_queryset_swagger_fake_view_returns_none(self):
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        req = factory.get("/api/quiz/1/answer/")
        req.user = self.admin

        view = QuizQuestionAnswerViewSet()
        view.swagger_fake_view = True
        view.request = req
        view.kwargs = {"quiz_id": 1}

        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    # ---------------------------------------------------------------------
    # QuizQuestionAnswerViewSet: retrieve
    # ---------------------------------------------------------------------
    def test_answer_retrieve_ok_and_404_when_not_owner(self):
        quiz_u1 = self._create_quiz(self.qt_ok, self.u1, active=True, started_at=timezone.now())
        ans = self._make_answer(quiz_u1, self.qq1, True, 1)

        # retrieve OK pour owner
        self._auth(self.u1)
        url = self._answers_detail_url(quiz_u1, ans.id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], ans.id)

        # u2 ne peut pas accéder au quiz de u1 -> 404 (get_quiz filtre)
        self._auth(self.u2)
        res2 = self.client.get(url)
        self.assertEqual(res2.status_code, status.HTTP_404_NOT_FOUND)
