from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Import your signals here to register them
import blog.signals


class Post(models.Model):
    STATUS_CHOICES = (
        ("ongoing", "Ongoing"),
        ("ended", "Ended"),
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ongoing")


class Comment(models.Model):
    post = models.ForeignKey("Post", on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"
