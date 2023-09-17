from django.db import models
from django.db.models import Q, F
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


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

    def clean(self):
        valid_subscription = Follow.objects.filter(
            user=self.user, author=self.author).first()
        if valid_subscription:
            raise ValidationError('Подписка на этого автора уже существует.')
        return

    def __Str__(self):
        return f'Пользователь {self.user} подписан на автора {self.author}'
