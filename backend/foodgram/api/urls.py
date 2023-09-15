# urls для api
from django.contrib import admin
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from recipes.views import RecipesViewSet,  TagsViewSet, IngredientsViewSet, ShoppingListViewSet, FavoritesViewSet
from rest_framework.routers import DefaultRouter
# FollowViewSet,

schema_view = get_schema_view(
   openapi.Info(
      title="Recipes API",
      default_version='v1',
      description="Документация для приложения ",
      # terms_of_service="URL страницы с пользовательским соглашением",
      contact=openapi.Contact(email="admin@kittygram.ru"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   url="http://localhost:8000/static/drf-yasg/openapi-schema.yml",
)
router = DefaultRouter()
router.register(r'recipes', RecipesViewSet)  # рецепты
router.register(r'tags', TagsViewSet)  # теги
router.register(r'ingredients', IngredientsViewSet)  # ингредиенты
router.register(r'shoppinglist', ShoppingListViewSet)  # список покупок
router.register(r'favorites', FavoritesViewSet)  # избранное
# router.register(r'follows', FollowViewSet)


urlpatterns = [
    path('', include(router.urls)),
    # документация api
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0),
            name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0),
            name='schema-redoc'),
    # регистрация и получение токена
    re_path('auth/', include('djoser.urls')),
    re_path('auth/', include('djoser.urls.authtoken')),
]