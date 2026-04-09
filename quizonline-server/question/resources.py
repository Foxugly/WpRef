from __future__ import annotations

from django.conf import settings
from django.utils import translation as django_translation
from import_export import fields, resources
from import_export.widgets import ManyToManyWidget

from core.import_export import (
    ParlerTranslationResourceMixin,
    build_translation_resource_attrs,
)
from domain.models import Domain
from subject.models import Subject

from .models import Question


class DomainByNameWidget:
    """
    Widget ForeignKey sur Domain via son nom traduit.
    Export  → nom du domaine.
    Import  → lookup par translations__name ; erreur si introuvable.
    """

    def render(self, value, obj=None):
        if not value:
            return ""
        return value.safe_translation_getter("name", any_language=True) or str(value.pk)

    def clean(self, value, row=None, **kwargs):
        if not value:
            return None
        value = value.strip()
        try:
            return Domain.objects.get(translations__name=value)
        except Domain.DoesNotExist:
            raise ValueError(f"Le domaine « {value} » n'existe pas.")
        except Domain.MultipleObjectsReturned:
            # Plusieurs domaines ont ce nom dans des langues différentes : on prend le premier
            return Domain.objects.filter(translations__name=value).first()


class SubjectsByNameWidget(ManyToManyWidget):
    """
    Widget ManyToMany sur Subject via les noms traduits, séparés par '|'.
    Export  → noms des subjects.
    Import  → lookup par nom + domaine ; création si introuvable.
    """

    separator = "|"

    def render(self, value, obj=None):
        if not value:
            return ""
        return self.separator.join(
            s.safe_translation_getter("name", any_language=True) or str(s.pk)
            for s in value.all()
        )

    def clean(self, value, row=None, **kwargs):
        if not value:
            return Subject.objects.none()

        names = [v.strip() for v in str(value).split(self.separator) if v.strip()]
        if not names:
            return Subject.objects.none()

        # Résoudre le domaine à partir de la colonne "domain" de la ligne
        domain_name = (row or {}).get("domain", "").strip()
        domain = Domain.objects.filter(translations__name=domain_name).first() if domain_name else None

        lang = django_translation.get_language() or settings.LANGUAGE_CODE
        subject_pks = []

        for name in names:
            if domain:
                existing = Subject.objects.filter(
                    translations__name=name, domain=domain
                ).first()
                if not existing:
                    existing = Subject.objects.create(domain=domain)
                    existing.set_current_language(lang)
                    existing.name = name
                    existing.save()
            else:
                existing = Subject.objects.filter(translations__name=name).first()
                if not existing:
                    continue
            subject_pks.append(existing.pk)

        return Subject.objects.filter(pk__in=subject_pks)


def build_question_resource():
    translated_fields = ("title", "description", "explanation")
    translation_attrs, translation_columns = build_translation_resource_attrs(translated_fields)
    translation_field_names = tuple(translation_columns.keys())

    attrs = {
        "domain": fields.Field(
            attribute="domain",
            column_name="domain",
            widget=DomainByNameWidget(),
        ),
        "subjects": fields.Field(
            attribute="subjects",
            column_name="subjects",
            widget=SubjectsByNameWidget(Subject),
        ),
        "translation_columns": translation_columns,
        "__module__": __name__,
    }
    attrs.update(translation_attrs)

    for column_name, (language_code, field_name) in translation_columns.items():
        def dehydrate(self, obj, lang=language_code, field=field_name):
            return self._dehydrate_translation(obj, lang, field)

        attrs[f"dehydrate_{column_name}"] = dehydrate

    def before_import(self, dataset, **kwargs):
        """Vérifie que tous les domaines référencés existent avant d'importer."""
        domain_names = {
            row.get("domain", "").strip()
            for row in dataset.dict
            if row.get("domain", "").strip()
        }
        if domain_names:
            existing = set(
                Domain.objects.filter(translations__name__in=domain_names)
                .values_list("translations__name", flat=True)
                .distinct()
            )
            missing = domain_names - existing
            if missing:
                raise ValueError(
                    f"Import annulé. Domaine(s) introuvable(s) : {', '.join(sorted(missing))}"
                )
        resources.ModelResource.before_import(self, dataset, **kwargs)

    attrs["before_import"] = before_import

    class Meta:
        model = Question
        import_id_fields = ("id",)
        fields = (
            "id",
            "domain",
            "subjects",
            "active",
            "allow_multiple_correct",
            "is_mode_practice",
            "is_mode_exam",
            "created_at",
            "updated_at",
            *translation_field_names,
        )
        export_order = fields
        skip_unchanged = True

    attrs["Meta"] = Meta

    return type(
        "QuestionResource",
        (ParlerTranslationResourceMixin, resources.ModelResource),
        attrs,
    )


QuestionResource = build_question_resource()
