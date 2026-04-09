from __future__ import annotations

import hashlib
import json

from django.utils import timezone

from domain.models import Domain
from subject.models import Subject

from .models import AnswerOption, Question


def translations_hash(translations: dict) -> str:
    """16-char SHA-256 fingerprint of a translations dict (keys sorted)."""
    normalized = json.dumps(translations, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def _domain_translations(domain: Domain) -> dict:
    return {
        t.language_code: {
            "name": t.name or "",
            "description": getattr(t, "description", "") or "",
        }
        for t in domain.translations.all()
    }


def _subject_translations(subject: Subject) -> dict:
    return {
        t.language_code: {"name": t.name or ""}
        for t in subject.translations.all()
    }


def _question_translations(question: Question) -> dict:
    return {
        t.language_code: {
            "title": t.title or "",
            "description": t.description or "",
            "explanation": t.explanation or "",
        }
        for t in question.translations.all()
    }


def _answer_option_translations(option: AnswerOption) -> dict:
    return {
        t.language_code: {"content": t.content or ""}
        for t in option.translations.all()
    }


def export_questions(queryset) -> dict:
    """
    Serialise un queryset de Question vers le format d'export structuré.
    Toutes les questions doivent appartenir au même domaine.
    """
    questions = list(
        queryset
        .select_related("domain")
        .prefetch_related(
            "domain__translations",
            "subjects__translations",
            "translations",
            "answer_options__translations",
        )
        .order_by("pk")
    )

    if not questions:
        return {
            "version": "1.0",
            "exported_at": timezone.now().isoformat(),
            "domain": None,
            "subjects": [],
            "questions": [],
        }

    domain = questions[0].domain
    domain_trans = _domain_translations(domain)

    subject_map: dict[int, Subject] = {}
    for q in questions:
        for s in q.subjects.all():
            subject_map[s.pk] = s

    subjects_data = [
        {
            "id": s.pk,
            "hash": translations_hash(_subject_translations(s)),
            "translations": _subject_translations(s),
        }
        for s in subject_map.values()
    ]

    questions_data = []
    for q in questions:
        answer_options_data = [
            {
                "id": opt.pk,
                "sort_order": opt.sort_order,
                "is_correct": opt.is_correct,
                "translations": _answer_option_translations(opt),
            }
            for opt in sorted(q.answer_options.all(), key=lambda o: (o.sort_order, o.pk))
        ]
        questions_data.append({
            "id": q.pk,
            "domain_id": domain.pk,
            "subject_ids": sorted(q.subjects.values_list("pk", flat=True)),
            "active": q.active,
            "allow_multiple_correct": q.allow_multiple_correct,
            "is_mode_practice": q.is_mode_practice,
            "is_mode_exam": q.is_mode_exam,
            "translations": _question_translations(q),
            "answer_options": answer_options_data,
        })

    return {
        "version": "1.0",
        "exported_at": timezone.now().isoformat(),
        "domain": {
            "id": domain.pk,
            "hash": translations_hash(domain_trans),
            "translations": domain_trans,
        },
        "subjects": subjects_data,
        "questions": questions_data,
    }
