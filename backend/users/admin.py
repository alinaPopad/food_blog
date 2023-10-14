from django.contrib import admin

from recipes.models import Recipe, Ingredient, Tags, RecipeIngredient
from recipes.models import Favorites, ShoppingList
from users.models import CustomUser, Follow


class AdminUser(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email')


class AdminIngredient(admin.ModelAdmin):
    """Поиск по названию."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class AdminRecipe(admin.ModelAdmin):
    """Фильтрация по полям."""
    list_display = (
        'id', 'name', 'author', 'get_favorites', 'get_tags'
    )
    list_filter = ('author', 'name', 'tags')
    search_fields = ('name',)

    def get_favorites(self, obj):
        return obj.favorites_recipe.count()

    get_favorites.short_description = (
        'В избранном'
    )

    def get_tags(self, obj):
        return '\n'.join(obj.tags.values_list('name', flat=True))

    get_tags.short_description = 'Теги'


class AdminFollow(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    search_fields = ('user', 'author')
    list_filter = ('user', 'author')


admin.site.register(Recipe, AdminRecipe)
admin.site.register(Ingredient, AdminIngredient)
admin.site.register(CustomUser, AdminUser)
admin.site.register(Favorites)
admin.site.register(ShoppingList)
admin.site.register(Follow, AdminFollow)
admin.site.register(Tags)
admin.site.register(RecipeIngredient)
