from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from language.models import Language
from language.serializers import LanguageReadSerializer
from rest_framework import serializers

from .models import Domain

User = get_user_model()
LANG_CODES = {code for code, _ in settings.LANGUAGES}


class DomainReadSerializer(serializers.ModelSerializer):
    # Parler: name/description ne sont pas des champs DB -> SerializerMethodField
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    allowed_languages = LanguageReadSerializer(many=True, read_only=True)

    owner_username = serializers.CharField(source="owner.username", read_only=True)
    staff_usernames = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Domain
        fields = [
            "id",
            "name",
            "description",
            "allowed_languages",
            "active",
            "owner",
            "owner_username",
            "staff_usernames",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_name(self, obj: Domain) -> str:
        return obj.safe_translation_getter("name", any_language=True) or ""

    def get_description(self, obj: Domain) -> str:
        return obj.safe_translation_getter("description", any_language=True) or ""

    def get_staff_usernames(self, obj: Domain) -> List[str]:
        return list(obj.staff.values_list("username", flat=True))


class DomainWriteSerializer(serializers.ModelSerializer):
    """
    Ecriture:
    - translations: {"fr": {"name": "...", "description": "..."}, "nl": {...}}
    - staff_ids: [1, 2, 3]
    - allowed_language_codes: ["fr", "nl"]
    """
    allowed_language_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
    )

    translations = serializers.DictField(
        child=serializers.DictField(),
        write_only=True,
        required=True,
        help_text='Ex: {"fr":{"name":"...","description":""},"nl":{"name":"...","description":""}}',
    )

    staff_ids = serializers.PrimaryKeyRelatedField(
        source="staff",
        queryset=User.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Domain
        fields = [
            "id",
            "translations",
            "allowed_language_codes",
            "active",
            "staff_ids",
        ]
        read_only_fields = ["id"]

    # ---------------------------
    # helpers
    # ---------------------------
    def _apply_translations(self, domain: Domain, translations: dict) -> None:
        for lang_code, data in (translations or {}).items():
            domain.set_current_language(lang_code)
            domain.name = data.get("name", "")
            domain.description = data.get("description", "")
            domain.save()

    # ---------------------------
    # validation
    # ---------------------------
    def validate_allowed_language_codes(self, value):
        value = value or []
        codes = [(c or "").strip().lower() for c in value if (c or "").strip()]
        invalid = [c for c in codes if c not in LANG_CODES]
        if invalid:
            raise serializers.ValidationError(f"Invalid language code(s): {', '.join(invalid)}")
        # dédup ordre
        seen = set()
        uniq = []
        for c in codes:
            if c in seen:
                continue
            seen.add(c)
            uniq.append(c)
        return uniq

    def validate(self, attrs):
        translations = attrs.get("translations")
        if not translations:
            raise serializers.ValidationError({"translations": "Au moins une traduction est requise."})

        # optionnel : imposer que translations couvre allowed_languages
        allowed = set(attrs.get("allowed_language_codes") or [])
        if allowed:
            provided = set(translations.keys())
            missing = allowed - provided
            if missing:
                raise serializers.ValidationError(
                    {"translations": f"Traductions manquantes pour: {sorted(missing)}"}
                )

        return attrs

    # ---------------------------
    # create / update
    # ---------------------------
    def create(self, validated_data):
        translations = validated_data.pop("translations")
        codes = validated_data.pop("allowed_language_codes", None)
        staff = validated_data.pop("staff", [])
        domain = Domain.objects.create(**validated_data)
        if staff:
            domain.staff.set(staff)
        if codes is not None:
            langs = list(Language.objects.filter(code__in=codes))
            domain.allowed_languages.set(langs)
        self._apply_translations(domain, translations)
        return domain

    def update(self, instance, validated_data):
        translations = validated_data.pop("translations", None)
        codes = validated_data.pop("allowed_language_codes", None)
        staff = validated_data.pop("staff", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if staff is not None:
            instance.staff.set(staff)

        if codes is not None:
            langs = list(Language.objects.filter(code__in=codes))
            instance.allowed_languages.set(langs)


        if translations is not None:
            self._apply_translations(instance, translations)

        return instance
