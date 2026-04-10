import base64
import hashlib
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from domain.models import Domain
from language.models import Language
from question.models import AnswerOption, MediaAsset, Question, QuestionMedia
from question.youtube import normalize_external_url
from quiz.constants import VISIBILITY_IMMEDIATE
from quiz.models import Quiz, QuizQuestion, QuizTemplate
from subject.models import Subject


User = get_user_model()

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO0p5n8AAAAASUVORK5CYII="
)
MP4_PLACEHOLDER = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"


def upsert_translation(obj, language_code: str, **fields) -> None:
    translation_model = obj._parler_meta.root_model
    translation_model.objects.update_or_create(
        master_id=obj.pk,
        language_code=language_code,
        defaults=fields,
    )


def file_digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class Command(BaseCommand):
    help = "Seed deterministic data for Playwright full-stack tests."

    @transaction.atomic
    def handle(self, *args, **options):
        media_dir = Path(settings.MEDIA_ROOT) / "question_media"
        media_dir.mkdir(parents=True, exist_ok=True)

        for code, name in (("fr", "Francais"), ("nl", "Nederlands"), ("en", "English")):
            Language.objects.update_or_create(
                code=code,
                defaults={"name": name, "active": True},
            )

        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.test",
                "is_staff": True,
                "is_superuser": True,
                "language": "fr",
            },
        )
        admin.email = "admin@example.test"
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.language = "fr"
        admin.email_confirmed = True
        admin.must_change_password = False
        admin.set_password("secret123")
        admin.save()

        testuser, _ = User.objects.get_or_create(
            username="testuser",
            defaults={
                "email": "testuser@example.test",
                "is_staff": False,
                "is_superuser": False,
                "language": "fr",
            },
        )
        testuser.email = "testuser@example.test"
        testuser.is_staff = False
        testuser.is_superuser = False
        testuser.is_active = True
        testuser.language = "fr"
        testuser.email_confirmed = True
        testuser.must_change_password = False
        testuser.set_password("secret123")
        testuser.save()

        domain = (
            Domain.objects.filter(
                owner=admin,
                translations__language_code="fr",
                translations__name="Sciences",
            )
            .distinct()
            .first()
        )
        if domain is None:
            domain = Domain.objects.create(owner=admin, active=True)
        else:
            domain.owner = admin
            domain.active = True
            domain.save(update_fields=["owner", "active"])
        upsert_translation(domain, "fr", name="Sciences", description="Domaine seede pour Playwright.")
        upsert_translation(domain, "nl", name="Wetenschappen", description="Seedomein voor Playwright.")
        upsert_translation(domain, "en", name="Science", description="Playwright seed domain.")
        domain.allowed_languages.set(Language.objects.filter(code__in=["fr", "nl"]))
        domain.staff.set([admin])
        domain.members.add(testuser)

        admin.current_domain = domain
        admin.save(update_fields=["current_domain"])
        testuser.current_domain = domain
        testuser.save(update_fields=["current_domain"])

        subject_physics = (
            Subject.objects.filter(
                domain=domain,
                translations__language_code="fr",
                translations__name="Physique",
            )
            .distinct()
            .first()
        )
        if subject_physics is None:
            subject_physics = Subject.objects.create(domain=domain, active=True)
        else:
            subject_physics.active = True
            subject_physics.save(update_fields=["active"])
        upsert_translation(subject_physics, "fr", name="Physique", description="Sujet seed.")
        upsert_translation(subject_physics, "nl", name="Fysica", description="Seedonderwerp.")

        subject_astronomy = (
            Subject.objects.filter(
                domain=domain,
                translations__language_code="fr",
                translations__name="Astronomie",
            )
            .distinct()
            .first()
        )
        if subject_astronomy is None:
            subject_astronomy = Subject.objects.create(domain=domain, active=True)
        else:
            subject_astronomy.active = True
            subject_astronomy.save(update_fields=["active"])
        upsert_translation(subject_astronomy, "fr", name="Astronomie", description="Sujet secondaire.")
        upsert_translation(subject_astronomy, "nl", name="Sterrenkunde", description="Tweede onderwerp.")

        question = self._upsert_question(domain=domain, index=1, allow_multiple_correct=False)

        question.subjects.set([subject_physics, subject_astronomy])
        upsert_translation(
            question,
            "fr",
            title="Question de seed",
            description="<p>Description FR</p>",
            explanation="<p>Explication FR</p>",
        )
        upsert_translation(
            question,
            "nl",
            title="Seedvraag",
            description="<p>Beschrijving NL</p>",
            explanation="<p>Uitleg NL</p>",
        )

        question.answer_options.all().delete()
        good_answer = AnswerOption.objects.create(question=question, is_correct=True, sort_order=1)
        upsert_translation(good_answer, "fr", content="<p>Bonne reponse</p>")
        upsert_translation(good_answer, "nl", content="<p>Goed antwoord</p>")

        bad_answer = AnswerOption.objects.create(question=question, is_correct=False, sort_order=2)
        upsert_translation(bad_answer, "fr", content="<p>Mauvaise reponse</p>")
        upsert_translation(bad_answer, "nl", content="<p>Fout antwoord</p>")

        second_question = self._upsert_question(domain=domain, index=2, allow_multiple_correct=True)
        second_question.subjects.set([subject_physics])
        upsert_translation(
            second_question,
            "fr",
            title="Question de quiz 2",
            description="<p>Description quiz 2 FR</p>",
            explanation="<p>Explication quiz 2 FR</p>",
        )
        upsert_translation(
            second_question,
            "nl",
            title="Quizvraag 2",
            description="<p>Beschrijving quiz 2 NL</p>",
            explanation="<p>Uitleg quiz 2 NL</p>",
        )

        second_question.answer_options.all().delete()
        second_good_answer = AnswerOption.objects.create(
            question=second_question,
            is_correct=True,
            sort_order=1,
        )
        upsert_translation(second_good_answer, "fr", content="<p>Bonne reponse quiz 2</p>")
        upsert_translation(second_good_answer, "nl", content="<p>Goed antwoord quiz 2</p>")

        second_bad_answer = AnswerOption.objects.create(
            question=second_question,
            is_correct=False,
            sort_order=2,
        )
        upsert_translation(second_bad_answer, "fr", content="<p>Mauvaise reponse quiz 2</p>")
        upsert_translation(second_bad_answer, "nl", content="<p>Fout antwoord quiz 2</p>")

        image_asset = self._upsert_file_asset(
            kind=MediaAsset.IMAGE,
            filename="fullstack-e2e-image.png",
            content=PNG_1X1,
        )
        video_asset = self._upsert_file_asset(
            kind=MediaAsset.VIDEO,
            filename="fullstack-e2e-video.mp4",
            content=MP4_PLACEHOLDER,
        )
        youtube_asset, _ = MediaAsset.objects.update_or_create(
            kind=MediaAsset.EXTERNAL,
            external_url=normalize_external_url("https://youtu.be/dQw4w9WgXcQ?t=43"),
            defaults={"sha256": None, "file": None},
        )

        QuestionMedia.objects.filter(question=question).delete()
        QuestionMedia.objects.bulk_create([
            QuestionMedia(question=question, asset=image_asset, sort_order=0),
            QuestionMedia(question=question, asset=video_asset, sort_order=1),
            QuestionMedia(question=question, asset=youtube_asset, sort_order=2),
        ])

        quiz_template = (
            QuizTemplate.objects.filter(
                domain=domain,
                title="Quiz full-stack",
            )
            .order_by("id")
            .first()
        )
        if quiz_template is None:
            quiz_template = QuizTemplate.objects.create(
                domain=domain,
                title="Quiz full-stack",
                mode=QuizTemplate.MODE_PRACTICE,
                description="Quiz seed pour Playwright.",
                max_questions=2,
                permanent=True,
                with_duration=True,
                duration=15,
                active=True,
                result_visibility=VISIBILITY_IMMEDIATE,
                detail_visibility=VISIBILITY_IMMEDIATE,
            )
        quiz_template.domain = domain
        quiz_template.mode = QuizTemplate.MODE_PRACTICE
        quiz_template.description = "Quiz seed pour Playwright."
        quiz_template.max_questions = 2
        quiz_template.permanent = True
        quiz_template.with_duration = True
        quiz_template.duration = 15
        quiz_template.active = True
        quiz_template.result_visibility = VISIBILITY_IMMEDIATE
        quiz_template.detail_visibility = VISIBILITY_IMMEDIATE
        quiz_template.save()

        QuizQuestion.objects.filter(quiz=quiz_template).exclude(question__in=[question, second_question]).delete()
        QuizQuestion.objects.update_or_create(
            quiz=quiz_template,
            question=question,
            defaults={"sort_order": 1, "weight": 1},
        )
        QuizQuestion.objects.update_or_create(
            quiz=quiz_template,
            question=second_question,
            defaults={"sort_order": 2, "weight": 1},
        )

        quiz_session = (
            Quiz.objects.filter(quiz_template=quiz_template, user=admin)
            .order_by("id")
            .first()
        )
        if quiz_session is None:
            quiz_session = Quiz.objects.create(
                quiz_template=quiz_template,
                user=admin,
                domain=domain,
                active=False,
                started_at=None,
                ended_at=None,
            )
        quiz_session.domain = domain
        quiz_session.active = False
        quiz_session.started_at = None
        quiz_session.ended_at = None
        quiz_session.save()
        quiz_session.answers.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded full-stack data: "
                f"user=admin question_id={question.id} quiz_id={quiz_session.id} domain_id={domain.id}",
            ),
        )

    def _upsert_file_asset(self, *, kind: str, filename: str, content: bytes) -> MediaAsset:
        digest = file_digest(content)
        asset = MediaAsset.objects.filter(kind=kind, sha256=digest).first()
        if asset:
            file_missing = not asset.file or not asset.file.name or not Path(asset.file.path).exists()
            if file_missing:
                asset.file.save(filename, ContentFile(content), save=False)
                asset.save(update_fields=["file", "updated_at"])
            return asset

        asset = MediaAsset(kind=kind, sha256=digest)
        asset.file.save(filename, ContentFile(content), save=False)
        asset.save()
        return asset

    def _upsert_question(self, *, domain: Domain, index: int, allow_multiple_correct: bool) -> Question:
        question = (
            Question.objects.filter(domain=domain)
            .order_by("id")
            .all()[index - 1:index]
            .first()
        )
        if question is None:
            question = Question.objects.create(
                domain=domain,
                active=True,
                is_mode_practice=True,
                is_mode_exam=True,
                allow_multiple_correct=allow_multiple_correct,
            )
        else:
            question.active = True
            question.is_mode_practice = True
            question.is_mode_exam = True
            question.allow_multiple_correct = allow_multiple_correct
            question.save(update_fields=["active", "is_mode_practice", "is_mode_exam", "allow_multiple_correct"])
        return question
