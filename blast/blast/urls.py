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
from django.conf.urls import url, include
from django.contrib import admin

from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from rest_framework.routers import DefaultRouter
from countries.views import CountryViewSet

from users.views import UserViewSet, UserProfileView, UserSettingsView, UserPasswordResetView, UserChangePhoneView
from smsconfirmation.views import PhoneConfirmView, ResetPasswordView
from posts.views import PostsViewSet, CommentsViewSet, VotedPostsViewSet, DonwvotedPostsViewSet

api_1 = DefaultRouter()
api_1.register('users', UserViewSet)
api_1.register('countries', CountryViewSet)
api_1.register('posts/downvoted', DonwvotedPostsViewSet, base_name='downvoted')
api_1.register('posts/voted', VotedPostsViewSet, base_name='voted')
api_1.register('posts', PostsViewSet)
api_1.register('comments', CommentsViewSet, base_name='comment')

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
    url(r'^api/v1/', include(api_1.urls)),
]
