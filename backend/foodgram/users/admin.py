from django.contrib import admin
from recipes.models import Recipe, Ingredient, Tags


admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Tags)
