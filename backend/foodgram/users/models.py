from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q, F
from django.core.exceptions import ValidationError


class CustomUser(AbstractUser):
    """Модель пользователя."""
    username = models.CharField(blank=True, max_length=150, )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_subscribed = models.BooleanField(default=False)
    (AbstractUser._meta.get_field('groups').
     remote_field.related_name) = 'custom_user_set'
    (AbstractUser._meta.get_field('user_permissions')
     .remote_field.related_name) = 'custom_user_set'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписок"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик',
        help_text='тот, кто подписался'
    )
    author = models.ForeignKey(
        CustomUser,
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

    def clean(self):
        valid_subscription = Follow.objects.filter(
            user=self.user, author=self.author).first()
        if valid_subscription:
            raise ValidationError('Подписка на этого автора уже существует.')
        return

    def __Str__(self):
        return f'Пользователь {self.user} подписан на автора {self.author}'
