from django.urls import path
from .views import CreateHost, Modules, DeleteModule, RootPageView, Hosts, Admins, Ldap, DeleteHost, DetailHost, ConfigRoot


urlpatterns = [
    path('', ConfigRoot.as_view(), name='root'),
    path('hosts/', Hosts.as_view(), name='hosts'),
    path('admins/', Admins.as_view(), name='admins'),
    path('ldap/', Ldap.as_view(), name='ldap'),
    path('modules/', Modules.as_view(), name='modules'),
    path('modules/delete/<str:module>/', DeleteModule.as_view(), name='delete_module'),
    path('host/create/', CreateHost.as_view(), name='host_create'),
    path('host/delete/<int:id>/', DeleteHost.as_view(), name='host_delete'),
    path('host/detail/<int:id>/', DetailHost.as_view(), name='host_detail'),
    path('root_page/', RootPageView.as_view(), name='root_page'),
]
