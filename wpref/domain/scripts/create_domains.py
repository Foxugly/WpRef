from django.contrib.auth import get_user_model
from django.db import transaction

from domain.models import Domain
from language.models import Language

User = get_user_model()
OWNER_USERNAME = "admin"


def _get_or_create_domain(owner, key: str, translations: dict):
    """
    Idempotent Domain creation with django-parler translations.
    We identify an existing domain by its EN name if present, otherwise by FR name, otherwise create new.
    """
    # Choix d’un "slug" de recherche stable (ici basé sur le nom)
    lookup_name = None
    if "en" in translations:
        lookup_name = translations["en"][0]
    elif "fr" in translations:
        lookup_name = translations["fr"][0]
    else:
        lookup_name = key

    # parler supports querying translated fields via translations__<field>
    domain = (
        Domain.objects.filter(translations__name=lookup_name, owner=owner)
        .distinct()
        .first()
    )
    created = False
    if not domain:
        domain = Domain.objects.create(owner=owner, active=True)
        created = True

    # assurer translations
    for lang_code, (name, desc) in translations.items():
        domain.set_current_language(lang_code)
        domain.name = name
        domain.description = desc
        domain.save()

    # (optionnel) tu peux tagger via un champ si tu en as un; sinon key est juste interne
    print(f"✔ {key} → {'created' if created else 'exists'} (id={domain.id})")
    return domain


@transaction.atomic
def run():
    try:
        owner = User.objects.get(username=OWNER_USERNAME)
    except User.DoesNotExist as e:
        raise Exception(f"Owner user '{OWNER_USERNAME}' not found.") from e

    all_langs = list(Language.objects.all())
    if not all_langs:
        raise Exception("No Language found. Run init_languages first.")

    codes_needed = {"fr", "nl", "en"}
    waterpolo_langs = list(Language.objects.filter(code__in=codes_needed))
    missing = sorted(codes_needed - {l.code for l in waterpolo_langs})
    if missing:
        raise Exception(
            f"Missing languages for Water-polo: {', '.join(missing)}. Run init_languages first."
        )

    # 1) Water-polo (FR/NL/EN)
    waterpolo = _get_or_create_domain(
        owner=owner,
        key="WATER_POLO",
        translations={
            "fr": ("Water-polo", "Discipline sportive collective aquatique."),
            "nl": ("Waterpolo", "Teamsport gespeeld in het water."),
            "en": ("Water polo", "Team water sport played in a pool."),
        },
    )
    waterpolo.allowed_languages.set(waterpolo_langs)
    print(f"✅ Water-polo domain id={waterpolo.id}")

    # 2) IT (toutes les langues)
    it_domain = _get_or_create_domain(
        owner=owner,
        key="IT",
        translations={
            "fr": ("IT", "Technologies de l'information."),
            "nl": ("IT", "Informatietechnologie."),
            "en": ("IT", "Information Technology."),
            "it": ("IT", "Tecnologia dell'informazione."),
            "es": ("IT", "Tecnología de la información."),
        },
    )
    it_domain.allowed_languages.set(all_langs)
    print(f"✅ IT domain id={it_domain.id}")

    print("🎉 Domains initialized")



