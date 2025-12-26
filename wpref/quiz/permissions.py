# quiz/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Quiz, QuizQuestionAnswer


class IsStaffOrReadOnly(BasePermission):
    """
    - Staff / superuser : tous droits
    - Autres : lecture seule (GET, HEAD, OPTIONS)
    Utile si tu veux un fallback générique.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


class IsOwnerOrStaff(BasePermission):
    """
    Pour les objets liés à un utilisateur :
    - Staff / superuser : accès complet
    - Sinon : uniquement si l'objet appartient à request.user
      (Quiz.user ou QuizQuestionAnswer.quiz.user)
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_staff or user.is_superuser:
            return True

        # Quiz : appartient à obj.user
        if isinstance(obj, Quiz):
            return obj.user_id == user.id

        # QuizQuestionAnswer : appartient au propriétaire du quiz
        if isinstance(obj, QuizQuestionAnswer):
            if obj.quiz_id is None:
                return False
            return obj.quiz.user_id == user.id

        # fallback générique : attribut "user"
        owner = getattr(obj, "user", None)
        return owner is not None and owner.id == user.id
