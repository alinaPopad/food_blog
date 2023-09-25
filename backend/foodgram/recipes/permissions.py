from rest_framework import permissions
from rest_framework.permissions import BasePermission

from users.models import Follow


class IsAuthorOrReadOnly(permissions.BasePermission):
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


class IsAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return self.is_author(request, obj)

    def is_author(self, request, obj):
        return obj.author == request.user


class IsNotAlreadyFollowing(permissions.BasePermission):
    message = 'You are already following this user.'

    def has_permission(self, request, view):
        following = request.data.get('following')
        user = request.user
        if following and Follow.objects.filter(
                user=user,
                following=following
        ).exists():
            return False
        return True