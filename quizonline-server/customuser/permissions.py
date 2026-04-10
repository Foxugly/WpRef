from rest_framework import permissions

from config.permissions import is_authenticated_user, is_django_admin


class IsSelfOrStaffOrSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_authenticated_user(request.user)

    def has_object_permission(self, request, view, obj):
        return is_django_admin(request.user) or obj == request.user


class IsSelf(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_authenticated_user(request.user)

    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsSuperuserOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_authenticated_user(request.user) and bool(getattr(request.user, "is_superuser", False))
