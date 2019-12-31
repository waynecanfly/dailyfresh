from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include

from apps.goods import views

urlpatterns = [
    url(r'^$', views.index, name='index'), # 跳转到首页
]
