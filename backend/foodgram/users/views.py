from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token

from .models import CustomUser, Follow
from .serializers import FollowSerializer, CustomUserCreateSerializer

from djoser.views import UserViewSet as DjoserUserViewSet

POST_FILTER = 6


class CustomUserViewSet(DjoserUserViewSet):
    """ViewSet для управления пользователями."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserCreateSerializer
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER
    permission_classes = (IsAuthenticated, )

    def custom_user_list(self, request):
        """Регистрация нового пользователя."""
        serializer = CustomUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                CustomUserCreateSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
            )

    def profile(self, request, pk=None):
        """Просмотр профиля по id."""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user = get_object_or_404(CustomUser, pk=id)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def current_user_profile(self, request, pk=None):
        """Просмотр своего профиля."""
        user = request.user
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Смена пароля."""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({'detail': 'Введите новый и текущий пароль.'},
                            status=status.HTTP_400_BAD_REQUEST
                            )

        if not user.check_password(current_password):
            return Response({'detail': 'Неправильный пароль.'},
                            status=status.HTTP_400_BAD_REQUEST
                            )

        user.set_password(new_password)
        user.save()
        return Response()

    @action(detail=False, methods=['post'])
    def obtain_auth_token(self, request):
        """Получение токена."""
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'detail': 'Both email and password are required.'}
            )
        user = authenticate(
            request,
            username=email,
            password=password
            )
        if user:
            token, created  = Token.objects.get_or_create(user=user)
            login(request, user)
            return Response({'auth_token': token.key})

    @action(detail=False, methods=['post'])
    def delete_token(self, request):
        """Удаление токена."""
        user = request.user
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})
        try:
            token = Token.objects.get(user=user)
            token.delete()
            logout(request)
            return Response()
        except Token.DoesNotExist:
            return Response({'detail': 'Токен не существует.'})

    @action(detail=True, methods=['POST', 'DELETE'], url_path='subscribe')
    def manage_subscription(self, request, id=None):
        """Управление подпиской."""
        user_to_modify_subscription = get_object_or_404(CustomUser, pk=id)
        user = request.user

        if request.method == 'POST':
            # Создать подписку
            try:
                subscription = Follow.objects.get(
                    user=user,
                    author=user_to_modify_subscription
                )
                return Response(
                    {'detail': 'Подписка на этого автора уже существует.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Follow.DoesNotExist:
                subscription = Follow(
                    user=user, author=user_to_modify_subscription)
                subscription.save()
                serializer = FollowSerializer(subscription)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
        elif request.method == 'DELETE':
            # Удалить подписку
            try:
                subscription = Follow.objects.get(
                    user=user,
                    author=user_to_modify_subscription
                )
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Follow.DoesNotExist:
                return Response(
                    {'detail': 'Подписка не найдена.'},
                    status=status.HTTP_404_NOT_FOUND
                )

    @action(detail=False, methods=['GET'], url_path='subscriptions')
    def list_subscriptions(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'},
                            status=status.HTTP_401_UNAUTHORIZED
                            )

        subscriptions = Follow.objects.filter(user=request.user)
        serializer = FollowSerializer(subscriptions, many=True)
        return Response(serializer.data)
