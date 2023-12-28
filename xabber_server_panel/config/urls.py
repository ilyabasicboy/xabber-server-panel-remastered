from django.contrib import admin
from django.urls import path, include
from .views import CreateHost, Modules, RootPageView, ConfigHosts, ConfigAdmins


urlpatterns = [
    path('hosts/', ConfigHosts.as_view(), name='hosts'),
    path('admins/', ConfigAdmins.as_view(), name='admins'),
    path('host/create/', CreateHost.as_view(), name='host_create'),
    path('modules/', Modules.as_view(), name='modules'),
    path('root_page/', RootPageView.as_view(), name='root_page'),
]
