from django.db import models
from users.models import CustomUser
#from django.contrib.auth import get_user_model

#User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиентов."""
    title = models.CharField(
        max_length=50,
        verbose_name='Название ингредиента',
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
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',)
    name_recipe = models.TextField(verbose_name='Название рецепта',)
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
        blank=True,
        null=True,  # пока не обязательное на тесте
    )
    text_recipe = models.TextField(verbose_name='Текст рецепта',)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tag = models.ManyToManyField(Tags)
    cooking_time = models.IntegerField(
        null=True,
        default=0,
        verbose_name='Время приготовления',
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_related_name = 'recipes'
        ordering = ['-pub_date']


class RecipeIngredient(models.Model):
    """Модель для связи many to many."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="ingredients"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        verbose_name='Количество ингредиента'
    )


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
        related_name='shopping_list_recipe',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(  # проверяю на уникальность пару пользователь-рецепт
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
            models.UniqueConstraint(  # проверяю на уникальность пару пользователь-рецепт
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'
