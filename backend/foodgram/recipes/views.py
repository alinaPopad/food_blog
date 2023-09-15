from rest_framework import viewsets, mixins, filters
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
from rest_framework.decorators import action

from .models import Recipe, User, Follow, Tags, Ingredient, ShoppingList, Favorites
from .serializers import FavoritesSerializer, FollowSerializer, RecipeSerializer, TagSerializer, IngredientSerializer, ShoppingListSerializer
from .permissions import IsAuthorOrReadOnly, IsAuthor
from .filters import RecipeFilter
from reportlab.pdfgen import canvas

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


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентыми."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']  # поиск по частичноми вхождению

"""
class ShoppingListViewSet(viewsets.ModelViewSet):
    queryset = ShoppingList.objects.all()
    serializer_class = ShoppingListSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        recipe = Recipe.objects.get(pk=pk)
        pdf = canvas.Canvas(ShoppingList)
        while line in recipe:


        pdf.setTitle(Recipe.name_recipe)
     
        # ...
        # return Response(file_data, content_type='application/pdf')
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)  

    @action(detail=True, methods=['post'])
    def add_to_shopping_cart(self, request, pk):
        recipe = Recipe.objects.get(pk=pk)
        shopping_list_item, created = ShoppingList.objects.get_or_create(user=request.user, recipe=recipe)
        if not created:
            return Response({"detail": "Рецепт уже в списке покупок"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_201_CREATED)

        
        def add_to_favorites(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        Favorites.objects.create(user=user, recipe=recipe)
        return Response()
 

    @action(detail=True, methods=['delete'])
    def remove_from_shopping_cart(self, request, pk):
        # Здесь вам нужно реализовать удаление рецепта из списка покупок для текущего пользователя
        # Пример:
        # recipe = Recipe.objects.get(pk=pk)
        # ShoppingList.objects.filter(user=request.user, recipe=recipe).delete()
        # return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)  

"""


class FavoritesViewSet(viewsets.ModelViewSet):  # только авторизованный пользователь 
    """ViewSet для работы с избранным."""  # может добавлять или удалять рецепты в избранном
    queryset = Favorites.objects.all()
    serializer_class = FavoritesSerializer
    permission_classes = (IsAuthenticated,)

    # Добавление нового рецепта в раздел
    @action(detail=True, methods=['post'])
    def add_to_favorites(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        Favorites.objects.create(user=user, recipe=recipe)
        return Response()

    # Удаление рецепта из раздела
    @action(detail=True, methods=['delete'])
    def remove_from_favorites(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        try:
            favorite = Favorites.objects.get(recipe=recipe, user=user)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Favorites.DoesNotExist:
            return Response({"detail": "Рецепт не найден в избранном"}, status=status.HTTP_400_BAD_REQUEST)





















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


