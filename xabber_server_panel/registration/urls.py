from django.contrib import admin
from django.urls import path, include
from .views import RegistrationList, RegistrationCreate, RegistrationUrl


urlpatterns = [
    path('', RegistrationList.as_view(), name='list'),
    path('create/<int:vhost_id>/', RegistrationCreate.as_view(), name='create'),
    path('url/<int:id>/', RegistrationUrl.as_view(), name='url'),
]
