from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
import logging
from .models import Follow, CustomUser


logger = logging.getLogger(__name__)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для CustomUser."""
    class Meta(UserCreateSerializer.Meta):
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        try:
            username = validated_data['username']
            email = validated_data['email']
            first_name = validated_data['first_name']
            last_name = validated_data['last_name']
            password = validated_data['password']
            user = CustomUser.objects.create_user(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            return user
        except Exception as e:
            logger.error(e)
            raise

    def to_representation(self, instance):
        representation = {
            "email": instance.email,
            "id": instance.id,
            "username": instance.username,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
        }
        return representation


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки на авторов."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField(
        read_only=True,
        method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()

    def get_recipes(self, obj):
        from recipes.serializers import MiniRecipeSerializer
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return MiniRecipeSerializer(recipes, many=True).data

    @staticmethod
    def get_recipes_count(obj):
        """Метод для получения количества рецептов"""

        return obj.recipes.count()
