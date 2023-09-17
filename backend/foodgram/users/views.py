from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from rest_framework.decorators import action

from .models import User, Follow
from .serializers import FollowSerializer, CustomUserCreateSerializer, UserRegistrationSerializer
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token

POST_FILTER = 6


class CustomUserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserCreateSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER

    def users_list(self, request, *args, **kwargs):  # список пользователей
        queryset = self.filter_queryset(self.get_queryset())
        total_count = queryset.count()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data_list = {
                'count': total_count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'result': serializer.data
            }
            return self.get_paginated_response(data_list)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])  # информация о текущем пользователе
    def current_user(self, request):
        user = request.user
        if user.is_authenticated:
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        else:
            return Response({'detail': 'Пользователь не авторизован.'})

    @action(detail=False, methods=['get'], permission_classes=(AllowAny,))  # показывает профиль пользователя
    def profile(self, request):
        user = request.user
        if not user.is_authenticared:
            return Response({'detail': 'Пользователь не авторизован.'})

        user_profile = get_object_or_404(User, pk=user.pk)

        serializer = self.get_serializer(user_profile)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])  # регистрация пользователя
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(CustomUserCreateSerializer(user).data)

        return Response(serializer.errors)

    @action(detail=False, methods=['post'], permission_classes=(IsAuthenticated,))  # смена пароля
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

    @action(detail=False, methods=['post'], permission_classes=(AllowAny,))  # получение токена
    def obtain_auth_token(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'detail': 'Both email and password are required.'})

        user = authenticate(request, username=email, password=password)

        if user:
            token, _ = Token.objects.get_or_create(user=user)
            login(request, user)
            return Response({'auth_token': token.key})

    @action(detail=False, methods=['post'], permission_classes=(IsAuthenticated,))  # удаление токена
    def delete_token(self, request):
        user = request.user
        try:
            token = Token.objects.get(user=user)
            token.delete()
            logout(request)
            return Response()
        except Token.DoesNotExist:
            return Response({'detail': 'Токен не существует.'})


class FollowViewSet(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.ListModelMixin,
                    mixins.DestroyModelMixin,  # делаем отписку
                    viewsets.GenericViewSet):
    """ViewSet для подписки авторизованного пользователя."""
    serializer_class = FollowSerializer
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER
    filter_backends = (SearchFilter,)
    # search_fields = ('following__username',)
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):  # создание подписки
        serializer.save(user=self.request.user)

    def get_queryset(self):  # возвращаем список подписок
        return self.request.user.follower.all()
