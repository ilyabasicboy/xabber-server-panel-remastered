from django.urls import path, include
from .views import GroupList


urlpatterns = [
    path('', GroupList.as_view(), name='list'),
]
