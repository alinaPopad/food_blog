import django_filters as filters
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Recipe, Ingredient

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов.(теги/избранное/список покупок)"""
    author = filters.NumberFilter(field_name="author__id")

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

    def filter_by_favorites(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated:
            return queryset.filter(
                Q(favorites__is_favorite=value, favorites__user=user) | Q(favorites=None)
            )
        else:
            return queryset.filter(favorites=None)

    def filter_by_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated:
            return queryset.filter(
                Q(is_in_shopping_cart=value, is_in_shopping_cart__user=user) | Q(is_in_shopping_cart=None)
            )
        else:
            return queryset.filter(is_in_shopping_cart=None)


class IngredientFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ['name']
