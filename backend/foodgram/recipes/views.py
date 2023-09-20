from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter
from rest_framework import permissions
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action

from .models import Recipe, User, Tags, Ingredient, ShoppingList, Favorites, RecipeIngredient
from .serializers import FavoritesSerializer, RecipeSerializer, TagSerializer, IngredientSerializer, ShoppingListSerializer
from .permissions import IsAuthorOrReadOnly, IsAuthor
from .filters import RecipeFilter
from reportlab.pdfgen import canvas
from django.http import HttpResponse



POST_FILTER = 6


class RecipesViewSet(viewsets.ModelViewSet):
    """ViewSet для просмотра и управления рецептами."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER
    filter_backends = (
        RecipeFilter,
        filters.SearchFilter,
    )
    filter_class = RecipeFilter
    search_fields = ('tag__slug', 'title',)

    def list(self, request, *args, **kwargs):  # список рецептов
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):  # создание рецепта
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            recipe = serializer.save(author=request.user)
            return Response(self.get_serializer(recipe).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):  # получение рецепта по id
        recipe = self.get_object()
        serializer = self.get_serializer(recipe)
        return Response(serializer.data)

    def put(self, request, pk=None):  # изменение рецепта
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})
        recipe = self.get_object_or_404(Recipe, id=pk)
        if request.user != recipe.author:
            return Response({'detail': 'Недостаточно прав.'})
        serializer = RecipeSerializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):  # удаление рецепта
        recipe = self.get_object_or_404(Recipe, id=pk)
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})
        if request.user != recipe.author:
            return Response({'detail': 'Недостаточно прав.'})
        recipe.delete()
        return Response()


class TagsViewSet(viewsets.ReadOnlyModelViewSet):  # ++++
    """ViewSet для работы с тегами."""
    queryset = Tags.objects.all()
    serializer_class = TagSerializer

    def list(self, request):  # список тегов
        tags = self.get_queryset()
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def tag_detail(self, request, pk=None):  # поиск по тегу
        tag = get_object_or_404(Tags, id=pk)
        serializer = self.get_serializer(tag)
        return Response(serializer.data)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентыми."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']

    def list(self, request, *args, **kwargs):  # получение списка ингредиентов
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):  # полчение игредиента по id
        ingredient = self.get_object()
        serializer = self.get_serializer(ingredient)
        return Response(serializer.data)


class ShoppingListViewSet(viewsets.ModelViewSet):
    queryset = ShoppingList.objects.all()
    serializer_class = ShoppingListSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):  # Скачать файл со списком покупок
        user = request.user
        recipes_in_shopping_cart = ShoppingList.objects.filter(user=user).values_list('recipe', flat=True)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.pdf"'

        pdf = canvas.Canvas(response, pagesize=letter)
        pdf.setTitle('Shopping Cart')

        for recipe_id in recipes_in_shopping_cart:
            recipe = Recipe.objects.get(pk=recipe_id)
            pdf.drawString(100, 700, recipe.name_recipe)

            ingredients = RecipeIngredient.objects.filter(recipe=recipe)
            for ingredient in ingredients:
                pdf.drawString(150, 680, f"{ingredient.ingredient.title}: {ingredient.quantity} {ingredient.ingredient.unit}")
            pdf.showPage()

        pdf.save()
        return response

    @action(detail=True, methods=['post'])
    def add_to_shopping_list(self, request, pk=None):  # добалвение рецепта в список покупок
        recipe = self.get_object()
        user = request.user
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})
        if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
            return Response({'detail': 'Рецепт уже есть в списке покупок.'})
        serializer = ShoppingList.objects.create(user=user, recipe=recipe)
        return Response(serializer.data)


    @action(detail=True, methods=['delete'])  # удаление рецепта из списка покупок
    def remove_from_shopping_list(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})
        try:
            favorite = ShoppingList.objects.get(recipe=recipe, user=user)
            favorite.delete()
            return Response()
        except ShoppingList.DoesNotExist:
            return Response({"detail": "Рецепт не найден в списке"})


class FavoritesViewSet(viewsets.ModelViewSet):  # только авторизованный пользователь 
    """ViewSet для работы с избранным."""  # может добавлять или удалять рецепты в избранном
    queryset = Favorites.objects.all()
    serializer_class = FavoritesSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=True, methods=['post'])
    def add_to_favorites(self, request, pk=None):  # Добавление нового рецепта в раздел
        recipe = self.get_object()
        user = request.user
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})
        if Favorites.objects.filter(user=user, recipe=recipe).exists():
            return Response({'detail': 'Рецепт уже есть в списке избранного.'})
        Favorites.objects.create(user=user, recipe=recipe)
        return Response()

    @action(detail=True, methods=['delete'])
    def remove_from_favorites(self, request, pk=None):  # Удаление рецепта из раздела
        recipe = self.get_object()
        user = request.user
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})
        try:
            favorite = Favorites.objects.get(recipe=recipe, user=user)
            favorite.delete()
            return Response()
        except Favorites.DoesNotExist:
            return Response({"detail": "Рецепт не найден в избранном"})
