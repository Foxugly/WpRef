# question/tests/test_models.py
import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from domain.models import Domain
from question.models import Question, AnswerOption, QuestionMedia, QuestionSubject
from subject.models import Subject

from language.models import Language

logger = logging.getLogger(__name__)
User = get_user_model()


class QuestionModelsTestCase(TestCase):
    # ------------------------------------------------------------------
    # Helpers "robustes" (Domain/Subject peuvent avoir des champs requis)
    # ------------------------------------------------------------------
    def _auto_create_required_fields(self, model_cls, overrides=None):
        """
        Crée un objet en remplissant automatiquement les champs requis (non null, sans default)
        avec des valeurs simples. Permet de ne pas dépendre du schéma exact du modèle.
        """
        overrides = overrides or {}
        data = dict(overrides)

        for f in model_cls._meta.fields:
            if f.primary_key:
                continue
            if f.name in data:
                continue

            # Si le champ a un default => ignore
            if f.has_default():
                continue

            # Requis ?
            required = (not getattr(f, "null", False)) and (not getattr(f, "blank", False))
            if not required:
                continue

            # ForeignKey requis -> pas géré ici (Domain est supposé sans FK requis)
            if f.is_relation and f.many_to_one:
                # On essaye au mieux : si FK requis, il faut adapter selon ton schéma.
                # On raise pour que tu voies vite le champ.
                raise RuntimeError(
                    f"Impossible d'auto-créer {model_cls.__name__}: FK requis '{f.name}'. "
                    f"Ajoute un override dans _make_domain()."
                )

            from django.db import models

            if isinstance(f, (models.CharField, models.SlugField)):
                data[f.name] = "x"
            elif isinstance(f, models.TextField):
                data[f.name] = "x"
            elif isinstance(f, models.BooleanField):
                data[f.name] = True
            elif isinstance(f, (models.IntegerField, models.PositiveIntegerField, models.SmallIntegerField)):
                data[f.name] = 1
            elif isinstance(f, models.DateTimeField):
                data[f.name] = timezone.now()
            elif isinstance(f, models.DateField):
                data[f.name] = timezone.now().date()
            else:
                # fallback simple
                data[f.name] = "x"

        return model_cls.objects.create(**data)

    def _make_user(self, username_prefix="owner"):
        n = User.objects.count() + 1
        return User.objects.create_user(username=f"{username_prefix}{n}", password="pass", is_staff=True)

    def _make_language(self, code="fr", name="Français"):
        """
        Optionnel: uniquement si tu veux utiliser allowed_languages dans Domain.
        Si ton modèle Language a d'autres champs requis, adapte ici.
        """
        try:
            return Language.objects.get(code=code)
        except Language.DoesNotExist:
            return Language.objects.create(code=code, name=name)

    def _make_domain(self, name="Domaine", *, owner=None, lang="fr", with_allowed_lang=False) -> Domain:
        owner = owner or self._make_user("owner")
        d = Domain.objects.create(owner=owner, active=True)
        d.set_current_language(lang)
        d.name = name
        d.description = "desc"
        d.save()

        # Optionnel: si tu veux tester Domain.clean()
        if with_allowed_lang:
            # ajoute une langue valide de settings.LANGUAGES
            # (si tu as le modèle language.Language)
            try:
                lang_obj = self._make_language(code=lang)
                d.allowed_languages.add(lang_obj)
            except Exception:
                # si ton app Language n'est pas dispo dans ce contexte, ignore
                pass

        return d

    def _make_subject(self, name="Math", lang="fr") -> Subject:
        s = Subject.objects.create()
        if hasattr(s, "set_current_language"):
            s.set_current_language(lang)
            if hasattr(s, "name"):
                s.name = name
            s.save()
        return s

    def _make_question(self, title="Q1", *, allow_multiple_correct=False, lang="fr") -> Question:
        d = self._make_domain()
        q = Question.objects.create(
            domain=d,
            allow_multiple_correct=allow_multiple_correct,
            active=True,
            is_mode_practice=True,
            is_mode_exam=True,
        )
        q.set_current_language(lang)
        q.title = title
        q.description = "desc"
        q.explanation = "expl"
        q.save()
        return q

    def _add_option(self, q: Question, *, is_correct: bool, sort_order: int, content="opt", lang="fr") -> AnswerOption:
        o = AnswerOption.objects.create(
            question=q,
            is_correct=is_correct,
            sort_order=sort_order,
        )
        o.set_current_language(lang)
        o.content = content
        o.save()
        return o

    def _validate_question(self, q: Question):
        # Question.clean() inspecte q.answer_options.all()
        q.clean()

    # ------------------------------------------------------------------
    # Question.clean() rules
    # ------------------------------------------------------------------
    def test_question_clean_requires_at_least_two_answer_options(self):
        q = self._make_question("Q-min-opts")

        # 0 option
        with self.assertRaises(ValidationError) as ctx0:
            self._validate_question(q)
        self.assertIn("at least 2", str(ctx0.exception).lower())

        # 1 option
        self._add_option(q, is_correct=True, sort_order=1)
        with self.assertRaises(ValidationError) as ctx1:
            self._validate_question(q)
        self.assertIn("at least 2", str(ctx1.exception).lower())

    def test_question_clean_requires_at_least_one_correct(self):
        q = self._make_question("Q-no-correct")
        self._add_option(q, is_correct=False, sort_order=1)
        self._add_option(q, is_correct=False, sort_order=2)

        with self.assertRaises(ValidationError) as ctx:
            self._validate_question(q)
        self.assertIn("au moins une", str(ctx.exception).lower())
        self.assertIn("correct", str(ctx.exception).lower())

    def test_question_clean_requires_exactly_one_correct_when_multiple_not_allowed(self):
        q = self._make_question("Q-one-correct-only", allow_multiple_correct=False)
        self._add_option(q, is_correct=True, sort_order=1)
        self._add_option(q, is_correct=True, sort_order=2)

        with self.assertRaises(ValidationError) as ctx:
            self._validate_question(q)
        self.assertIn("only one", str(ctx.exception).lower())

    def test_question_clean_allows_multiple_correct_when_flag_true(self):
        q = self._make_question("Q-multi-correct", allow_multiple_correct=True)
        self._add_option(q, is_correct=True, sort_order=1)
        self._add_option(q, is_correct=True, sort_order=2)

        # doit passer
        self._validate_question(q)

    def test_question_clean_passes_for_valid_single_correct(self):
        q = self._make_question("Q-valid", allow_multiple_correct=False)
        self._add_option(q, is_correct=True, sort_order=1)
        self._add_option(q, is_correct=False, sort_order=2)

        self._validate_question(q)

    # ------------------------------------------------------------------
    # Question __str__ (avec fallback si pas de traduction)
    # ------------------------------------------------------------------
    def test_question_str_with_translation(self):
        q = self._make_question("Ma question")
        self.assertEqual(str(q), "Ma question")

    def test_question_str_fallback_when_no_title_translation(self):
        d = self._make_domain()
        q = Question.objects.create(
            domain=d,
            allow_multiple_correct=False,
            active=True,
            is_mode_practice=True,
            is_mode_exam=True,
        )
        # pas de titre en traduction
        self.assertEqual(str(q), f"Question#{q.pk}")

    # ------------------------------------------------------------------
    # Question ordering (Meta.ordering = ["-pk"])
    # ------------------------------------------------------------------
    def test_question_ordering_is_newest_pk_first(self):
        q1 = self._make_question("Q-old")
        q2 = self._make_question("Q-new")
        ordered = list(Question.objects.all())
        self.assertEqual([x.pk for x in ordered], [q2.pk, q1.pk])

    # ------------------------------------------------------------------
    # AnswerOption ordering + __str__
    # ------------------------------------------------------------------
    def test_answeroption_ordering_sort_order_then_id(self):
        q = self._make_question("Q-ordering")
        o2 = self._add_option(q, is_correct=False, sort_order=2, content="B")
        o1 = self._add_option(q, is_correct=True, sort_order=1, content="A")

        ordered = list(q.answer_options.all())
        self.assertEqual([x.pk for x in ordered], [o1.pk, o2.pk])

        # __str__
        self.assertIn(f"Option(Q{q.pk})", str(o1))
        self.assertIn("✔", str(o1))
        self.assertIn("✗", str(o2))

    # ------------------------------------------------------------------
    # M2M subjects through QuestionSubject
    # ------------------------------------------------------------------
    def test_question_subject_add_creates_through_row(self):
        s = self._make_subject("History", "history")
        q = self._make_question("Q-subjects")

        q.subjects.add(s)  # crée QuestionSubject (through)
        self.assertEqual(q.subjects.count(), 1)
        self.assertEqual(QuestionSubject.objects.filter(question=q, subject=s).count(), 1)

        link = QuestionSubject.objects.get(question=q, subject=s)
        self.assertEqual(link.sort_order, 0)
        self.assertEqual(link.weight, 1)
        self.assertIn("↔", str(link))
        self.assertIn("ord:", str(link))
        self.assertIn("w:", str(link))

    def test_questionsubject_unique_together_enforced(self):
        s = self._make_subject("Geo", "geo")
        q = self._make_question("Q-unique-link")

        QuestionSubject.objects.create(question=q, subject=s)
        with self.assertRaises(IntegrityError):
            QuestionSubject.objects.create(question=q, subject=s)

    def test_questionsubject_ordering_is_newest_pk_first(self):
        s1 = self._make_subject("Aaa", "aaa")
        s2 = self._make_subject("Bbb", "bbb")
        q = self._make_question("Q-order-subject")
        qs1 = QuestionSubject.objects.create(question=q, subject=s1, sort_order=5)
        qs2 = QuestionSubject.objects.create(question=q, subject=s2, sort_order=0)

        ordered = list(QuestionSubject.objects.all())
        # ordering = ["-pk"]
        self.assertEqual([x.pk for x in ordered], [qs2.pk, qs1.pk])

    def test_questionsubject_str_fallback_when_subject_has_no_translation(self):
        # Subject sans name traduit => fallback Subject#id
        s = Subject.objects.create()
        q = self._make_question("Q-link-fallback")
        link = QuestionSubject.objects.create(question=q, subject=s, sort_order=0, weight=1)
        self.assertIn(f"Subject#{s.pk}", str(link))

    # ------------------------------------------------------------------
    # QuestionMedia.clean() + __str__
    # ------------------------------------------------------------------
    def test_questionmedia_clean_external_requires_external_url_only(self):
        q = self._make_question("Q-media-ext")

        # external sans url
        m1 = QuestionMedia(question=q, kind=QuestionMedia.EXTERNAL, external_url=None, file=None, sort_order=0)
        with self.assertRaises(ValidationError) as ctx:
            m1.clean()
        self.assertIn("external_url", str(ctx.exception).lower())

        # external avec url + file => interdit
        f = SimpleUploadedFile("x.png", b"fake", content_type="image/png")
        m2 = QuestionMedia(question=q, kind=QuestionMedia.EXTERNAL, external_url="https://x", file=f, sort_order=0)
        with self.assertRaises(ValidationError):
            m2.clean()

    def test_questionmedia_clean_file_requires_file_only(self):
        q = self._make_question("Q-media-file")

        # image sans file
        m1 = QuestionMedia(question=q, kind=QuestionMedia.IMAGE, file=None, external_url=None, sort_order=0)
        with self.assertRaises(ValidationError) as ctx:
            m1.clean()
        self.assertIn("file", str(ctx.exception).lower())

        # image avec file + external_url => interdit
        f = SimpleUploadedFile("x.png", b"fake", content_type="image/png")
        m2 = QuestionMedia(question=q, kind=QuestionMedia.IMAGE, file=f, external_url="https://x", sort_order=0)
        with self.assertRaises(ValidationError):
            m2.clean()

        # OK : image avec file only
        m3 = QuestionMedia(question=q, kind=QuestionMedia.IMAGE, file=f, external_url=None, sort_order=0)
        m3.clean()

    def test_questionmedia_str(self):
        q = self._make_question("Q-media-str")

        # external url
        m1 = QuestionMedia.objects.create(
            question=q,
            kind=QuestionMedia.EXTERNAL,
            external_url="https://example.com",
            sort_order=1,
        )
        self.assertIn("external", str(m1))
        self.assertIn("https://example.com", str(m1))

        # file
        f = SimpleUploadedFile("x.png", b"fake", content_type="image/png")
        m2 = QuestionMedia.objects.create(
            question=q,
            kind=QuestionMedia.IMAGE,
            file=f,
            sort_order=2,
        )
        self.assertIn("image", str(m2))
        # le path exact dépend du storage, on check juste qu'il y a un nom
        self.assertTrue("x.png" in str(m2) or "question_media" in str(m2))

    def test_domain_clean_rejects_invalid_allowed_language_code(self):
        owner = self._make_user("owner")
        d = self._make_domain(name="D", owner=owner, lang="fr")

        # crée une language invalide (pas dans settings.LANGUAGES)
        bad = Language.objects.create(code="xx", name="Invalid")
        d.allowed_languages.add(bad)

        with self.assertRaises(ValidationError):
            d.clean()
