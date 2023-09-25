from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.authentication import TokenAuthentication
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from django.contrib.auth.models import User
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import CustomUser, Follow
from .serializers import FollowSerializer, CustomUserCreateSerializer
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token

POST_FILTER = 6


class CustomUserViewSet(DjoserUserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserCreateSerializer
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER

    @action(detail=False, methods=['GET'])
    @permission_classes([AllowAny])
    def user_list(self, request, *args, **kwargs):  # список пользователей
        queryset = self.filter_queryset(self.get_queryset())
        total_count = queryset.count()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data_list = {
                'count': total_count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': serializer.data
            }
            return self.get_paginated_response(data_list)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'], permission_classes=(TokenAuthentication,))  # информация о текущем пользователе
    def current_user(self, request):
        user = request.user
        if user.is_authenticated:
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        else:
            return Response({'detail': 'Пользователь не авторизован.'})

    @action(detail=False, methods=['GET'])  # показывает профиль пользователя
    def profile(self, request):
        user = request.user
        if not user.is_authenticared:
            return Response({'detail': 'Пользователь не авторизован.'})

        user_profile = get_object_or_404(User, pk=user.pk)

        serializer = self.get_serializer(user_profile)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'], permission_classes=(AllowAny,))  # регистрация пользователя
    def register(self, request):
        serializer = CustomUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(CustomUserCreateSerializer(user).data)
        return Response(serializer.errors)

    @action(detail=False, methods=['post'])  # смена пароля
    def change_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({'detail': 'Введите новый и текущий пароль.'})

        if not user.check_password(current_password):
            return Response({'detail': 'Неправильный пароль.'})

        user.set_password(new_password)
        user.save()
        return Response()

    @action(detail=False, methods=['post'])  # получение токена
    def obtain_auth_token(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'detail': 'Both email and password are required.'})

        user = authenticate(request, username=email, password=password)

        if user:
            token, created  = Token.objects.get_or_create(user=user)
            login(request, user)
            return Response({'auth_token': token.key})

    @action(detail=False, methods=['post'])  # удаление токена
    def delete_token(self, request):
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


class FollowViewSet(viewsets.ModelViewSet):
    """ViewSet для подписки авторизованного пользователя."""
    queryset = CustomUser.objects.none()
    serializer_class = FollowSerializer
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER
    filter_backends = (SearchFilter,)
    # search_fields = ('following__username',)
    permission_classes = (IsAuthenticated,)

    def list(self, request):  # возвращаем список подписок
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})
        return self.request.user.follower.all()

    @action(detail=False, methods=['post'])
    def create_subscription(self, request, pk=None):  # создание подписки
        user_to_sub_to = get_object_or_404(CustomUser, pk=pk)
        user = request.user
        serializer = self.get_serializer(data={'user': user.id, 'following': user_to_sub_to.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete_subscription(self, request, pk=None):  # Отписка
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})
        user_to_unsub = get_object_or_404(CustomUser, pk=pk)
        user = request.user

        try:
            subscription = Follow.objects.get(user=user, author=user_to_unsub)
            subscription.delete()
            return Response()
        except Follow.DoesNotExist:
            return Response({'detail': 'Подписка не найденна.'})
