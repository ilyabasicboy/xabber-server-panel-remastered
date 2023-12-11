from django.contrib import admin
from django.urls import path, include
from .views import ConfigList, CreateHost, ManageAdmins, Modules


urlpatterns = [
    path('', ConfigList.as_view(), name='tabs'),
    path('host/create/', CreateHost.as_view(), name='host_create'),
    path('admins/manage/', ManageAdmins.as_view(), name='manage_admins'),
    path('modules/', Modules.as_view(), name='modules'),
    path('root_page/', Modules.as_view(), name='root_page'),
]
