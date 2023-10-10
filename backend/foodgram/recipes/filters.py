from django_filters import rest_framework as filters
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Recipe, Ingredient, Tags

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов.(теги/избранное/список покупок)"""
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_by_shopping_cart')
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tags.objects.all(),
        field_name='tags__slug',
        to_field_name='slug')

    class Meta:
        model = Recipe
        fields = ('tags', 'author',)

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(favorites_recipe__user=user)
        return queryset

    def filter_by_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(is_in_shopping_cart__user=user) 
        return queryset


class IngredientFilter(filters.FilterSet):
    """Фильтрация для выбора ингредиента."""
    title = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
