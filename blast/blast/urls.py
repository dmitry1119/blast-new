"""blast URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.conf.urls.static import static
from push_notifications.api.rest_framework import APNSDeviceAuthorizedViewSet

from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from rest_framework.routers import DefaultRouter
from countries.views import CountryViewSet
from notifications.views import NotificationsViewSet, FollowRequestViewSet
from tags.views import TagsViewSet

from users.views import (UserViewSet, UserProfileView, UserSettingsView,
                         UserPasswordResetView, UserChangePhoneView, UsernameSearchView, UserSearchView)
from smsconfirmation.views import (PhoneConfirmView, ResetPasswordView,
                                   SinchPhoneConfirmationView)

from posts.views import (PostsViewSet, CommentsViewSet, VotedPostsViewSet,
                         DonwvotedPostsViewSet, PinnedPostsViewSet, FeedsView, PostSearchViewSet)

api_1 = DefaultRouter()
api_1.register(r'feeds', FeedsView, base_name='feed')
api_1.register(r'users/search', UserSearchView, base_name='user-search')
api_1.register(r'users', UserViewSet)
api_1.register(r'usernames', UsernameSearchView, base_name='usernames')
api_1.register(r'countries', CountryViewSet, base_name='country')
api_1.register(r'posts/pinned', PinnedPostsViewSet, base_name='pinned')
api_1.register(r'posts/downvoted', DonwvotedPostsViewSet, base_name='downvoted')
api_1.register(r'posts/voted', VotedPostsViewSet, base_name='voted')
api_1.register(r'posts/search', PostSearchViewSet, base_name='post-search')
api_1.register(r'posts', PostsViewSet, base_name='posts')
api_1.register(r'comments', CommentsViewSet, base_name='comment')
api_1.register(r'tags', TagsViewSet, base_name='tag')
api_1.register(r'notifications/follow', FollowRequestViewSet, base_name='followrequest')
api_1.register(r'notifications', NotificationsViewSet, base_name='notifications')
api_1.register(r'devices/apns', APNSDeviceAuthorizedViewSet, base_name='apns-device')

urlpatterns = [
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^admin/', admin.site.urls),

    url(r'^api/v1/user/password/$', UserPasswordResetView.as_view(), name='user-password-auth'),
    url(r'^api/v1/user/profile/$', UserProfileView.as_view(), name='user-profile'),
    url(r'^api/v1/user/settings/$', UserSettingsView.as_view(), name='user-settings'),
    url(r'^api/v1/user/phone/$', UserChangePhoneView.as_view(), name='user-phone'),

    url(r'^api/v1/token/refresh/', refresh_jwt_token, name='refresh-token'),
    url(r'^api/v1/token/$', obtain_jwt_token, name='get-auth-token'),
    url(r'^api/v1/sms/phone', PhoneConfirmView.as_view(), name='phone-confirmation'),
    url(r'^api/v1/sms/password/', ResetPasswordView.as_view(), name='reset-password'),

    url(r'^api/v1/phone/verification', SinchPhoneConfirmationView.as_view(),
        name='sinch-phone-confirmation'),

    url(r'^api/v1/', include(api_1.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
