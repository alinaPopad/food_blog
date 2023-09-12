from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиентов."""
    title = models.CharField(
        max_length=50,
        verbose_name='Название ингредиента',
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        verbose_name='Количество ингредиента'
    )
    unit = models.CharField(
        max_length=50,
        verbose_name='Единицы измерения',
    )


class Tags(models.Model):
    """ Модель тегов."""
    title = models.CharField(
        max_length=50,
        verbose_name='Название тега',
    )
    slug = models.SlugField(
        max_length=30,
        unique=True,
        db_index=True,
        verbose_name='slug',
    )
    color_code = models.TextField(verbose_name='Цветовой код',)

    def __str__(self) -> str:
        return self.title


class Recipe(models.Model):
    """ Модель рецепта."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',)
    name_recipe = models.TextField(verbose_name='Название рецепта',)
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
        blank=True,
        verbose_name='Изображение',
    )
    text_recipe = models.TextField(verbose_name='Текст рецепта',)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tag = tags = models.ManyToManyField(Tags)
    cooking_time = models.IntegerField(
        null=True,
        default=0,
        verbose_name='Время приготовления',
    )

    class Meta:
        default_related_name = 'recipes'
