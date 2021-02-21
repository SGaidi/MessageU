from django.urls import path
from serverapp import views


urlpatterns = [
    path('', views.index, name='index',)
]
