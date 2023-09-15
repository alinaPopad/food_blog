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

from .models import Recipe, User, Follow, Tags
from .serializers import FollowSerializer, RecipeSerializer, TagSerializer
from .permissions import IsAuthorOrReadOnly, IsAuthor
from .filters import RecipeFilter

POST_FILTER = 6


class RecipesViewSet(viewsets.ModelViewSet):  # ++++
    """ViewSet для просмотра и управления рецептами."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER
    search_fields = ('tag',)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        if self.request.user.is_authenticated:
            # Если пользователь авторизован, добавить фильтрацию для него
            filterset = RecipeFilter(
                self.request.query_params,
                queryset=queryset,
                request=self.request
            )
            queryset = filterset.qs
        return queryset


class TagsViewSet(viewsets.ReadOnlyModelViewSet):  # ++++
    """ViewSet для работы с тегами."""
    queryset = Tags.objects.all()
    serializer_class = TagSerializer



























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
    # search_fields = ('following__username',)
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):  # создание подписки
        serializer.save(user=self.request.user)

    def get_queryset(self):  # возвращаем список подписок
        return self.request.user.follower.all()


