from django_filters import rest_framework as filters
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Recipe, Ingredient, Favorites, Tags

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов.(теги/избранное/список покупок)"""
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited')

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


""""
def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['tags'] = filters.CharFilter(method="filter_by_tags")

    def filter_by_tags(self, queryset, name, value):
        tags = value.split(",")
        print("Received tags:", tags) 
        return queryset.filter(tags__slug__in=tags).distinct()
"""
