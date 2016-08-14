from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, mixins, permissions, generics, filters
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response

from posts.models import Post
from posts.serializers import PostSerializer, PostPublicSerializer
from users.models import User, UserSettings
from users.serializers import (RegisterUserSerializer, PublicUserSerializer,
                               ProfilePublicSerializer, ProfileUserSerializer,
                               NotificationSettingsSerializer, ChangePasswordSerializer, ChangePhoneSerializer,
                               CheckUsernameAndPassword, UsernameSerializer, FollwersSerializer)

from core.views import ExtandableModelMixin


def fill_follower(users: list, request):
    user = request.user

    if not user.is_authenticated():
        return

    user_ids = {it['id'] for it in users}
    followes = user.followees.filter(pk__in=user_ids).values('id')
    followes = {it['id']: it for it in followes}

    for it in users:
        it['is_followee'] = it['id'] in followes


# TODO: Use class from core.views
class UserViewSet(ExtandableModelMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    permission_classes = (permissions.AllowAny,)

    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return PublicUserSerializer
        else:
            return RegisterUserSerializer

    def extend_response_data(self, data):
        fill_follower(data, self.request)

    # def list(self, request, *args, **kwargs):
    #     response = super().list(request, *args, **kwargs)
    #     fill_follower(response.data['results'], request)
    #     return response

    def create(self, request, *args, **kwarg):
        """
        Register user by phone, username, password, avatar, country id and confirmation code received by sms.

        ---
        parameters:
            - name: phone
              description: user phone number with country code (e.g. +79131234567, +1-492-9131234567)
            - name: username
              description: unique user name. Must be less then 16 symbols.
            - name: password
              description: user password. Must be greater than 5 symbols.
            - name: country
              description: user country id.
        """
        return super().create(request, *args, **kwarg)

    @list_route(['get'])
    def check(self, request, *args, **kwargs):
        """

        ---
        serializer: users.serializers.CheckUsernameAndPassword
        """
        serializer = CheckUsernameAndPassword(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        return Response()

    @detail_route(['put'])
    def follow(self, request, pk=None):
        """
        Adds authorized user to list of followers of user with id equal to pk

        ---
        omit_serializer: true
        """
        if not self.request.user.is_authenticated():
            return self.permission_denied(request, 'You should be authorized')

        user = get_object_or_404(User, pk=pk)
        if not user.followers.filter(pk=request.user.pk).exists():
            user.followers.add(request.user)

        return Response()

    @detail_route(['put'])
    def unfollow(self, request, pk):
        """
        Removes authorized user from list of followers of user with id equal to pk

        ---
        omit_serializer: true
        """
        if not self.request.user.is_authenticated:
            return self.permission_denied(request, 'You should be authorized')

        user = get_object_or_404(User, pk=pk)
        if user.followers.filter(pk=request.user.pk).exists():
            user.followers.remove(request.user)

        return Response()

    def _get_user_recent_posts(self, data: list, user_ids: set):
        """Returns dict of last post for users in user_ids"""
        # Adds last three post to each user
        # FIXME: can be slow and huge
        posts = Post.objects.filter(user__in=user_ids, expired_at__gte=timezone.now())
        posts = posts.order_by('user_id', 'voted_count')

        user_post_list = {}
        for user in data:
            user_post_list[user['id']] = []

        for post in posts:
            user = post.user_id
            user_posts = user_post_list[user]
            if len(user_posts) > 3:
                continue

            user_posts.append(post)

        return user_post_list

    @detail_route(['get'])
    def followers(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)

        qs = user.followers.all()
        page = self.paginate_queryset(qs)

        context = self.get_serializer_context()
        serializer = FollwersSerializer(page, many=True, context=context)

        followers_ids = {it.pk for it in page}
        followees = user.followees.filter(pk__in=followers_ids)
        followees_ids = {it.pk for it in followees}

        user_post_list = self._get_user_recent_posts(serializer.data, followers_ids)

        for it in serializer.data:
            it['is_followee'] = it['id'] in followees_ids
            it['posts'] = PostPublicSerializer(user_post_list[it['id']], many=True).data

        return self.get_paginated_response(serializer.data)

    @detail_route(['get'])
    def following(self, request, pk=None):
        # user = get_object_or_404(User, pk=pk)
        user = get_object_or_404(User, pk=pk)

        qs = user.followees.all()
        page = self.paginate_queryset(qs)

        context = self.get_serializer_context()
        serializer = FollwersSerializer(page, many=True, context=context)

        user_ids = {it['id'] for it in serializer.data}
        user_post_list = self._get_user_recent_posts(serializer.data, user_ids)

        for it in serializer.data:
            it['is_followee'] = True
            it['posts'] = PostPublicSerializer(user_post_list[it['id']], many=True).data

        return self.get_paginated_response(serializer.data)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """

    ---
    PATCH:
        parameters:
            - name: website
              description: user website
            - name: gender
              description: 0 - female, 1 - male.
            - name: avatar
              required: false
              type: file
    PUT:
        parameters:
            - name: website
              description: user website
            - name: gender
              description: 0 - female, 1 - male.
    """
    queryset = User.objects.all()

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfilePublicSerializer

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return ProfilePublicSerializer
        else:
            return ProfileUserSerializer

    def get_object(self):
        self.request.user.refresh_from_db()
        return self.request.user


class UserSettingsView(generics.RetrieveUpdateAPIView):
    """

    ---
    PATCH:
        parameters:
            - name: notify_new_followers
              description: 0 - off, 1 - people I follow, 2 - everyone.
            - name: notify_comments
              description: 0 - off, 1 - people I follow, 2 - everyone.
            - name: notify_reblasts
              description: 0 - off, 1 - people I follow, 2 - everyone.
    PUT:
        parameters:
            - name: notify_new_followers
              description: 0 - off, 1 - people I follow, 2 - everyone.
            - name: notify_comments
              description: 0 - off, 1 - people I follow, 2 - everyone.
            - name: notify_reblasts
              description: 0 - off, 1 - people I follow, 2 - everyone.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationSettingsSerializer

    def get_object(self):
        instance, _ = UserSettings.objects.get_or_create(user=self.request.user)
        return instance


class UserPasswordResetView(generics.UpdateAPIView):
    """
    Changes password for authorized user

    ---
    PUT:
        - name: old_password
          description: old user password
        - name: password1
          description: new password
        - name: password2
          description: new password confirmation
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        return self.request.user


class UserChangePhoneView(generics.UpdateAPIView):
    """
    Changes user phone

    ---
    PUT:
        - name: password
          description: user password
        - name: old_phone
          description: old user phone
        - name: new_phone
          description: new user phone
    """
    permissions_class = (permissions.IsAuthenticated,)
    serializer_class = ChangePhoneSerializer

    def get_object(self):
        return self.request.user


class UsernameSearchView(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    permissions = (permissions.IsAuthenticated,)
    serializer_class = UsernameSerializer

    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)