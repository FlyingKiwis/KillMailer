from django.urls import path, re_path

from . import views

urlpatterns = [
    path('home', views.home, name='home'),
    path('compose', views.compose, name='compose'),
    path('send', views.send, name='send'),
    path('sent/<int:batch>', views.sent, name='sent')
]
