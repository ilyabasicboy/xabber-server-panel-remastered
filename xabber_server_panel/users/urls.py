from django.contrib import admin
from django.urls import path, include
from xabber_server_panel.users.views import CreateUser, UserDetail, UserList, UserVcard, UserSecurity, UserCircles, UserPermissions, UserDelete


urlpatterns = [
    path('', UserList.as_view(), name='list'),
    path('create/', CreateUser.as_view(), name='create'),
    path('detail/<int:id>/', UserDetail.as_view(), name='detail'),
    path('delete/<int:id>/', UserDelete.as_view(), name='delete'),
    path('vcard/<int:id>/', UserVcard.as_view(), name='vcard'),
    path('security/<int:id>/', UserSecurity.as_view(), name='security'),
    path('circles/<int:id>/', UserCircles.as_view(), name='circles'),
    path('permissions/<int:id>/', UserPermissions.as_view(), name='permissions'),
]
