import os
import uuid
from django.db import models
from django.contrib.auth.models import User

def user_upload_path(instance, filename):
    """Generate upload path for user files"""
    return f'users/{instance.owner.username}/files/{filename}'

class UploadedFile(models.Model):
    """Model for storing file information"""
    
    FILE_TYPES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('archive', 'Archive'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=user_upload_path)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='other')
    size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100, blank=True)
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    
    is_public = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return f"{self.name} ({self.owner.username})"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
            self.name = self.name or self.file.name
        super().save(*args, **kwargs)

class Note(models.Model):
    """Model for storing notes"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.title} ({self.owner.username})"