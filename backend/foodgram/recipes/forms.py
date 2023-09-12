from django import forms

from .models import Recipe


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['name_recipe', 'text_recipe', 'image', 'tag', 'cooking_time']
        labels = {
            'name_recipe': 'Назание рецепта',
            'text_recipe': 'Текст рецепта',
            'image': 'Картинка',
            'tag': 'Теги',
            'cooking_time': 'Время приготовления',
        }
        help_texts = {
            'name_recipe': 'Введите название рецепта',
            'text_recipe': 'Введите текст рецепта',
            'image': 'Загрузите изображение',
            'tag': 'Выберите теги',
            'cooking_time': 'Введите время приготовления в минутах',
        }
