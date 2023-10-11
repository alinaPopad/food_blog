import os

from rest_framework import filters
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from users.models import CustomUser
from .filters import RecipeFilter, IngredientFilter
from .models import Recipe, Tags, Ingredient, ShoppingList
from .models import Favorites, RecipeIngredient
from .pagination import DefaultPagination
from .permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from .serializers import RecipeSerializer, TagSerializer
from .serializers import IngredientSerializer, PublicRecipeSerializer
from .serializers import CreateUpdateRecipeSerializer


class RecipesViewSet(viewsets.ModelViewSet):
    """ViewSet для просмотра и управления рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)
    pagination_class = DefaultPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от метода."""
        if self.action == 'create' or self.action == 'partial_update':
            return CreateUpdateRecipeSerializer
        elif self.action in ('list', 'retrieve'):
            if not self.request.user.is_authenticated:
                return PublicRecipeSerializer
            return RecipeSerializer

    def get_queryset(self):
        """Получение queryset."""
        queryset = Recipe.objects.all()
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(
                self.request, queryset,
                view=self
            )
        print(self.request.query_params)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def list(self, request, *args, **kwargs):
        """Метод для просмотра рецептов на главной странице."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'recipes': serializer.data})

    def create(self, request, *args, **kwargs):
        """Создание рецепта."""
        if (
            not request.user.is_authenticated
            or not isinstance(request.user, CustomUser)
        ):
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            recipe_id = serializer.instance.id
            return Response(
                {'detail': 'Recipe created successfully',
                 'recipe_id': recipe_id},
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
        print("Request data:", request.data)
        serializer = CreateUpdateRecipeSerializer(recipe, data=request.data)
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
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
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
            settings.BASE_DIR,
            'recipes/fonts/DejaVuSans.ttf'
        )
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment;'
            'filename="shopping_cart.pdf"'
        )

        pdf = canvas.Canvas(response, pagesize=letter)
        pdf.setTitle('Shopping Cart')
        pdf.setFont("DejaVuSans", 16)
        pdf.drawString(100, 750, "Ваш список покупок.")
        ingredient_list = []

        for recipe_id in recipes_in_shopping_cart:
            recipe = Recipe.objects.get(pk=recipe_id)
            pdf.setFont("DejaVuSans", 12)

            ingredients = RecipeIngredient.objects.filter(recipe=recipe)
            for ingredient in ingredients:
                ingredient_name = ingredient.ingredient.name
                ingredient_amount = ingredient.amount
                measurement_unit = ingredient.ingredient.measurement_unit

                existing_ingredient = next((
                    i for i in ingredient_list if i['name'] == ingredient_name
                ),
                    None
                )

                if existing_ingredient:
                    existing_ingredient['amount'] += ingredient_amount
                else:
                    ingredient_list.append({
                        'name': ingredient_name,
                        'amount': ingredient_amount,
                        'measurement_unit': measurement_unit,
                    })

        pdf.setFont("DejaVuSans", 12)
        y = 700
        for ingredient in ingredient_list:
            ingredient_name = ingredient['name']
            ingredient_amount = ingredient['amount']
            measurement_unit = ingredient['measurement_unit']
            ingredient_string = (
                f"{ingredient_name}: {ingredient_amount} {measurement_unit}"
            )
            pdf.drawString(100, y, ingredient_string)
            y -= 20

        pdf.save()
        return response


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами."""
    queryset = Tags.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)

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
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    permission_classes = (IsAdminOrReadOnly,)
