from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('callback', views.callback, name='callback')

]