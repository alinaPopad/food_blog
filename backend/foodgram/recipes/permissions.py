from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

from .models import Recipe


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Permission для доступа к рецептам."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if isinstance(obj, Recipe) and request.method == 'POST':
            return True
        if isinstance(obj, Recipe) and request.method == 'DELETE':
            return True
        return obj.author == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permission для персонала."""
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_staff)
