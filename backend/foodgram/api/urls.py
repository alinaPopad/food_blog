# urls для api
from django.urls import include, re_path
from django.conf import settings
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static

from recipes.views import RecipesViewSet,  TagsViewSet, IngredientsViewSet
from users.views import CustomUserViewSet

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
