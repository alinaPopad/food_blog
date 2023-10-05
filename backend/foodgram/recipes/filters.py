from django_filters import rest_framework as filters
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Recipe, Ingredient, Favorites

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов.(теги/избранное/список покупок)"""
    author = filters.NumberFilter(field_name="author__id")
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = {
            'author': ['exact'],
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['tags'] = filters.CharFilter(method="filter_by_tags")

    def filter_by_tags(self, queryset, name, value):
        tags = value.split(",")
        return queryset.filter(tags__slug__in=tags).distinct()

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value == '1' and user.is_authenticated:
            favorite_recipes = Favorites.objects.filter(user=user).values_list('recipe', flat=True)
            return queryset.filter(pk__in=favorite_recipes)
        return queryset

    def filter_by_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated:
            return queryset.filter(
                Q(is_in_shopping_cart=value, is_in_shopping_cart__user=user) | Q(is_in_shopping_cart=None)
            )
        else:
            return queryset.filter(is_in_shopping_cart=None)


class IngredientFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
