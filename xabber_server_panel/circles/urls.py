from django.contrib import admin
from django.urls import path, include
from xabber_server_panel.circles.views import CircleList, CircleCreate, CircleDetail


urlpatterns = [
    path('', CircleList.as_view(), name='list'),
    path('create/', CircleCreate.as_view(), name='create'),
    path('detail/<int:id>/', CircleDetail.as_view(), name='detail'),
]
