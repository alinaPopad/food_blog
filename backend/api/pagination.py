from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Кастомный пагинатор для рецептов/пользователей."""
    page_size = 6
