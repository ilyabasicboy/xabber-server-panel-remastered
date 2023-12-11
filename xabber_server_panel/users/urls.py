from django.contrib import admin
from django.urls import path, include
from xabber_server_panel.users.views import CreateUser, UserDetail, UserList


urlpatterns = [
    path('', UserList.as_view(), name='list'),
    path('create/', CreateUser.as_view(), name='create'),
    path('detail/<int:id>/', UserDetail.as_view(), name='detail'),
]
