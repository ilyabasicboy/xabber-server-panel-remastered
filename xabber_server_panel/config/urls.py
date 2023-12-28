from django.contrib import admin
from django.urls import path, include
from .views import CreateHost, ConfigModules, RootPageView, ConfigHosts, ConfigAdmins, ConfigLdap


urlpatterns = [
    path('hosts/', ConfigHosts.as_view(), name='hosts'),
    path('admins/', ConfigAdmins.as_view(), name='admins'),
    path('ldap/', ConfigLdap.as_view(), name='ldap'),
    path('modules/', ConfigModules.as_view(), name='modules'),
    path('host/create/', CreateHost.as_view(), name='host_create'),
    path('root_page/', RootPageView.as_view(), name='root_page'),
]
