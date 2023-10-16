from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, re_path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet
from .views import RecipesViewSet, TagsViewSet, IngredientsViewSet

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')  # пользователи
router.register(r'recipes', RecipesViewSet)  # рецепты
router.register(r'tags', TagsViewSet)  # теги
router.register(r'ingredients', IngredientsViewSet)  # ингредиенты

urlpatterns = [
    re_path('', include(router.urls)),
    re_path('auth/', include('djoser.urls')),
    re_path('auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT)
