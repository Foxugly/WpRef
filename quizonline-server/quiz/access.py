from __future__ import annotations

from rest_framework.exceptions import PermissionDenied
from config.domain_access import manageable_domain_ids, user_can_access_domain

from .querysets import accessible_quiz_template_queryset


def user_matches_template_domain(user, quiz_template) -> bool:
    return user_can_access_domain(user, quiz_template.domain_id)


def user_manages_template_domain(user, quiz_template) -> bool:
    if quiz_template.domain_id is None:
        return True
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return quiz_template.domain_id in manageable_domain_ids(user)


def _has_started_exam_attempt(user, quiz_template) -> bool:
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and quiz_template.mode == quiz_template.MODE_EXAM
        and quiz_template.quiz.filter(user=user).exclude(started_at__isnull=True, ended_at__isnull=True).exists()
    )


def _can_access_public_template(user, quiz_template) -> bool:
    if not quiz_template.is_public or not quiz_template.can_answer:
        return False
    if _has_started_exam_attempt(user, quiz_template):
        return False
    return True


def user_can_access_template(user, quiz_template) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return _can_access_public_template(user, quiz_template)
    if user.is_superuser:
        return True
    if user_manages_template_domain(user, quiz_template):
        return True
    if not quiz_template.can_answer:
        return False
    if _has_started_exam_attempt(user, quiz_template):
        return False
    if quiz_template.quiz.filter(user=user).exists():
        return True
    return _can_access_public_template(user, quiz_template)


def filter_accessible_templates(user, templates):
    if hasattr(templates, "filter"):
        return accessible_quiz_template_queryset(user)
    if user.is_superuser:
        return templates
    return [quiz_template for quiz_template in templates if user_can_access_template(user, quiz_template)]


def user_can_manage_template_assignments(user, quiz_template) -> bool:
    return bool(
        user
        and (
            user.is_superuser
            or user_manages_template_domain(user, quiz_template)
        )
    )


def user_can_create_quiz_from_template(user, quiz_template) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    if user_manages_template_domain(user, quiz_template):
        return True
    if not quiz_template.can_answer:
        return False
    if _has_started_exam_attempt(user, quiz_template):
        return False
    if quiz_template.quiz.filter(user=user).exists():
        return True
    return _can_access_public_template(user, quiz_template)


def user_can_edit_template(user, quiz_template) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user_manages_template_domain(user, quiz_template)


def user_can_delete_template(user, quiz_template) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    if user_manages_template_domain(user, quiz_template):
        return True
    return quiz_template.created_by_id == getattr(user, "id", None)


def validate_target_user_domain(quiz_template, target_user) -> None:
    if quiz_template.domain_id is None:
        return
    if user_matches_template_domain(target_user, quiz_template):
        return
    raise PermissionDenied("L'utilisateur cible n'appartient pas au meme domaine que ce quiz.")
