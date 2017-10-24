"""workboard URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
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

import os
from django.conf.urls import url, include
from django.contrib import admin

from api import views as api_views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^userlogin/$', api_views.user_login, name = 'userlogin'),
    url(r'^userlogout/$', api_views.user_logout, name = 'userlogout'),

    url(r'^tasklist/$', api_views.task_list, name = 'tasklist'),
    url(r'^taskdetail/$', api_views.task_detail, name = 'taskdetail'),

    url(r'^contentnew/$', api_views.content_new, name = 'contentnew'),
    url(r'^contentedit/$', api_views.content_edit, name = 'contentedit'),
    url(r'^contentdel/$', api_views.content_del, name = 'contentdel'),
]
