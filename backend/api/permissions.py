from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

from recipes.models import Recipe
from users.models import CustomUser


class IsSafeMethod(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class IsRecipeAuthor(IsAuthor):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Recipe):
            return super().has_object_permission(request, view, obj)
        return False


class IsRecipeAuthorOrSafe(IsRecipeAuthor, IsSafeMethod):
    """Permission объединяющий общую логику."""
    pass


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permission для персонала."""
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_staff)


class IsAuthenticatedCustomUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and isinstance(request.user, CustomUser)
        )


class IsAuthenticatedForList(IsAuthenticatedCustomUser):
    def has_permission(self, request, view):
        if view.action in ('list', 'retrieve'):
            return True
        return super().has_permission(request, view)
