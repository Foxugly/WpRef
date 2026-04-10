from __future__ import annotations

from django.contrib.auth import get_user_model
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from core.import_export import (
    ParlerTranslationResourceMixin,
    build_translation_resource_attrs,
)
from language.models import Language

from .models import Domain

User = get_user_model()


def build_domain_resource():
    translated_fields = ("name", "description")
    translation_attrs, translation_columns = build_translation_resource_attrs(translated_fields)
    translation_field_names = tuple(translation_columns.keys())

    attrs = {
        "owner": fields.Field(
            attribute="owner",
            column_name="owner",
            widget=ForeignKeyWidget(User, "username"),
        ),
        "allowed_languages": fields.Field(
            attribute="allowed_languages",
            column_name="allowed_languages",
            widget=ManyToManyWidget(Language, field="code", separator="|"),
        ),
        "managers": fields.Field(
            attribute="managers",
            column_name="managers",
            widget=ManyToManyWidget(User, field="username", separator="|"),
        ),
        "members": fields.Field(
            attribute="members",
            column_name="members",
            widget=ManyToManyWidget(User, field="username", separator="|"),
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
        model = Domain
        import_id_fields = ("id",)
        fields = (
            "id",
            "active",
            "owner",
            "allowed_languages",
            "managers",
            "members",
            "created_at",
            "updated_at",
            *translation_field_names,
        )
        export_order = fields
        skip_unchanged = True

    attrs["Meta"] = Meta

    return type(
        "DomainResource",
        (ParlerTranslationResourceMixin, resources.ModelResource),
        attrs,
    )


DomainResource = build_domain_resource()
