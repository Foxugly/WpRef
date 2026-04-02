from __future__ import annotations

from rest_framework.exceptions import PermissionDenied

from .querysets import accessible_quiz_template_queryset

def user_matches_template_domain(user, quiz_template) -> bool:
    if quiz_template.domain_id is None:
        return True
    if getattr(user, "current_domain_id", None) is None:
        return True
    if getattr(user, "current_domain_id", None) == quiz_template.domain_id:
        return True
    if hasattr(user, "can_manage_domain"):
        return user.can_manage_domain(quiz_template.domain)
    return False


def user_can_access_template(user, quiz_template) -> bool:
    if user.is_staff or user.is_superuser:
        return True
    if quiz_template.quiz.filter(user=user).exists():
        return True
    if not quiz_template.is_public:
        return False
    return user_matches_template_domain(user, quiz_template)


def filter_accessible_templates(user, templates):
    if hasattr(templates, "filter"):
        return accessible_quiz_template_queryset(user)
    if user.is_staff or user.is_superuser:
        return templates
    return [quiz_template for quiz_template in templates if user_can_access_template(user, quiz_template)]


def user_can_manage_template_assignments(user, quiz_template) -> bool:
    return bool(
        user
        and (
            user.is_staff
            or user.is_superuser
            or quiz_template.created_by_id == user.id
        )
    )


def user_can_create_quiz_from_template(user, quiz_template) -> bool:
    if user.is_staff or user.is_superuser:
        return True
    if quiz_template.created_by_id == user.id:
        return True
    if not quiz_template.is_public:
        return False
    return user_matches_template_domain(user, quiz_template) or getattr(user, "current_domain_id", None) is None


def validate_target_user_domain(quiz_template, target_user) -> None:
    if quiz_template.domain_id is None:
        return
    if user_matches_template_domain(target_user, quiz_template):
        return
    raise PermissionDenied("L'utilisateur cible n'appartient pas au meme domaine que ce quiz.")
