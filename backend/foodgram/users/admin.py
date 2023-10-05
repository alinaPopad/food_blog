from django.contrib import admin
from recipes.models import Recipe, Ingredient, Tags, RecipeIngredient
from recipes.models import Favorites, ShoppingList, RecipeTag
from users.models import CustomUser, Follow

admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Tags)
admin.site.register(RecipeIngredient)
admin.site.register(CustomUser)
admin.site.register(Favorites)
admin.site.register(ShoppingList)
admin.site.register(Follow)
admin.site.register(RecipeTag)
"""
class AdminTag(admin.TabularInline):
    model = Tags
    min_num = 1

class AdminIngredient(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1

class AdminRecipe(admin.ModelAdmin):
    list_filter = ('name', 'author', 'tags')
    list_display = ('name', 'amount_favorite')
    inlines = [AdminIngredient, AdminTag]
"""