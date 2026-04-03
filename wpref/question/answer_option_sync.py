from __future__ import annotations

from collections.abc import Iterable

from rest_framework import serializers

from .models import AnswerOption, Question


def sync_question_answer_options(
    *,
    question: Question,
    answer_options_data: Iterable[dict],
    allowed_langs: set[str],
    upsert_translations,
) -> None:
    existing_options = {option.id: option for option in question.answer_options.all()}
    referenced_existing_ids = set(
        AnswerOption.objects.filter(question=question, quiz_answers__isnull=False)
        .distinct()
        .values_list("id", flat=True)
    )
    retained_ids: set[int] = set()

    for i, raw_option in enumerate(answer_options_data):
        if not isinstance(raw_option, dict):
            raise serializers.ValidationError({f"answer_options[{i}]": "Each item must be an object."})

        option_translations = raw_option.get("translations") or {}
        if not isinstance(option_translations, dict):
            raise serializers.ValidationError(
                {f"answer_options[{i}].translations": "Must be an object keyed by language code."}
            )

        option_payload = dict(raw_option)
        option_id = option_payload.pop("id", None)
        option_payload.pop("translations", None)

        if option_id is not None:
            option = existing_options.get(option_id)
            if option is None:
                raise serializers.ValidationError(
                    {f"answer_options[{i}].id": "Unknown answer option for this question."}
                )
            if option_id in retained_ids:
                raise serializers.ValidationError(
                    {f"answer_options[{i}].id": "Duplicate answer option id in payload."}
                )
            new_is_correct = option_payload.get("is_correct", option.is_correct)
            if option_id in referenced_existing_ids and bool(new_is_correct) != bool(option.is_correct):
                raise serializers.ValidationError(
                    {
                        "answer_options": (
                            "Impossible de modifier le statut correcte/incorrecte "
                            f"de reponses deja utilisees dans des quiz: [{option_id}]"
                        )
                    }
                )
            for attr, value in option_payload.items():
                setattr(option, attr, value)
            option.save()
            retained_ids.add(option_id)
        else:
            option = AnswerOption.objects.create(question=question, **option_payload)
            retained_ids.add(option.id)

        upsert_translations(
            option,
            {lang_code: option_translations.get(lang_code, {}) for lang_code in allowed_langs},
            fields=["content"],
        )

    removable_ids = set(existing_options) - retained_ids
    if removable_ids:
        referenced_ids = sorted(referenced_existing_ids.intersection(removable_ids))
        if referenced_ids:
            raise serializers.ValidationError(
                {
                    "answer_options": (
                        "Impossible de supprimer des reponses deja utilisees dans des quiz: "
                        f"{referenced_ids}"
                    )
                }
            )
        AnswerOption.objects.filter(id__in=removable_ids).delete()
