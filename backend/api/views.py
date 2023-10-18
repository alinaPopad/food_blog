import os

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .filters import RecipeFilter, IngredientFilter
from recipes.models import Recipe, Tags, Ingredient, ShoppingList
from recipes.models import Favorites, RecipeIngredient
from .permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from .pagination import DefaultPagination
from .serializers import RecipeSerializer, TagSerializer
from .serializers import IngredientSerializer, PublicRecipeSerializer
from .serializers import CreateUpdateRecipeSerializer
from users.models import CustomUser, Follow
from .serializers import FollowSerializer, CustomUserCreateSerializer
from .serializers import FollowViewSerializer


class RecipesViewSet(viewsets.ModelViewSet):
    """ViewSet для просмотра и управления рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = (
        IsAuthorOrReadOnly | IsAdminOrReadOnly,
    )
    pagination_class = DefaultPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от метода."""
        if self.action in ('create', 'partial_update'):
            return CreateUpdateRecipeSerializer
        elif self.action in ('list', 'retrieve'):
            if not self.request.user.is_authenticated:
                return PublicRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """Создание рецепта."""
        serializer = self.get_serializer(data=request.data)
        print(request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        recipe_id = serializer.instance.id
        return Response(
            {'detail': 'Recipe created successfully',
             'recipe_id': recipe_id},
            status=status.HTTP_201_CREATED
        )

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
        serializer = CreateUpdateRecipeSerializer(recipe, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Удаление рецепта."""
        recipe = get_object_or_404(Recipe, id=pk)
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def favorites(self, request, pk=None):
        """Метод для управления избранным."""
        recipe = self.get_object()
        user = request.user

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

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Метод для управления списком покупок."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            # Добавление в список покупок
            if not recipe.is_in_shopping_cart.filter(user=user).exists():
                ShoppingList.objects.create(user=user, recipe=recipe)
                return Response(
                    {'detail': 'Рецепт добавлен в список покупок.'},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'detail': 'Рецепт уже есть в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
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

    @action(detail=False, methods=['get'])
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
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = [IngredientFilter, ]
    search_fields = ['^name', ]


class CustomUserViewSet(DjoserUserViewSet):
    """ViewSet для управления пользователями."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserCreateSerializer
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated, )

    def custom_user_list(self, request):
        """Регистрация нового пользователя."""
        serializer = CustomUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                CustomUserCreateSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def profile(self, request, pk=None):
        """Просмотр профиля по id."""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user = get_object_or_404(CustomUser, pk=id)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def current_user_profile(self, request, pk=None):
        """Просмотр своего профиля."""
        user = request.user
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Смена пароля."""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({'detail': 'Введите новый и текущий пароль.'},
                            status=status.HTTP_400_BAD_REQUEST
                            )

        if not user.check_password(current_password):
            return Response({'detail': 'Неправильный пароль.'},
                            status=status.HTTP_400_BAD_REQUEST
                            )

        user.set_password(new_password)
        user.save()
        return Response()

    @action(detail=False, methods=['post'])
    def obtain_auth_token(self, request):
        """Получение токена."""
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'detail': 'Both email and password are required.'}
            )
        user = authenticate(
            request,
            username=email,
            password=password
        )
        if user:
            token, created = Token.objects.get_or_create(user=user)
            login(request, user)
            return Response({'auth_token': token.key})

    @action(detail=False, methods=['post'])
    def delete_token(self, request):
        """Удаление токена."""
        user = request.user
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})
        try:
            token = Token.objects.get(user=user)
            token.delete()
            logout(request)
            return Response()
        except Token.DoesNotExist:
            return Response({'detail': 'Токен не существует.'})

    @action(detail=True, methods=['POST', 'DELETE'], url_path='subscribe')
    def manage_subscription(self, request, id):
        if request.method == 'POST':
            return self.sub_create(request, id)
        if request.method == 'DELETE':
            return self.sub_del(request, id)

    def sub_create(self, request, id):
        data = {
            'user': request.user.id,
            'author': id
        }
        serializer = FollowViewSerializer(
            data=data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def sub_del(self, request, id):
        author = get_object_or_404(CustomUser, id=id)
        if Follow.objects.filter(
            user=request.user,
            author=author
        ).exists():
            Follow.objects.filter(
                user=request.user,
                author=author
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], url_path='subscriptions')
    def list_subscriptions(self, request):
        user = request.user
        print(user)
        queryset = CustomUser.objects.filter(following__user=user)
        print(queryset)
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
