from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.relations import SlugRelatedField
from .models import Follow, CustomUser
import logging

logger = logging.getLogger(__name__)

# User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):

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

"""
class FollowSerializer(serializers.ModelSerializer):
    Сериализатор для подписки на авторов.
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        default=serializers.CurrentUserDefault(),
    )
    following_id = serializers.PrimaryKeyRelatedField(
        source='following',
        queryset=CustomUser.objects.all(),
    )
    author = serializers.ReadOnlyField(source='following')

    def validate_following(self, value):
        if value == self.context["request"].user:
            raise serializers.ValidationError("Нельзя подписаться на себя")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        following_user = validated_data["following"]
        return Follow.objects.create(user=user, author=following_user)
    
    class Meta:
        fields = '__all__'
        model = Follow
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following')
            )
        ]
"""


"""Сериализатор для регистрации по токену"""
"""
class UserRegistrationSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
"""
