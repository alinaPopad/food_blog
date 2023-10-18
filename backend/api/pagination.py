from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Кастомный пагинатор для рецептов/пользователей."""
    page_size = 6
    page_size_query_param = 'limit'
