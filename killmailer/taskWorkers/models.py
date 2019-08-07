from django.db import models
import hashlib
import random

def create_hash():
    return hashlib.sha256(str(random.getrandbits(256)).encode('utf-8')).hexdigest()[-10:]

# Create your models here.
class Task(models.Model):
    PENDING = 'P'
    RUNNING = 'R'
    DONE = 'D'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (RUNNING, 'Running'),
        (DONE, 'Complete'),
    ]

    hash = models.CharField(max_length=25,default=create_hash)
    created_at=models.DateTimeField(auto_now_add=True)
    started_at=models.DateTimeField(null=True)
    finished_at=models.DateTimeField(null=True)
    has_error=models.BooleanField(default=False)
    error=models.TextField(null=True)
    progress=models.FloatField(default=0)
    status=models.CharField(max_length=1, choices=STATUS_CHOICES, default=PENDING)