from rest_framework.permissions import BasePermission, SAFE_METHODS

from config.permissions import is_authenticated_user, is_staff_user

from .models import Quiz, QuizAlertThread, QuizQuestion, QuizQuestionAnswer
from .access import user_can_edit_template


class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return is_staff_user(request.user)


class IsStaffOrSuperuser(BasePermission):
    def has_permission(self, request, view):
        return is_staff_user(request.user)


class IsOwnerOrStaff(BasePermission):
    def has_permission(self, request, view):
        return is_authenticated_user(request.user)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not is_authenticated_user(user):
            return False
        if is_staff_user(user):
            return True
        if isinstance(obj, Quiz):
            return obj.user_id == user.id
        if isinstance(obj, QuizQuestionAnswer):
            return bool(obj.quiz_id) and obj.quiz.user_id == user.id
        owner = getattr(obj, "user", None)
        return owner is not None and owner.id == user.id


class IsQuizAlertParticipant(BasePermission):
    def has_permission(self, request, view):
        return is_authenticated_user(request.user)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not is_authenticated_user(user):
            return False
        if is_staff_user(user):
            return True
        if isinstance(obj, QuizAlertThread):
            return obj.is_participant(user)
        thread = getattr(obj, "thread", None)
        if isinstance(thread, QuizAlertThread):
            return thread.is_participant(user)
        return False


class CanManageQuizTemplate(BasePermission):
    def has_permission(self, request, view):
        return is_authenticated_user(request.user)

    def has_object_permission(self, request, view, obj):
        quiz_template = obj
        if isinstance(obj, QuizQuestion):
            quiz_template = obj.quiz
        return user_can_edit_template(request.user, quiz_template)
