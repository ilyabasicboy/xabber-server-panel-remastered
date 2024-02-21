from django.urls import path, include
from .views import GroupList, GroupCreate


urlpatterns = [
    path('', GroupList.as_view(), name='list'),
    path('create/', GroupCreate.as_view(), name='create'),
]
