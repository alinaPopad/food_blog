import os
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from users.models import CustomUser
from .models import Recipe, Tags, Ingredient, ShoppingList
from .models import Favorites, RecipeIngredient
from .serializers import RecipeSerializer, TagSerializer, IngredientSerializer
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter


POST_FILTER = 6


class RecipesViewSet(viewsets.ModelViewSet):
    """ViewSet для просмотра и управления рецептами."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_class = RecipeFilter
    search_fields = ('tag__slug', 'title',)

    def list(self, request, *args, **kwargs):
        """Получение списка рецептов с фильтрацией."""
        queryset = self.get_queryset()
        if 'tag' in request.query_params:
            queryset = self.filter_class(
                request.query_params, queryset=queryset).qs
        if 'author' in request.query_params:
            queryset = queryset.filter(
                author__id=request.query_params['author'])
        if 'favorite' in request.query_params:
            queryset = self.filter_class(
                request.query_params, queryset=queryset).qs
        if 'shopping_list' in request.query_params:
            queryset = self.filter_class(
                request.query_params, queryset=queryset).qs
        page = self.paginate_queryset(queryset)
        if page:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)

        if page is not None:
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Создание рецепта."""
        if (
            not request.user.is_authenticated or
            not isinstance(request.user, CustomUser)
        ):
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            recipe = serializer.save(author=request.user)
            return Response(
                self.get_serializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        """Получение рецепта по id."""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe)
        return Response(serializer.data)

    def put(self, request, pk=None):
        """Изменение рецепта."""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        recipe = self.get_object_or_404(Recipe, id=pk)
        if request.user != recipe.author:
            return Response({'detail': 'Недостаточно прав.'},
                            status=status.HTTP_403_FORBIDDEN
                            )
        serializer = RecipeSerializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Удаление рецепта."""
        recipe = get_object_or_404(Recipe, id=pk)
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if request.user != recipe.author:
            return Response(
                {'detail': 'Недостаточно прав.'},
                status=status.HTTP_403_FORBIDDEN
            )
        recipe.delete()
        return Response()

    @action(detail=True, methods=['post', 'delete'], url_path='favorites')
    def favorites(self, request, pk=None):
        """Метод для управления избранным."""
        recipe = self.get_object()
        user = request.user

        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if request.method == 'POST':
            # Добавить в избранное
            if Favorites.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже есть в списке избранного.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorites.objects.create(user=user, recipe=recipe)
            return Response(
                {'detail': 'Рецепт добавлен в избранное.'},
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            # Удалить из избранного
            try:
                favorite = Favorites.objects.get(recipe=recipe, user=user)
                favorite.delete()
                return Response(
                    {'detail': 'Рецепт удален из избранного.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            except Favorites.DoesNotExist:
                return Response(
                    {'detail': 'Рецепт не найден в избранном.'},
                    status=status.HTTP_404_NOT_FOUND
                )

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        """Метод для управления списком покупок."""
        recipe = self.get_object()
        user = request.user

        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if request.method == 'POST':
            # Добавление в список покупок
            if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже есть в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingList.objects.create(user=user, recipe=recipe)
            return Response(
                {'detail': 'Рецепт добавлен в список покупок.'},
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            # Удаление из списка покупок
            try:
                favorite = ShoppingList.objects.get(recipe=recipe, user=user)
                favorite.delete()
                return Response(
                    {'detail': 'Рецепт удален из списка покупок.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            except ShoppingList.DoesNotExist:
                return Response(
                    {'detail': 'Рецепт не найден в списке покупок.'},
                    status=status.HTTP_404_NOT_FOUND
                )

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        user = request.user
        recipes_in_shopping_cart = (
            ShoppingList.objects.filter(user=user).
            values_list('recipe', flat=True)
        )
        font_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'dejavu-sans-ttf-2.37/dejavu-sans-ttf-2.37/ttf/DejaVuSans.ttf' 
        )

        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment;'
            'filename="shopping_cart.pdf"'
            )

        pdf = canvas.Canvas(response, pagesize=letter)
        pdf.setTitle('Shopping Cart')

        for recipe_id in recipes_in_shopping_cart:
            recipe = Recipe.objects.get(pk=recipe_id)
            pdf.setFont("DejaVuSans", 12)
            pdf.drawString(100, 700, recipe.name_recipe)

            ingredients = RecipeIngredient.objects.filter(recipe=recipe)
            for ingredient in ingredients:
                pdf.drawString(150, 680, f"{ingredient.ingredient.title}:"
                               f" {ingredient.quantity}"
                               f" {ingredient.ingredient.unit}"
                               )
            pdf.showPage()

        pdf.save()
        return response


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами."""
    queryset = Tags.objects.all()
    serializer_class = TagSerializer

    def list(self, request):
        """Получение списка тегов."""
        tags = self.get_queryset()
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def tag_detail(self, request, pk=None):
        """Получение тега по id."""
        tag = get_object_or_404(Tags, id=pk)
        serializer = self.get_serializer(tag)
        return Response(serializer.data)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентыми."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']

    def list(self, request, *args, **kwargs):
        """Получение списка игредиентов."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Получение ингредиента по id."""
        ingredient = self.get_object()
        serializer = self.get_serializer(ingredient)
        return Response(serializer.data)
