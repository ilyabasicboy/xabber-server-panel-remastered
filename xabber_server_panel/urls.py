from django.contrib import admin
from django.urls import path, include

from xabber_server_panel.views import HomePage, Search
from xabber_server_panel.utils import get_modules


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomePage.as_view(), name='home'),
    path('search/', Search.as_view(), name='search'),
    path('dashboard/', include('xabber_server_panel.dashboard.urls')),
    path('auth/', include(('xabber_server_panel.custom_auth.urls', 'custom_auth'), namespace='custom_auth')),
    path('users/', include(('xabber_server_panel.users.urls', 'users'), namespace='users')),
    path('circles/', include(('xabber_server_panel.circles.urls', 'circles'), namespace='circles')),
    path('groups/', include(('xabber_server_panel.groups.urls', 'groups'), namespace='groups')),
    path('registration/', include(('xabber_server_panel.registration.urls', 'registration'), namespace='registration')),
    path('config/', include(('xabber_server_panel.config.urls', 'config'), namespace='config')),

]

for module in get_modules():
    urlpatterns += [path(f'modules/{module}/', include((f'modules.{module}.urls', module), namespace=module))]