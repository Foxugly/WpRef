from __future__ import annotations

import json
import hashlib

from django.conf import settings
from django.db import transaction
from django.utils import translation as django_translation

from domain.models import Domain
from subject.models import Subject

from .models import AnswerOption, Question


# ──────────────────────────────────────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class StructuredImportError(Exception):
    pass


class StructuredImportPermissionError(StructuredImportError):
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def translations_hash(translations: dict) -> str:
    normalized = json.dumps(translations, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def _domain_hash(domain: Domain) -> str:
    trans = {
        t.language_code: {
            "name": t.name or "",
            "description": getattr(t, "description", "") or "",
        }
        for t in domain.translations.all()
    }
    return translations_hash(trans)


def _subject_hash(subject: Subject) -> str:
    trans = {
        t.language_code: {"name": t.name or ""}
        for t in subject.translations.all()
    }
    return translations_hash(trans)


def _apply_translations(instance, translations: dict, fields: list[str]) -> None:
    """Applique les traductions parler sur une instance (déjà sauvegardée)."""
    for lang_code, payload in translations.items():
        instance.set_current_language(lang_code)
        for field in fields:
            if field in payload:
                setattr(instance, field, payload[field])
        instance.save()


# ──────────────────────────────────────────────────────────────────────────────
# Résolution Domain / Subject
# ──────────────────────────────────────────────────────────────────────────────

def _resolve_domain(domain_data: dict, user) -> tuple[Domain, bool]:
    """
    Retourne (domain, created).
    - Hash présent  → recherche par hash ; si trouvé remappe l'id, sinon crée.
    - Hash absent   → toujours création.
    Création requiert is_superuser.
    """
    domain_hash = domain_data.get("hash")
    translations = domain_data.get("translations", {})

    if domain_hash:
        for d in Domain.objects.prefetch_related("translations").all():
            if _domain_hash(d) == domain_hash:
                return d, False

    # Création
    if not getattr(user, "is_superuser", False):
        raise StructuredImportPermissionError(
            "Seul un superutilisateur peut créer un domaine. "
            "Aucun domaine correspondant au hash fourni n'a été trouvé."
        )
    domain = Domain(owner=user, created_by=user, updated_by=user)
    domain.save()
    _apply_translations(domain, translations, ["name", "description"])
    return domain, True


def _resolve_subject(subject_data: dict, domain: Domain, user) -> tuple[Subject, bool]:
    """
    Retourne (subject, created).
    - Hash présent  → recherche par hash dans le domaine résolu.
    - Hash absent   → toujours création.
    Création requiert is_staff ou is_superuser.
    """
    subject_hash = subject_data.get("hash")
    translations = subject_data.get("translations", {})

    if subject_hash:
        for s in Subject.objects.filter(domain=domain).prefetch_related("translations"):
            if _subject_hash(s) == subject_hash:
                return s, False

    # Création
    if not (getattr(user, "is_superuser", False) or getattr(user, "is_staff", False)):
        raise StructuredImportPermissionError(
            "Vous devez être staff pour créer un subject."
        )
    subject = Subject.objects.create(domain=domain)
    _apply_translations(subject, translations, ["name"])
    return subject, True


# ──────────────────────────────────────────────────────────────────────────────
# Sync answer options
# ──────────────────────────────────────────────────────────────────────────────

def _sync_answer_options(question: Question, options_data: list[dict]) -> None:
    existing = {opt.pk: opt for opt in question.answer_options.all()}
    referenced_ids = set(
        question.answer_options.filter(quiz_answers__isnull=False)
        .values_list("pk", flat=True)
        .distinct()
    )
    kept_ids: set[int] = set()

    for opt_data in options_data:
        opt_id = opt_data.get("id")
        is_correct = opt_data.get("is_correct", False)
        sort_order = opt_data.get("sort_order", 0)
        opt_translations = opt_data.get("translations", {})

        opt: AnswerOption | None = existing.get(opt_id) if opt_id else None

        if opt is None:
            opt = AnswerOption.objects.create(
                question=question,
                is_correct=is_correct,
                sort_order=sort_order,
            )
        else:
            opt.sort_order = sort_order
            if opt.pk not in referenced_ids:
                opt.is_correct = is_correct
            opt.save()

        kept_ids.add(opt.pk)
        _apply_translations(opt, opt_translations, ["content"])

    # Supprime les options absentes du payload (sauf celles référencées)
    removable = set(existing) - kept_ids - referenced_ids
    if removable:
        AnswerOption.objects.filter(pk__in=removable).delete()


# ──────────────────────────────────────────────────────────────────────────────
# Point d'entrée principal
# ──────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def import_questions(data: dict, user) -> dict:
    """
    Importe des questions depuis le format d'export structuré.
    Retourne un résumé de l'opération.
    Tout est dans une transaction atomique : une erreur annule tout.
    """
    if data.get("version") != "1.0":
        raise StructuredImportError("Version non supportée. Attendu : 1.0")

    domain_data = data.get("domain")
    subjects_data = data.get("subjects", [])
    questions_data = data.get("questions", [])

    if not domain_data:
        raise StructuredImportError("Clé 'domain' manquante dans le fichier.")

    export_domain_id: int = domain_data["id"]

    # ── Domaine ────────────────────────────────────────────────────────────────
    resolved_domain, domain_created = _resolve_domain(domain_data, user)
    domain_id_map: dict[int, int] = {export_domain_id: resolved_domain.pk}

    # ── Subjects ───────────────────────────────────────────────────────────────
    subject_id_map: dict[int, int] = {}
    subjects_created = 0

    for subject_data in subjects_data:
        export_subject_id: int = subject_data["id"]
        resolved_subject, created = _resolve_subject(subject_data, resolved_domain, user)
        subject_id_map[export_subject_id] = resolved_subject.pk
        if created:
            subjects_created += 1

    # ── Questions ──────────────────────────────────────────────────────────────
    questions_created = 0
    questions_updated = 0

    for q_data in questions_data:
        real_domain_id = domain_id_map.get(q_data["domain_id"], q_data["domain_id"])
        real_subject_ids = [
            subject_id_map.get(sid, sid) for sid in q_data.get("subject_ids", [])
        ]
        q_translations = q_data.get("translations", {})
        answer_options_data = q_data.get("answer_options", [])
        export_q_id = q_data.get("id")

        question: Question | None = None
        if export_q_id:
            question = Question.objects.filter(pk=export_q_id).first()

        if question is None:
            question = Question(
                domain_id=real_domain_id,
                active=q_data.get("active", True),
                allow_multiple_correct=q_data.get("allow_multiple_correct", False),
                is_mode_practice=q_data.get("is_mode_practice", True),
                is_mode_exam=q_data.get("is_mode_exam", False),
                created_by=user,
                updated_by=user,
            )
            question.save()
            questions_created += 1
        else:
            question.domain_id = real_domain_id
            question.active = q_data.get("active", question.active)
            question.allow_multiple_correct = q_data.get(
                "allow_multiple_correct", question.allow_multiple_correct
            )
            question.is_mode_practice = q_data.get("is_mode_practice", question.is_mode_practice)
            question.is_mode_exam = q_data.get("is_mode_exam", question.is_mode_exam)
            question.updated_by = user
            question.save()
            questions_updated += 1

        _apply_translations(question, q_translations, ["title", "description", "explanation"])
        question.subjects.set(real_subject_ids)
        _sync_answer_options(question, answer_options_data)

    return {
        "domain_created": domain_created,
        "domain_id": resolved_domain.pk,
        "domain_remapped": resolved_domain.pk != export_domain_id,
        "subjects_created": subjects_created,
        "subject_remaps": {k: v for k, v in subject_id_map.items() if k != v},
        "questions_created": questions_created,
        "questions_updated": questions_updated,
    }
