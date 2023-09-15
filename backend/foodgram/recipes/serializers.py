from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.relations import SlugRelatedField
from .models import Recipe, Follow, Tags
from django.contrib.auth import get_user_model

User = get_user_model()


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки на авторов."""
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="username",
        default=serializers.CurrentUserDefault(),
    )
    following = SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username',
        default=serializers.CurrentUserDefault(),
    )

    def validate_following(self, value):
        if value == self.context["request"].user:
            raise serializers.ValidationError("Нельзя подписаться на себя")
        return value

    class Meta:
        fields = '__all__'
        model = Follow
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following')
            )
        ]


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    author = SlugRelatedField(slug_field='username', read_only=True)
    image = serializers.ImageField(required=True, write_only=True)

    class Meta:
        fields = '__all__'
        model = Recipe


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ('id', 'title', 'color_code', 'slug')
