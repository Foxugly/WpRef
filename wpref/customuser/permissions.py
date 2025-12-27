from rest_framework import permissions


class IsSelfOrStaffOrSuperuser(permissions.BasePermission):

    def has_permission(self, request, view):
        # On exige d'être loggé pour accéder à la vue
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        return (user.is_staff or user.is_superuser or obj == user)


class IsSelf(permissions.BasePermission):

    def has_permission(self, request, view):
        # On exige d'être loggé pour accéder à la vue
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        return (obj == user)
