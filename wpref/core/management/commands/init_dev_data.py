from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from domain.models import Domain
from language.models import Language
from subject.models import Subject

User = get_user_model()


class Command(BaseCommand):
    help = "Initialize dev data: users, languages, domains, subjects (idempotent)."

    LANGUAGES = {
        "fr": "Français",
        "en": "English",
        "nl": "Nederlands",
        "it": "Italiano",
        "es": "Español",
    }

    @transaction.atomic
    def handle(self, *args, **options):
        owner = self._ensure_owner_user(username="admin", email="admin@example.com")

        self._init_languages()
        waterpolo, it_domain = self._init_domains(owner=owner)
        self._init_subjects(waterpolo=waterpolo, it_domain=it_domain)

        self.stdout.write(self.style.SUCCESS("✅ Dev data initialized"))

    # ---------- USERS ----------
    def _ensure_owner_user(self, *, username: str, email: str) -> User:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        if created:
            # mot de passe simple en dev; change-le si tu veux
            user.set_password("SuperPassword123")
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f"✔ user '{username}' created (password=admin)"))
        else:
            self.stdout.write(f"✔ user '{username}' exists")
        return user

    # ---------- LANGUAGES ----------
    def _init_languages(self) -> None:
        for code, name in self.LANGUAGES.items():
            lang, created = Language.objects.get_or_create(
                code=code,
                defaults={"name": name, "active": True},
            )
            if not created and not getattr(lang, "active", True):
                lang.active = True
                lang.save(update_fields=["active"])

            self.stdout.write(f"✔ language {code} → {'created' if created else 'exists'}")

    # ---------- DOMAINS ----------
    def _init_domains(self, *, owner: User) -> tuple[Domain, Domain]:
        all_langs = list(Language.objects.all())
        if not all_langs:
            raise CommandError("No Language found. Run init_languages first (or this command should have created them).")

        waterpolo_langs = list(Language.objects.filter(code__in=["fr", "nl", "en"]))
        missing = sorted({"fr", "nl", "en"} - {l.code for l in waterpolo_langs})
        if missing:
            raise CommandError(f"Missing languages for Water-polo: {', '.join(missing)}")

        waterpolo = self._get_or_create_domain_by_any_name(
            owner=owner,
            names=["Water polo", "Water-polo", "Waterpolo"],
            translations={
                "fr": ("Water-polo", "Discipline sportive collective aquatique."),
                "nl": ("Waterpolo", "Teamsport gespeeld in het water."),
                "en": ("Water polo", "Team water sport played in a pool."),
            },
        )
        waterpolo.allowed_languages.set(waterpolo_langs)
        self.stdout.write(self.style.SUCCESS(f"✔ domain Water-polo id={waterpolo.id}"))

        it_domain = self._get_or_create_domain_by_any_name(
            owner=owner,
            names=["IT"],
            translations={
                "fr": ("IT", "Technologies de l'information."),
                "nl": ("IT", "Informatietechnologie."),
                "en": ("IT", "Information Technology."),
                "it": ("IT", "Tecnologia dell'informazione."),
                "es": ("IT", "Tecnología de la información."),
            },
        )
        it_domain.allowed_languages.set(all_langs)
        self.stdout.write(self.style.SUCCESS(f"✔ domain IT id={it_domain.id}"))

        return waterpolo, it_domain

    def _get_or_create_domain_by_any_name(
        self,
        *,
        owner: User,
        names: list[str],
        translations: dict[str, tuple[str, str]],
    ) -> Domain:
        domain = Domain.objects.filter(owner=owner, translations__name__in=names).distinct().first()
        created = False
        if not domain:
            domain = Domain.objects.create(owner=owner, active=True)
            created = True

        for lang_code, (name, desc) in translations.items():
            domain.set_current_language(lang_code)
            domain.name = name
            domain.description = desc
            domain.save()

        self.stdout.write(f"✔ domain {names[0]} → {'created' if created else 'exists'}")
        return domain

    # ---------- SUBJECTS ----------
    def _init_subjects(self, *, waterpolo: Domain, it_domain: Domain) -> None:
        # Water-polo (FR)
        self._get_or_create_subject(domain=waterpolo, lang="fr", name="Règlement général")
        self._get_or_create_subject(domain=waterpolo, lang="fr", name="Dimensions, champ de jeu et durée")

        # IT (FR)
        for name in ["Programmation", "Réseau", "Django", "Python"]:
            self._get_or_create_subject(domain=it_domain, lang="fr", name=name)

    def _get_or_create_subject(self, *, domain: Domain, lang: str, name: str) -> Subject:
        subject = Subject.objects.filter(domain=domain, translations__name=name).distinct().first()
        created = False
        if not subject:
            subject = Subject.objects.create(domain=domain, active=True)
            created = True

        subject.set_current_language(lang)
        subject.name = name
        subject.description = ""
        subject.save()

        self.stdout.write(f"✔ subject {domain} / {name} → {'created' if created else 'exists'}")
        return subject
