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
        missing = sorted({"fr", "nl", "en"} - {language.code for language in waterpolo_langs})
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
        # Water-polo
        self._get_or_create_subject(
            domain=waterpolo,
            translations={
                "fr": {"name": "Règlement général", "description": "Les bases du jeu."},
                "nl": {"name": "Algemeen reglement", "description": "De basis van het spel."},
                "en": {"name": "General rules", "description": "Game fundamentals."},
            },
        )

        self._get_or_create_subject(
            domain=waterpolo,
            translations={
                "fr": {
                    "name": "Dimensions, champ de jeu et durée",
                    "description": "Dimensions du bassin, zones de jeu et durée des matchs."
                },
                "nl": {
                    "name": "Afmetingen, speelveld en speeltijd",
                    "description": "Afmetingen van het bad, speelzones en speeltijd."
                },
                "en": {
                    "name": "Field dimensions and match duration",
                    "description": "Pool dimensions, playing areas and match duration."
                },
            }
        )

        # IT
        self._get_or_create_subject(
            domain=it_domain,
            translations={
                "fr": {"name": "Programmation", "description": "Principes fondamentaux de la programmation."},
                "nl": {"name": "Programmeren", "description": "Basisprincipes van programmeren."},
                "en": {"name": "Programming", "description": "Fundamental programming principles."},
                "it": {"name": "Programmazione", "description": "Principi fondamentali della programmazione."},
                "es": {"name": "Programación", "description": "Principios fundamentales de la programación."},
            }
        )

        self._get_or_create_subject(
            domain=it_domain,
            translations={
                "fr": {"name": "Réseau", "description": "Concepts réseaux fondamentaux."},
                "nl": {"name": "Netwerken", "description": "Basisnetwerkconcepten."},
                "en": {"name": "Networking", "description": "Core networking concepts."},
                "it": {"name": "Reti", "description": "Concetti fondamentali di rete."},
                "es": {"name": "Redes", "description": "Conceptos básicos de redes."},
            }
        )

        self._get_or_create_subject(
            domain=it_domain,
            translations={
                "fr": {"name": "Django", "description": "Framework web Python orienté rapidité et robustesse."},
                "nl": {"name": "Django", "description": "Python webframework voor snelle ontwikkeling."},
                "en": {"name": "Django", "description": "Python web framework for rapid development."},
                "it": {"name": "Django", "description": "Framework web Python per sviluppo rapido."},
                "es": {"name": "Django", "description": "Framework web Python para desarrollo rápido."},
            }
        )

        self._get_or_create_subject(
            domain=it_domain,
            translations={
                "fr": {"name": "Python", "description": "Langage de programmation polyvalent et lisible."},
                "nl": {"name": "Python", "description": "Veelzijdige en leesbare programmeertaal."},
                "en": {"name": "Python", "description": "Versatile and readable programming language."},
                "it": {"name": "Python", "description": "Linguaggio di programmazione versatile e leggibile."},
                "es": {"name": "Python", "description": "Lenguaje de programación versátil y legible."},
            }
        )

    def _get_or_create_subject(
            self,
            *,
            domain: Domain,
            name: str | None = None,
            description: str | None = "",
            translations: dict[str, dict[str, str]] | None = None,
    ) -> Subject:
        """
        Idempotent subject init:
        - subject is searched by any provided translated name (if translations) or by `name`
        - for each allowed language of the domain, ensures (name, description) are set
        """

        # 1) Determine target languages for the subject
        domain_langs = list(domain.allowed_languages.all())
        if not domain_langs:
            domain_langs = list(Language.objects.all())  # fallback if domain has none

        lang_codes = [language.code for language in domain_langs]

        # 2) Find existing subject (by any translated name)
        lookup_names: list[str] = []
        if translations:
            lookup_names = [v.get("name", "") for v in translations.values() if v.get("name")]
        if not lookup_names and name:
            lookup_names = [name]

        subject = None
        if lookup_names:
            subject = (
                Subject.objects
                .filter(domain=domain, translations__name__in=lookup_names)
                .distinct()
                .first()
            )

        created = False
        if not subject:
            subject = Subject.objects.create(domain=domain, active=True)
            created = True

        # 3) Prepare per-language payload
        # If translations provided, use it. Otherwise replicate (name/description) across all languages.
        if translations is None:
            if not name:
                raise CommandError("Provide either `name` or `translations` for subject creation.")
            translations = {code: {"name": name, "description": description or ""} for code in lang_codes}

        # 4) Ensure every domain language has a translation
        for code in lang_codes:
            payload = translations.get(code)

            # fallback strategy if missing:
            # - try "en", else first provided translation, else domain default `name`
            if not payload:
                payload = translations.get("en") or next(iter(translations.values()), None) or {"name": name or "",
                                                                                                "description": description or ""}

            subject.set_current_language(code)
            subject.name = payload.get("name", name or "") or ""
            subject.description = payload.get("description", "") or ""
            subject.save()

        self.stdout.write(
            f"✔ subject {domain.id} / {lookup_names[0] if lookup_names else 'subject'} → {'created' if created else 'exists'}"
        )
        return subject
