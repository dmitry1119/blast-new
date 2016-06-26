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

from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.routers import DefaultRouter
from countries.views import CountryViewSet

from users.views import UserViewSet
from smsconfirmation.views import PhoneConfirmView

api_1 = DefaultRouter()
api_1.register('users', UserViewSet)
api_1.register('countries', CountryViewSet)

urlpatterns = [
    url(r'api/v1/', include(api_1.urls)),
    url(r'api/v1/phone', PhoneConfirmView.as_view(), name='phone-confirmation'),

    url(r'^admin/', admin.site.urls),
    url(r'^auth/v1/token/', obtain_jwt_token, name='get-auth-token'),
]
