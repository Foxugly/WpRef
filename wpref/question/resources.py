from __future__ import annotations

from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from core.import_export import (
    ParlerTranslationResourceMixin,
    build_translation_resource_attrs,
)
from domain.models import Domain
from subject.models import Subject

from .models import Question


def build_question_resource():
    translated_fields = ("title", "description", "explanation")
    translation_attrs, translation_columns = build_translation_resource_attrs(translated_fields)
    translation_field_names = tuple(translation_columns.keys())

    attrs = {
        "domain": fields.Field(
            attribute="domain",
            column_name="domain",
            widget=ForeignKeyWidget(Domain, "id"),
        ),
        "subjects": fields.Field(
            attribute="subjects",
            column_name="subjects",
            widget=ManyToManyWidget(Subject, field="id", separator="|"),
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
