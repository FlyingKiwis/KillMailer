from django.urls import path, re_path

from . import views

urlpatterns = [
    path('status/<int:id>/<slug:hash>', views.get_status, name='task-status'),
]