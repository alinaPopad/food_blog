from rest_framework.filters import SearchFilter
from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from recipes.models import Recipe, Tags


User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов.(теги/избранное/список покупок)"""
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited')
    is_in_shopping_cart = filters.ChoiceFilter(
        method='filter_by_shopping_cart',
        field_name='is_in_shopping_cart',
        lookup_expr='exact',
        choices=[(0, '0'), (1, '1')]
    )
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

    def filter_queryset(self, queryset):
        if self.request.query_params.get('is_in_shopping_cart'):
            self.request._request.GET = self.request._request.GET.copy()
            self.request._request.GET['page'] = '1'
            return queryset
        return super().filter_queryset(queryset)


class IngredientFilter(SearchFilter):
    """Фильтр для поиска ингредиента."""
    search_param = 'name'  #
