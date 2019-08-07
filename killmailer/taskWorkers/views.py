from .models import Task
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse

# Create your views here.
def get_status(self, id, hash):
    task = get_object_or_404(Task, pk=id, hash=hash)
    json = {}
    json['progress'] = task.progress
    json['status'] = task.get_status_display()
    json['started'] = task.started_at
    return JsonResponse(json)
