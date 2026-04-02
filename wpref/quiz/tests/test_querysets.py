from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import translation

from domain.models import Domain
from quiz.models import Quiz, QuizTemplate
from quiz.querysets import accessible_quiz_template_queryset

User = get_user_model()


class QuizQuerysetsTests(TestCase):
    def setUp(self):
        translation.activate("fr")
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.user = User.objects.create_user(username="user", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")

        self.domain = Domain.objects.create(owner=self.owner, name="Domain A", description="", active=True)
        self.other_domain = Domain.objects.create(owner=self.owner, name="Domain B", description="", active=True)
        self.user.current_domain = self.domain
        self.user.save(update_fields=["current_domain"])

        self.public_same_domain = QuizTemplate.objects.create(
            domain=self.domain,
            title="Public same",
            is_public=True,
            active=True,
            permanent=True,
        )
        self.public_other_domain = QuizTemplate.objects.create(
            domain=self.other_domain,
            title="Public other",
            is_public=True,
            active=True,
            permanent=True,
        )
        self.private_assigned = QuizTemplate.objects.create(
            domain=self.other_domain,
            title="Private assigned",
            is_public=False,
            active=True,
            permanent=True,
        )
        self.private_hidden = QuizTemplate.objects.create(
            domain=self.other_domain,
            title="Private hidden",
            is_public=False,
            active=True,
            permanent=True,
        )
        Quiz.objects.create(quiz_template=self.private_assigned, user=self.user, active=False)

    def tearDown(self):
        translation.deactivate_all()
        super().tearDown()

    def test_accessible_quiz_template_queryset_filters_in_database(self):
        queryset = accessible_quiz_template_queryset(self.user)

        self.assertTrue(hasattr(queryset, "filter"))
        self.assertCountEqual(
            list(queryset.values_list("id", flat=True)),
            [self.public_same_domain.id, self.private_assigned.id],
        )
