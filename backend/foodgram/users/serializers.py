from djoser.serializers import UserCreateSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для регистрации по токену"""
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'login', 'email', 'password', 'first_name', 'last_name')
