from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token

from .models import CustomUser, Follow
from .serializers import FollowSerializer, CustomUserCreateSerializer
from .permissions import AllowAnyGet

from djoser.views import UserViewSet as DjoserUserViewSet

POST_FILTER = 6


class CustomUserViewSet(DjoserUserViewSet):
    """ViewSet для управления пользователями."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserCreateSerializer
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER
    permission_classes = IsAuthenticatedOrReadOnly

    def get_queryset(self):
        """Доступ неавторизованным пользователея к методу get."""
        queryset = super().get_queryset()
        if self.action == "list" and settings.DJOSER['HIDE_USERS']:
            queryset = queryset.all()
        return queryset

    def get_permissions(self):
        if self.action == "list" or self.action == "retrieve":
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    def custom_user_list(self, request):
        """Получение списка пользователей и регистрация."""
        if request.method == 'GET':
            queryset = CustomUser.objects.all()
            total_count = queryset.count()
            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size', POST_FILTER)

            if page is not None:
                paginator = Paginator(queryset, page_size)
                try:
                    users = paginator.page(page)
                except EmptyPage:
                    return Response(
                        {'detail': 'Страница не найдена.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                serializer = CustomUserCreateSerializer(users, many=True)
                data_list = {
                    'count': total_count,
                    'next': users.has_next(),
                    'previous': users.has_previous(),
                    'results': serializer.data
                }
                return Response(data_list)

            serializer = CustomUserCreateSerializer(queryset, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
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
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def current_user_profile(self, request):
        """Просмотр своего профиля."""
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})

        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Смена пароля."""
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
            return Response({'detail': 'Пользователь не авторизован.'})

        subscriptions = Follow.objects.filter(user=request.user)
        serializer = FollowSerializer(subscriptions, many=True)
        return Response(serializer.data)


"""
    def get_permissions(self):
        if self.action == "list" or self.action == "profile":
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        elif self.action == "current_user_profile":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()"""