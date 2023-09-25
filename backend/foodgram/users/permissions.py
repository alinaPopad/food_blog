from rest_framework.permissions import BasePermission


class AllowAnyGet(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        return True  # Разрешить все остальные методы для всех пользователей
