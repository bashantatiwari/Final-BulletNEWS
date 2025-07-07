from django.db import models
from django.conf import settings  # ✅ Use this instead of importing User directly
from django.utils import timezone

class GeneratedContent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # ✅ Updated line
    content_type = models.CharField(max_length=10, choices=[('PDF', 'PDF'), ('AUDIO', 'Audio')])
    category = models.CharField(max_length=50)
    file_path = models.CharField(max_length=255)
    generated_at = models.DateTimeField(default=timezone.now)
    is_downloaded = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'content_type', 'category', 'generated_at')

    def __str__(self):
        return f"{self.user.username}'s {self.content_type} for {self.category} ({self.generated_at})"
