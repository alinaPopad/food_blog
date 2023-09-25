from django.contrib import admin
from recipes.models import Recipe, Ingredient, Tags, RecipeIngredient, Favorites, ShoppingList
from users.models import CustomUser, Follow

admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Tags)
admin.site.register(RecipeIngredient)
admin.site.register(CustomUser)
admin.site.register(Favorites)
admin.site.register(ShoppingList)