from django.db import transaction

from domain.models import Domain
from subject.models import Subject

def _get_domain_by_name_any_lang(names: list[str]) -> Domain | None:
    qs = Domain.objects.filter(translations__name__in=names).distinct()
    return qs.first()

def _create_subjects(domain: Domain, names: list[str], lang: str = "fr") -> None:
    for name in names:
        # get_or_create sur (domain + nom traduit) pour être idempotent
        subject = (
            Subject.objects.filter(domain=domain, translations__name=name)
            .distinct()
            .first()
        )

        created = False
        if not subject:
            subject = Subject.objects.create(domain=domain, active=True)
            created = True

        subject.set_current_language(lang)
        subject.name = name
        subject.description = ""
        subject.save()

        status = "created" if created else "exists"
        print(f"✔ {domain} → {name} ({status})")



@transaction.atomic
def run():
    # --- récupérer domaines (par leur traduction EN/FR) ---
    waterpolo = _get_domain_by_name_any_lang(["Water polo", "Water-polo", "Waterpolo"])
    it_domain = _get_domain_by_name_any_lang(["IT"])

    if not waterpolo:
        raise Exception(
            "Domain 'Water-polo' not found (searched names: Water polo / Water-polo / Waterpolo). "
            "Run init_domains first."
        )
    if not it_domain:
        raise Exception("Domain 'IT' not found. Run init_domains first.")

    # --- sujets à créer ---
    waterpolo_subjects = [
        "Règlement général",
        "Dimensions, champ de jeu et durée",
    ]
    it_subjects = [
        "Programmation",
        "Réseau",
        "Django",
        "Python",
    ]

    _create_subjects(domain=waterpolo, names=waterpolo_subjects, lang="fr")
    _create_subjects(domain=it_domain, names=it_subjects, lang="fr")

    print("✅ Subjects initialized")

