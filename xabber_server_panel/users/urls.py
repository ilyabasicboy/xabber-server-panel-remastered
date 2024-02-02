from django.urls import path
from xabber_server_panel.users.views import CreateUser, UserDetail, UserList, UserVcard, UserSecurity, \
    UserCircles, UserPermissions, UserDelete, UserBlock


urlpatterns = [
    path('', UserList.as_view(), name='list'),
    path('create/', CreateUser.as_view(), name='create'),
    path('detail/<int:id>/', UserDetail.as_view(), name='detail'),
    path('block/<int:id>/', UserBlock.as_view(), name='block'),
    path('delete/<int:id>/', UserDelete.as_view(), name='delete'),
    path('vcard/<int:id>/', UserVcard.as_view(), name='vcard'),
    path('security/<int:id>/', UserSecurity.as_view(), name='security'),
    path('manage_circles/<int:id>/', UserCircles.as_view(), name='circles'),
    path('permissions/<int:id>/', UserPermissions.as_view(), name='permissions'),
]
