from django.db import models

# Create your models here.

class Batch(models.Model):
    subject = models.TextField()
    body = models.TextField()
    sent_by = models.CharField(max_length=250, null=True)
    sent_by_id = models.CharField(max_length=20, null=True)
    fake = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Message(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="messages")
    subject = models.TextField()
    body = models.TextField()
    sent_to = models.CharField(max_length=250)
    sent_to_id = models.CharField(max_length=20)
    sent = models.BooleanField(default=False)
    error = models.TextField(null=True)
    sent_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
