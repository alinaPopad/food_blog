from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter
from rest_framework import permissions
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import Recipe, User, Follow
from .forms import RecipeForm
from .serializers import FollowSerializer, RecipeSerializer
from .permissions import IsAuthorOrReadOnly, IsAuthor

POST_FILTER = 6


class RecipesViewSet(viewsets.ModelViewSet):
    """ViewSet для неавторизованного пользователя."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER

    def list(self, request, *args, **kwargs):  # просмотр списка
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):  # просмотр одного рецепта
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def user_profile(self, request, *args, **kwargs):  # просмотр страницы 
        try:
            user = User.objects.get(username=username) # автора с рецептами
        except User.DoesNotExist:
            return Response(
                {"error": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        user_data = {
            "username": user.username,
        }
        return Response(user_data)


class FollowViewSet(mixins.CreateModelMixin, 
                    mixins.RetrieveModelMixin,
                    mixins.ListModelMixin,
                    mixins.DestroyModelMixin,  # делаем отписку
                    viewsets.GenericViewSet):
    """ViewSet для подписки авторизованного пользователя."""
    serializer_class = FollowSerializer
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER
    filter_backends = (SearchFilter,)
    search_fields = ('following__username',)
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):  # создание подписки
        serializer.save(user=self.request.user)

    def get_queryset(self):  # возвращаем список подписок
        return self.request.user.follower.all()


class AuthUservViewSet(mixins.CreateModelMixin,  # создание/удаление/редактирование
                       mixins.DestroyModelMixin,  # для автора
                       mixins.UpdateModelMixin,
                       ):
    """ViewSet для авторизованных пользователей."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthor,)
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER
    search_fields = ('tag',)
