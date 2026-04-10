from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.utils import translation

from domain.models import Domain
from question.models import Question
from quiz.models import Quiz, QuizQuestion, QuizQuestionAnswer, QuizTemplate
from quiz.querysets import accessible_quiz_template_queryset, quiz_template_queryset, template_sessions_queryset

User = get_user_model()


class QuizQuerysetsTests(TestCase):
    def setUp(self):
        translation.activate("fr")
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.user = User.objects.create_user(username="user", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        self.staff_user = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.domain_staff = User.objects.create_user(username="domainstaff", password="pass")

        self.domain = Domain.objects.create(owner=self.owner, name="Domain A", description="", active=True)
        self.other_domain = Domain.objects.create(owner=self.owner, name="Domain B", description="", active=True)

        self.public_same_domain = QuizTemplate.objects.create(
            domain=self.domain,
            title="Public same",
            is_public=True,
            active=True,
            permanent=True,
            created_by=self.owner,
        )
        self.public_other_domain = QuizTemplate.objects.create(
            domain=self.other_domain,
            title="Public other",
            is_public=True,
            active=True,
            permanent=True,
            created_by=self.owner,
        )
        self.private_assigned = QuizTemplate.objects.create(
            domain=self.other_domain,
            title="Private assigned",
            is_public=False,
            active=True,
            permanent=True,
            created_by=self.owner,
        )
        self.private_hidden = QuizTemplate.objects.create(
            domain=self.other_domain,
            title="Private hidden",
            is_public=False,
            active=True,
            permanent=True,
            created_by=self.other_user,
        )
        Quiz.objects.create(quiz_template=self.private_assigned, user=self.user, active=False)
        self.domain.members.add(self.user)
        self.domain.staff.add(self.domain_staff)

    def tearDown(self):
        translation.deactivate_all()
        super().tearDown()

    def test_accessible_quiz_template_queryset_filters_in_database(self):
        queryset = accessible_quiz_template_queryset(self.user)

        self.assertTrue(hasattr(queryset, "filter"))
        with self.assertNumQueries(1):
            ids = list(queryset.values_list("id", flat=True))
        self.assertCountEqual(ids, [self.public_same_domain.id, self.public_other_domain.id, self.private_assigned.id])

    def test_staff_user_without_linked_domain_sees_public_available_templates(self):
        queryset = accessible_quiz_template_queryset(self.staff_user)

        self.assertCountEqual(
            list(queryset.values_list("id", flat=True)),
            [self.public_same_domain.id, self.public_other_domain.id],
        )

    def test_domain_staff_sees_all_templates_of_managed_domain(self):
        private_same_domain = QuizTemplate.objects.create(
            domain=self.domain,
            title="Private same domain",
            is_public=False,
            active=True,
            permanent=True,
            created_by=self.other_user,
        )

        queryset = accessible_quiz_template_queryset(self.domain_staff)

        self.assertCountEqual(
            list(queryset.values_list("id", flat=True)),
            [self.public_same_domain.id, private_same_domain.id],
        )

    def test_simple_creator_does_not_see_inactive_template(self):
        own_inactive = QuizTemplate.objects.create(
            domain=self.other_domain,
            title="Own inactive",
            is_public=False,
            active=False,
            permanent=True,
            created_by=self.user,
        )

        queryset = accessible_quiz_template_queryset(self.user)

        self.assertNotIn(own_inactive.id, list(queryset.values_list("id", flat=True)))

    def test_domain_staff_still_sees_inactive_template_of_managed_domain(self):
        inactive_same_domain = QuizTemplate.objects.create(
            domain=self.domain,
            title="Inactive same domain",
            is_public=False,
            active=False,
            permanent=True,
            created_by=self.other_user,
        )

        queryset = accessible_quiz_template_queryset(self.domain_staff)

        self.assertIn(inactive_same_domain.id, list(queryset.values_list("id", flat=True)))

    def test_stale_current_domain_does_not_grant_template_access(self):
        self.other_user.current_domain = self.domain
        self.other_user.save(update_fields=["current_domain"])

        queryset = accessible_quiz_template_queryset(self.other_user)

        self.assertCountEqual(
            list(queryset.values_list("id", flat=True)),
            [self.public_same_domain.id, self.public_other_domain.id],
        )

    def test_simple_user_does_not_see_public_template_outside_availability_window(self):
        unavailable_public = QuizTemplate.objects.create(
            domain=self.other_domain,
            title="Public unavailable",
            is_public=True,
            active=True,
            permanent=False,
            started_at=timezone.now() + timezone.timedelta(days=1),
            ended_at=timezone.now() + timezone.timedelta(days=2),
            created_by=self.owner,
        )

        queryset = accessible_quiz_template_queryset(self.user)

        self.assertNotIn(unavailable_public.id, list(queryset.values_list("id", flat=True)))

    def test_domain_staff_sees_public_template_outside_availability_window(self):
        unavailable_public = QuizTemplate.objects.create(
            domain=self.domain,
            title="Managed public unavailable",
            is_public=True,
            active=True,
            permanent=False,
            started_at=timezone.now() + timezone.timedelta(days=1),
            ended_at=timezone.now() + timezone.timedelta(days=2),
            created_by=self.owner,
        )

        queryset = accessible_quiz_template_queryset(self.domain_staff)

        self.assertIn(unavailable_public.id, list(queryset.values_list("id", flat=True)))

    def test_simple_user_does_not_see_private_template_outside_availability_window_even_if_assigned(self):
        unavailable_private = QuizTemplate.objects.create(
            domain=self.other_domain,
            title="Private unavailable",
            is_public=False,
            active=True,
            permanent=False,
            started_at=timezone.now() + timezone.timedelta(days=1),
            ended_at=timezone.now() + timezone.timedelta(days=2),
            created_by=self.owner,
        )
        Quiz.objects.create(quiz_template=unavailable_private, user=self.user, active=False)

        queryset = accessible_quiz_template_queryset(self.user)

        self.assertNotIn(unavailable_private.id, list(queryset.values_list("id", flat=True)))

    def test_started_exam_template_is_hidden_for_simple_user(self):
        exam_template = QuizTemplate.objects.create(
            domain=self.other_domain,
            title="Exam public",
            is_public=True,
            active=True,
            permanent=True,
            mode=QuizTemplate.MODE_EXAM,
            created_by=self.owner,
        )
        Quiz.objects.create(
            quiz_template=exam_template,
            user=self.user,
            active=True,
            started_at=timezone.now(),
        )

        queryset = accessible_quiz_template_queryset(self.user)

        self.assertNotIn(exam_template.id, list(queryset.values_list("id", flat=True)))

    def test_quiz_template_queryset_annotates_questions_count_without_n_plus_one(self):
        question_a = Question.objects.create(
            domain=self.domain,
            title="Question A",
            description="",
            explanation="",
            active=True,
            allow_multiple_correct=False,
            is_mode_practice=True,
            is_mode_exam=True,
        )
        question_b = Question.objects.create(
            domain=self.domain,
            title="Question B",
            description="",
            explanation="",
            active=True,
            allow_multiple_correct=False,
            is_mode_practice=True,
            is_mode_exam=True,
        )
        QuizQuestion.objects.create(quiz=self.public_same_domain, question=question_a, sort_order=1, weight=1)
        QuizQuestion.objects.create(quiz=self.public_same_domain, question=question_b, sort_order=2, weight=1)
        QuizQuestion.objects.create(quiz=self.public_other_domain, question=question_a, sort_order=1, weight=1)

        with self.assertNumQueries(3):
            templates = list(quiz_template_queryset().order_by("id"))

        with self.assertNumQueries(0):
            rows = [(template.id, template.questions_count) for template in templates]

        counts = {template_id: count for template_id, count in rows}
        self.assertEqual(counts[self.public_same_domain.id], 2)
        self.assertEqual(counts[self.public_other_domain.id], 1)

    def test_template_sessions_queryset_prefetches_selected_options(self):
        question = Question.objects.create(
            domain=self.domain,
            title="Question Sessions",
            description="",
            explanation="",
            active=True,
            allow_multiple_correct=False,
            is_mode_practice=True,
            is_mode_exam=True,
        )
        option = question.answer_options.create(content="A", is_correct=True, sort_order=1)
        quiz_question = QuizQuestion.objects.create(quiz=self.private_assigned, question=question, sort_order=1, weight=1)
        session = Quiz.objects.create(
            quiz_template=self.private_assigned,
            user=self.user,
            active=True,
            started_at=timezone.now(),
        )
        answer = QuizQuestionAnswer.objects.create(quiz=session, quizquestion=quiz_question, question_order=1)
        answer.selected_options.set([option])

        with self.assertNumQueries(3):
            sessions = list(template_sessions_queryset(self.private_assigned))

        with self.assertNumQueries(0):
            selected_ids = [
                [option.id for option in answer.selected_options.all()]
                for session in sessions
                for answer in session.answers.all()
            ]

        self.assertIn([option.id], selected_ids)
