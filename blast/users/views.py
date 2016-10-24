import logging

from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from push_notifications.api.rest_framework import APNSDeviceSerializer, APNSDeviceViewSet
from rest_framework import viewsets, mixins, permissions, generics, filters, status, views
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from core.views import ExtendableModelMixin
from core.utils import get_or_none
from notifications.models import FollowRequest, Notification
from posts.models import Post
from posts.serializers import PostPublicSerializer, PreviewPostSerializer
from posts.utils import mark_voted
from reports.serializers import ReportSerializer
from users.models import User, UserSettings, Follower, BlockedUsers
from users.serializers import (RegisterUserSerializer, PublicUserSerializer,
                               ProfilePublicSerializer, ProfileUserSerializer,
                               NotificationSettingsSerializer, ChangePasswordSerializer, ChangePhoneSerializer,
                               CheckUsernameAndPassword, UsernameSerializer, FollowersSerializer)

from push_notifications.models import APNSDevice
from notifications.tasks import send_push_notification_to_device
from users.utils import bound_posts_to_users, filter_followee_users, mark_followee, mark_requested

logger = logging.getLogger(__name__)


def extend_users_response(users: list, request):
    user = request.user

    if not user.is_authenticated():
        return

    user_ids = {it['id'] for it in users}
    followees = filter_followee_users(user, user_ids)
    follow_requests = FollowRequest.objects.filter(follower=user,
                                                   followee__in=user_ids)
    # TODO: use redis
    follow_requests = {it.followee_id for it in follow_requests}

    # TODO: Use redis
    blocked_users = BlockedUsers.objects.filter(user=user, blocked__in=user_ids)
    blocked_users = {it.blocked_id for it in blocked_users}

    for it in users:
        pk = it['id']
        it['is_followee'] = pk in followees
        it['is_requested'] = pk in follow_requests  # TODO: Make test
        it['is_blocked'] = pk in blocked_users


# TODO: Use mixin from core.views
class UserViewSet(ExtendableModelMixin,
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
        extend_users_response(data, self.request)

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

    @detail_route(['put'], permission_classes=[permissions.IsAuthenticated])
    def report(self, request, pk=None):
        """

        ---
        serializer: reports.serializers.ReportSerializer
        parameters:
            - name: pk
              description: post id
              type: query
            - name: reason
              description: OTHER = 0, SENSITIVE_CONTENT = 1, SPAM = 2, DUPLICATED_CONTENT = 3,
                           BULLYING = 4, INTEL_VIOLATION = 5
            - name: text
              description: length < 128
        """
        user = get_object_or_404(User, pk=pk)
        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, object_pk=user.pk,
                        content_type=ContentType.objects.get(model='user'))
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
        if not Follower.objects.filter(followee=user, follower=request.user).exists():
            if user.is_private:
                logging.info('Send follow request to {} from {}'.format(user, request.user))
                _, created = FollowRequest.objects.get_or_create(follower=request.user,
                                                                 followee=user)
            else:
                logging.info('{} stated to follow by {}'.format(request.user, user))
                # start_following.send(sender=user, follower=request.user, followee=user)
                Follower.objects.create(followee=user, follower=request.user)

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

        if Follower.objects.filter(follower=self.request.user, followee=user).exists():
            Follower.objects.filter(follower=self.request.user, followee=user).delete()
            Notification.objects.filter(user=user, other=self.request.user).delete()
        else:
            # TODO: make test
            FollowRequest.objects.filter(follower=self.request.user, followee=user).delete()

        return Response()

    def _get_user_recent_posts(self, data: list, user_ids: set):
        """Returns dict with three last post for users in user_ids"""
        # Adds last three post to each user
        # TODO: Use Redis sorted set, like User.get_posts(user['id'], 0, 5)
        result = {}
        for user in data:
            pk = user['id']
            result[pk] = Post.objects.filter(user_id=pk).order_by('-created_at')[:3]

        return result

    def _extend_follow_response(self, page):
        context = self.get_serializer_context()
        serializer = FollowersSerializer(page, many=True, context=context)

        user_ids = {it.pk for it in page}
        user_post_list = self._get_user_recent_posts(serializer.data, user_ids)

        data = serializer.data

        mark_followee(data, self.request.user)
        mark_requested(data, self.request.user)

        for it in data:
            pk = it['id']
            # TODO: Make test
            if it['is_private'] and not it['is_followee']:
                it['posts'] = []
            else:
                posts = PreviewPostSerializer(user_post_list[pk], many=True, context=context).data
                posts = mark_voted(posts, self.request.user)
                it['posts'] = posts

        return self.get_paginated_response(serializer.data)

    @detail_route(['get'])
    def followers(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)

        qs = Follower.objects.filter(followee=user).prefetch_related('follower')
        qs = qs.order_by('follower__username')

        page = self.paginate_queryset(qs)
        page = [it.follower for it in page]

        return self._extend_follow_response(page)

    @detail_route(['get'])
    def following(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)

        qs = Follower.objects.filter(follower=user).prefetch_related('followee')
        qs = qs.order_by('followee__username')
        page = self.paginate_queryset(qs)
        page = [it.followee for it in page]

        return self._extend_follow_response(page)

    @detail_route(['put'])
    def block(self, request, pk=None):
        """
        Adds user to blacklist

        ---
        omit_serializer: true
        """
        blocked = get_object_or_404(User, pk=pk)

        try:
            BlockedUsers.objects.create(user=request.user, blocked=blocked)
        except IntegrityError as e:
            logging.error("User {} already blocked by {}".format(blocked, request.user))
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response()

    @detail_route(['put'])
    def unblock(self, request, pk=None):
        """
        Removes user from blacklist.
        ---
        omit_serializer: true
        """
        blocked = get_object_or_404(User, pk=pk)

        BlockedUsers.objects.filter(user=request.user, blocked=blocked).delete()

        return Response()


class UserProfileView(ExtendableModelMixin,
                      generics.RetrieveUpdateAPIView):
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

    def extend_response_data(self, data):
        extend_users_response(data, self.request)

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


class UserSearchView(ExtendableModelMixin,
                     viewsets.ReadOnlyModelViewSet):
    # TODO: take into account a followers
    queryset = User.objects.filter().order_by('-search_range', 'username')
    serializer_class = PublicUserSerializer

    filter_backends = (filters.SearchFilter,)
    search_fields = ('username', 'fullname',)

    def extend_response_data(self, data):
        users_to_posts = {}
        posts = []
        for user in data:
            user_posts_ids = User.get_posts(user['id'], 0, 5)
            users_to_posts[user['id']] = user_posts_ids
            posts.extend(user_posts_ids)

        # Pulls posts from memory and builds in-memory index
        posts = Post.objects.actual().filter(pk__in=posts)
        posts = {it.pk: it for it in posts}

        context = self.get_serializer_context()
        for user in data:
            user_posts_ids = users_to_posts[user['id']]

            user_posts = []
            for post_id in user_posts_ids:
                if post_id in posts:
                    user_posts.append(posts[post_id])
                if len(user_posts) >= 3:  # FIXME: Magic number.
                    break

            user['posts'] = PostPublicSerializer(user_posts, many=True, context=context).data
        # user_ids = {it['id'] for it in data}
        # user_to_posts = bound_posts_to_users(user_ids, 3)
        #
        # context = self.get_serializer_context()
        # for it in data:
        #     pk = it['id']
        #     posts = user_to_posts[pk]
        #     it['posts'] = PostPublicSerializer(posts, many=True, context=context).data

        return data

    # on each tab it's populated by popularity/randomness so on the users tab for every
    # 10 displayed 7 are most popular and 3 are random.
    @list_route(['get'])
    def feeds(self, request):
        page = request.query_params.get('page', 0)
        page_size = request.query_params.get('page_size', 50)

        try:
            page = int(page)
            page_size = min(int(page_size), 250)
        except ValueError:
            logging.error('Failed to cast page {} and page_size {} to int'.format(page, page_size))
            return Response(status=status.HTTP_400_BAD_REQUEST)

        random_count = page_size // 10 * 3

        # Calculates limits for getting most popular users
        page_size -= random_count
        start = page * page_size
        end = (page + 1) * page_size - 1
        page_size += random_count

        users = User.get_most_popular_ids(start, end)

        # TODO: Total count is wrong if random_users too small or empty.
        # Getting random users
        logger.debug('Fetch random users. {} {}'.format(page, page_size))
        random_users = User.get_random_user_ids(page_size*2)  # Increase random_count to avoid duplications with users
        random_users = random_users.difference(set(users))  # Excludes already selected users
        random_users = list(random_users)[random_count:]  # Slice unneeded elements
        logger.debug('Got {} random users. {} {}'.format(len(random_users), page, page_size))
        # random_users = User.objects.filter(pk__in=random_users).exclude(users)[random_count:]

        rand_pos = 0
        random_count = min(random_count, len(random_users))
        for i in range(0, page_size + 1, 10):
            pos = i + 7
            for j in range(rand_pos * 3, (rand_pos + 1) * 3):
                if j < random_count:
                    users.insert(pos, random_users[j])
                else:
                    break

            rand_pos += 1
            if rand_pos * 3 >= random_count:
                break

        # Pulls users and sort according to cached popularity
        sort_keys = {it: i for i, it in enumerate(users)}
        users = User.objects.filter(pk__in=users)
        users = sorted(users, key=lambda it: sort_keys[it.pk])

        serializer = PublicUserSerializer(users, many=True,
                                          context=self.get_serializer_context())
        self.extend_response_data(serializer.data)
        return Response({
            'count': User.get_users_count(),
            'results': serializer.data,
        })


class UsernameSearchView(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    permissions = (permissions.IsAuthenticated,)
    serializer_class = UsernameSerializer

    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)


def _clear_auth_data(user: User, registration_id: str or None, send_push: bool):
    Token.objects.filter(user=user).delete()

    devices = APNSDevice.objects.filter(user=user)

    if send_push:
        # Send message to user device
        reg_ids = list(it.registration_id for it in devices)
        if registration_id in reg_ids:
            reg_ids.remove(registration_id)
        msg = 'You have been signed out as you have logged in on another device'
        send_push_notification_to_device.delay(reg_ids, msg)

    devices.delete()


def _update_device_token(user: User, registration_id: str):

    serializer = APNSDeviceSerializer(data={'registration_id': registration_id})
    token_device = get_or_none(APNSDevice, registration_id=registration_id)
    user_device = get_or_none(APNSDevice, user=user)

    if token_device and user_device and token_device.pk == user_device.pk:  # Same user with same device
        return None

    if not user_device and token_device:  # Other user register same device
        _clear_auth_data(token_device.user, registration_id, True)

    if user_device and not token_device:  # Current user has some other device
        user_device.delete()

    serializer.is_valid(raise_exception=True)
    serializer.save(user=user)

    return serializer.data


class UserAuthView(views.APIView):
    def post(self, request):
        credentials = {
            'username': request.data.get('username'),
            'password': request.data.get('password')
        }

        registration_id = request.data.get('registration_id', None)

        if not all(credentials.values()):
            msg = 'Must include "username" and "password".'
            return Response({'errors': [msg]}, status=status.HTTP_403_FORBIDDEN)

        user = authenticate(**credentials)

        if user:
            if not user.is_active:
                msg = 'User account is disabled.'
                return Response({'errors': [msg]}, status=status.HTTP_403_FORBIDDEN)

            _clear_auth_data(user, registration_id, True)
            if registration_id:
                _update_device_token(user, registration_id)

            return Response({
                'token': Token.objects.create(user=user).key,
            }, status=status.HTTP_200_OK)
        else:
            msg = 'Unable to login with provided credentials.'
            return Response({'errors': [msg]}, status=status.HTTP_403_FORBIDDEN)

    def delete(self):
        if self.request.user.is_authenticated():
            _clear_auth_data(self.request.user, None, False)

        return Response(status=status.HTTP_204_NO_CONTENT)


class APNSDeviceView(APNSDeviceViewSet):
    def create(self, request, *args, **kwargs):

        registration_id = request.data['registration_id']

        data = _update_device_token(request.user, registration_id)
        if data is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        headers = self.get_success_headers(data)
        return Response(data=data, status=status.HTTP_201_CREATED, headers=headers)
