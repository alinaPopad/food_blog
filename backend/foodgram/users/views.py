from djoser.views import UserViewSet as DjoserUserViewSet


class CustomUserViewSet(DjoserUserViewSet):
    pass


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
