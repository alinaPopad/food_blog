import django_filters as filters
from django.contrib.auth import get_user_model

from .models import Recipe

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов.(теги/избранное/список покупок)"""
    author = filters.NumberFilter(field_name="author__id")
    tags = filters.CharFilter(field_name="tags__slug", method="filter_by_tags")

    class Meta:
        model = Recipe
        fields = {
            'author': ['exact'],
            'tag': ['exact', 'in'],
        }

    def filter_by_tags(self, queryset, name, value):
        tags = value.split(",")
        return queryset.filter(tags__slug__in=tags).distinct()

    def filter_by_favorites(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset.none()
        return queryset.filter(
            favorites__is_favorite=value,
            favorites__user=self.request.user
        )

    def filter_by_shopping_cart(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset.none()
        return queryset.filter(
            shopping_list__in_list=value,
            shopping_list__user=self.request.user
        )
