from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.core.validators import MinLengthValidator
from django.core.validators import MinValueValidator

from users.models import CustomUser


class Tags(models.Model):
    """ Модель тегов."""
    name = models.CharField(
        max_length=50,
        verbose_name='Название тега',
    )
    slug = models.SlugField(
        max_length=30,
        unique=True,
        db_index=True,
        verbose_name='slug',
    )
    color = models.TextField(verbose_name='Цветовой код',)

    class Meta:
        ordering = ['name']
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField(
        max_length=100,
        verbose_name='Название ингредиента',
        validators=[MinLengthValidator(3)],
        db_index=True,
    )
    measurement_unit = models.CharField(
        max_length=100,
        verbose_name='Единицы измерения',
    )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """ Модель рецепта."""
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',)
    name = models.TextField(verbose_name='Название рецепта',)
    image = models.ImageField(
        'Картинка',
        blank=True,
        null=True,
    )
    text = models.TextField(verbose_name='Текст рецепта',)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tags,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        null=False,
        validators=[
            MinValueValidator(
                1, "Время приготовления должно быть не меньше 1."
            )],
        verbose_name='Время приготовления',
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_related_name = 'recipes'
        ordering = ['-pub_date']

    def get_ingredients(self):
        return self.ingredients.through.objects.filter(recipe=self)


class RecipeIngredient(models.Model):
    """Модель для связи many to many."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredient_used"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="ingredients"
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(1, message='Минимальное количество 1!')]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте.'
        verbose_name_plural = 'Ингредиенты в рецептах.'
        constraints = [
            UniqueConstraint(fields=['recipe', 'ingredient'],
                             name='recipe_ingredient_constraint')
        ]


class ShoppingList(models.Model):
    """Модель для списка покупок."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_list_user',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_in_shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_list'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class Favorites(models.Model):
    """Модель избранного."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorites_user',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites_recipe',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class RecipeTag(models.Model):
    """Модель для связи many to many для тегов."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="tag_used"
    )
    tag = models.ForeignKey(
        Tags,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="tags"
    )

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'
        constraints = [
            models.UniqueConstraint(fields=['tag', 'recipe'],
                                    name='unique_tagrecipe')
        ]

    def __str__(self):
        return f'{self.tag} {self.recipe}'
