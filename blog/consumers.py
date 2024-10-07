from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging

logger = logging.getLogger("blog")


class BlogConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time blog updates and comments.

    This consumer handles connections for the blog application and processes
    messages related to blog posts and comments.
    """

    async def connect(self):
        """
        Accept the WebSocket connection and join the group for blog updates.
        """
        self.group_name = "blog_updates"
        # Join the WebSocket group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(
            f"WebSocket connection established and added to group:{self.group_name}"
        )

    async def disconnect(self, close_code):
        """
        Leave the WebSocket group when the connection is closed.

        Parameters:
        close_code (int): The code indicating why the connection was closed.
        """
        await self.channel_layer.group_discard("blog_updates", self.channel_name)
        logger.info(
            "WebSocket connection closed and removed from group '%s'.", self.group_name
        )

    async def blog_post_update(self, event):
        # Handle the blog_post_update message type
        """
        Handle the blog_post_update message type and send updated post data.

        Parameters:
        event (dict): The event data containing the updated post information.
        """
        data = event["data"]  # Extract the data from the event
        await self.send(
            text_data=json.dumps(
                {
                    "type": "blog_post_update",
                    "id": data["id"],
                    "title": data["title"],
                    "description": data["description"],
                    "timestamp": data["timestamp"],
                    "status": data["status"],
                }
            )
        )
        logger.debug(f"Sent blog post update:{data}")

    async def blog_post_edit(self, event):
        # Handle post updates
        """
        Handle post updates and send updated post data.

        Parameters:
        event (dict): The event data containing the edited post information.
        """
        data = event["data"]  # Extract the data from the event
        await self.send(
            text_data=json.dumps(
                {
                    "type": "blog_post_edit",
                    "id": data["id"],
                    "title": data["title"],
                    "description": data["description"],
                    "timestamp": data["timestamp"],
                    "status": data["status"],
                }
            )
        )
        logger.debug(f"Sent blog post edit: {data}")

    async def blog_delete_post(self, event):
        # Handle the blog_delete_post message type
        """
        Handle the blog_delete_post message type and notify about the deleted post.

        Parameters:
        event (dict): The event data containing the ID of the deleted post.
        """
        data = event["data"]
        await self.send(
            text_data=json.dumps(
                {
                    "type": "blog_delete_post",
                    "id": data["id"],
                }
            )
        )
        logger.info("Sent notification for deleted post.")

    async def new_comment(self, event):
        """
        Handle new comments and send comment data to the WebSocket.

        Parameters:
        event (dict): The event data containing the new comment information.
        """
        data = event["data"]

        await self.send(
            text_data=json.dumps(
                {
                    "type": "new_comment",
                    "post_id": data["post_id"],
                    "user": data["user"],
                    "content": data["content"],
                    "timestamp": data["timestamp"],
                }
            )
        )
        logger.debug(f"Sent new comment: {data}")

    # New function to handle blog post notifications
    async def notification(self, event):
        """
        Handle blog post notifications and send notification messages to the WebSocket.

        Parameters:
        event (dict): The event data containing the notification message.
        """
        message = event["data"]

        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "message": message,
                }
            )
        )
        logger.info(f"Sent notification message: {message}")
