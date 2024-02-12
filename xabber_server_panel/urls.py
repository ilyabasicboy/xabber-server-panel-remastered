from django.urls import path, include

from xabber_server_panel.views import HomePage, Search, Root
from xabber_server_panel.utils import get_modules


urlpatterns = [
    path('', Root.as_view(), name='root'),
    path('', include('xabber_server_panel.base_modules.urls')),
    path('home/', HomePage.as_view(), name='home'),
    path('search/', Search.as_view(), name='search'),
    path('auth/', include(('xabber_server_panel.custom_auth.urls', 'custom_auth'), namespace='custom_auth')),
    path('webhooks/', include(('xabber_server_panel.webhooks.urls', 'webhooks'), namespace='webhooks')),
    path('installation/', include(('xabber_server_panel.installation.urls', 'installation'), namespace='installation')),
]

for module in get_modules():
    urlpatterns += [path(f'modules/{module}/', include((f'modules.{module}.urls', module), namespace=module))]