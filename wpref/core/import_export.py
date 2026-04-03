from __future__ import annotations

from collections.abc import Iterable

from django.conf import settings
from import_export import fields


def build_translation_resource_attrs(
    translated_fields: Iterable[str],
) -> tuple[dict[str, fields.Field], dict[str, tuple[str, str]]]:
    attrs: dict[str, fields.Field] = {}
    translation_columns: dict[str, tuple[str, str]] = {}

    for lang_code, _ in settings.LANGUAGES:
        for field_name in translated_fields:
            column_name = f"{field_name}_{lang_code}"
            attrs[column_name] = fields.Field(
                column_name=column_name,
                dehydrate_method=f"dehydrate_{column_name}",
            )
            translation_columns[column_name] = (lang_code, field_name)

    return attrs, translation_columns


class ParlerTranslationResourceMixin:
    translation_columns: dict[str, tuple[str, str]] = {}

    def _dehydrate_translation(self, obj, language_code: str, field_name: str) -> str:
        return obj.safe_translation_getter(
            field_name,
            language_code=language_code,
            any_language=False,
        ) or ""

    def after_save_instance(self, instance, row, **kwargs):
        updated = False

        for column_name, (language_code, field_name) in self.translation_columns.items():
            if column_name not in row:
                continue

            value = row.get(column_name)
            if value is None:
                continue

            instance.set_current_language(language_code)
            setattr(instance, field_name, value)
            updated = True

        if updated and not kwargs.get("dry_run", False):
            instance.save()

        return super().after_save_instance(instance, row, **kwargs)
