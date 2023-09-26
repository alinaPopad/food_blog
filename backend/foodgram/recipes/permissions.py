from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Permission для доступа к рецептам."""
    def has_permission(self, request, view):
        # Разрешить все методы HTTP для неавторизованных пользователей,
        # для авторизованных - только чтение или создание (POST)
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Разрешить только авторам изменять и удалять объекты
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
