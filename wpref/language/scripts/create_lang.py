from language.models import Language

LANGUAGES = {
    "fr": "Français",
    "en": "English",
    "nl": "Nederlands",
    "it": "Italiano",
    "es": "Español",
}

def run():
    for code, name in LANGUAGES.items():
        lang, created = Language.objects.get_or_create(
            code=code,
            defaults={"name": name, "active": True},
        )

        # sécurité : réactiver si déjà existant mais inactif
        if not created and not lang.active:
            lang.active = True
            lang.save(update_fields=["active"])

        status = "created" if created else "exists"
        print(f"✔ {code} ({name}) → {status}")

    print("✅ Languages initialized")
