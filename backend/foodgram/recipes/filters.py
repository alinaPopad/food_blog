import django_filters as filters

from .models import Recipe


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(
        field_name="favorites__user",
        method="filter_by_favorites"
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name="shopping_cart__user",
        method="filter_by_shopping_list"
    )
    author = filters.NumberFilter(field_name="author__id")
    tags = filters.CharFilter(field_name="tags__slug", method="filter_by_tags")

    class Meta:
        model = Recipe
        fields = {
            'author': ['exact'],
            'tags__slug': ['exact', 'in'],
            'is_favorited': ['exact'],
            'is_in_shopping_cart': ['exact'],
        }

    def filter_by_favorites(self, queryset, name, value):
        return queryset.filter(
            favorites__is_favorite=value,
            favorites__user=self.request.user
        )

    def filter_by_shopping_cart(self, queryset, name, value):
        return queryset.filter(
            shopping_cart__in_cart=value,
            shopping_cart__user=self.request.user
        )

    def filter_by_tags(self, queryset, name, value):
        tags = value.split(",")
        return queryset.filter(tags__slug__in=tags).distinct()


