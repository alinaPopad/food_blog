from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.authentication import TokenAuthentication
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from django.contrib.auth.models import User
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import CustomUser, Follow
from .serializers import FollowSerializer, CustomUserCreateSerializer
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from rest_framework import status
from .permissions import AllowAnyGet
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage




POST_FILTER = 6


class CustomUserViewSet(DjoserUserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserCreateSerializer
    pagination_class = LimitOffsetPagination
    page_size = POST_FILTER

    @api_view(['GET', 'POST'])
    @permission_classes([AllowAny])
    def custom_user_list(request):
        if request.method == 'GET':
            queryset = CustomUser.objects.all()
            total_count = queryset.count()

        # Проверяем, нужно ли пагинировать результат
            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size', POST_FILTER)

            if page is not None:
                paginator = Paginator(queryset, page_size)
                try:
                    users = paginator.page(page)
                except EmptyPage:
                    return Response({'detail': 'Страница не найдена.'}, status=status.HTTP_404_NOT_FOUND)

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
                return Response(CustomUserCreateSerializer(user).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['GET'], url_path='profile/(?P<pk>[^/.]+)')
    @permission_classes([AllowAny])
    def profile(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], url_path='me')
    def current_user_profile(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})
        
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)


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

    @action(detail=True, methods=['POST', 'DELETE'], url_path='subscribe', permission_classes=[IsAuthenticated])
    def manage_subscription(self, request, id=None):
        user_to_modify_subscription = get_object_or_404(CustomUser, pk=id)
        user = request.user

        if request.method == 'POST':
            # Создать подписку
            try:
                subscription = Follow.objects.get(user=user, author=user_to_modify_subscription)
                return Response({'detail': 'Подписка на этого автора уже существует.'}, status=status.HTTP_400_BAD_REQUEST)
            except Follow.DoesNotExist:
                subscription = Follow(user=user, author=user_to_modify_subscription)
                subscription.save()
                serializer = FollowSerializer(subscription)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            # Удалить подписку
            try:
                subscription = Follow.objects.get(user=user, author=user_to_modify_subscription)
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Follow.DoesNotExist:
                return Response({'detail': 'Подписка не найдена.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['GET'], url_path='subscriptions')
    def list_subscriptions(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Пользователь не авторизован.'})
    
        subscriptions = Follow.objects.filter(user=request.user)
        serializer = FollowSerializer(subscriptions, many=True)
        return Response(serializer.data)

"""
    @action(detail=True, methods=['post', 'delete'])
    def manage_subscription(self, request, pk=None):
        user_to_manage = get_object_or_404(CustomUser, pk=pk)
        user = request.user

        if request.method == 'POST':
            # Создать подписку
            if user != user_to_manage:
                # Пользователь не может подписаться на самого себя
                serializer = FollowSerializer(data={'user': user.id, 'following': user_to_manage.id})
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'detail': 'Вы не можете подписаться на сами себя.'}, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            # Удалить подписку
            if user != user_to_manage:
                try:
                    subscription = Follow.objects.get(user=user, author=user_to_manage)
                    subscription.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                except Follow.DoesNotExist:
                    return Response({'detail': 'Подписка не найдена.'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'detail': 'Вы не можете отписаться от сами себя.'}, status=status.HTTP_400_BAD_REQUEST)

class FollowViewSet(viewsets.ModelViewSet):

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




            @action(detail=False, methods=['GET'], url_path='custom_user_list')
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

@action(detail=False, methods=['POST'], permission_classes=(AllowAny,))  # регистрация пользователя
    def register(self, request):
        serializer = CustomUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(CustomUserCreateSerializer(user).data)
        return Response(serializer.errors)

"""