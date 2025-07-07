from django.db import models
from django.conf import settings
import json

# Create your models here.

class ChatHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prompt = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    news_title = models.CharField(max_length=500, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)  # Store additional data like analysis type, sections, etc.
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Chat histories"
        
    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        
    def get_metadata_display(self):
        """Format metadata for display"""
        if not self.metadata:
            return None
            
        if isinstance(self.metadata, str):
            try:
                return json.loads(self.metadata)
            except:
                return self.metadata
                
        return self.metadata
