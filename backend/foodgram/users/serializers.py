from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import Follow, CustomUser
import logging

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
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        fields = '__all__'
        model = Follow
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author')
            )
        ]
