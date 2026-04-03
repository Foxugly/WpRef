from __future__ import annotations

from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from core.import_export import (
    ParlerTranslationResourceMixin,
    build_translation_resource_attrs,
)
from domain.models import Domain

from .models import Subject


def build_subject_resource():
    translated_fields = ("name", "description")
    translation_attrs, translation_columns = build_translation_resource_attrs(translated_fields)
    translation_field_names = tuple(translation_columns.keys())

    attrs = {
        "domain": fields.Field(
            attribute="domain",
            column_name="domain",
            widget=ForeignKeyWidget(Domain, "id"),
        ),
        "translation_columns": translation_columns,
        "__module__": __name__,
    }
    attrs.update(translation_attrs)

    for column_name, (language_code, field_name) in translation_columns.items():
        def dehydrate(self, obj, lang=language_code, field=field_name):
            return self._dehydrate_translation(obj, lang, field)

        attrs[f"dehydrate_{column_name}"] = dehydrate

    class Meta:
        model = Subject
        import_id_fields = ("id",)
        fields = (
            "id",
            "domain",
            "active",
            "created_at",
            "updated_at",
            *translation_field_names,
        )
        export_order = fields
        skip_unchanged = True

    attrs["Meta"] = Meta

    return type(
        "SubjectResource",
        (ParlerTranslationResourceMixin, resources.ModelResource),
        attrs,
    )


SubjectResource = build_subject_resource()
