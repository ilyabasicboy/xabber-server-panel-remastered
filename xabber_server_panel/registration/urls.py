from django.contrib import admin
from django.urls import path, include
from .views import RegistrationList, RegistrationCreate, RegistrationUrl, RegistrationChange, RegistrationDelete


urlpatterns = [
    path('', RegistrationList.as_view(), name='list'),
    path('create/<int:vhost_id>/', RegistrationCreate.as_view(), name='create'),
    path('change/<int:vhost_id>/<str:key>/', RegistrationChange.as_view(), name='change'),
    path('delete/<int:vhost_id>/<str:key>/', RegistrationDelete.as_view(), name='delete'),
    path('url/<int:id>/', RegistrationUrl.as_view(), name='url'),
]
