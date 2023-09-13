from django.db import models
from django.db.models import Q, F
from django.contrib.auth import get_user_model

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


class Follow(models.Model):
    """Модель подписок"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик',
        help_text='тот, кто подписался'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='автор',
        help_text='тот, на кого подписались',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.CheckConstraint(
                check=~Q(user=F('author')),
                name='prevent_self_folowwing'
            ),
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_pair'
            ),
        ]

    def __Str__(self):
        return f'Пользователь {self.user} подписан на автора {self.author}'