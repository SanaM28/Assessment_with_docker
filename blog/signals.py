from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps  # Import apps to use get_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger("blog")


@receiver(post_save, sender="blog.Post")
def send_notification(sender, instance, created, **kwargs):
    """
    Sends a notification to all users when a blog post is created or updated.

    This function listens for the post_save signal from the Post model.
    When a post is created or updated, it sends a notification message
    to the WebSocket group for real-time updates.

    Parameters:
    sender (Model): The model class that sent the signal.
    instance (Post): The instance of the Post that was saved.
    created (bool): A boolean indicating whether a new record was created.
    **kwargs: Additional keyword arguments.
    """
    Post = apps.get_model("blog", "Post")  # Get the Post model dynamically
    channel_layer = get_channel_layer()

    if created:
        message = f"New post created: {instance.title[:30]}{'...' if len(instance.title) > 30 else ''}"
        logger.info("A new post was created: %s", message)
    else:
        message = f"Post updated: {instance.title[:30]}{'...' if len(instance.title) > 30 else ''}"
        logger.info("A post was updated: %s", message)

    try:
        # Send the notification to all users
        async_to_sync(channel_layer.group_send)(
            "blog_updates", {"type": "notification", "data": message}
        )
        logger.debug("Notification sent successfully to group 'blog_updates'.")
    except Exception as e:
        logger.error("Error occurred while sending notification: %s", str(e))
