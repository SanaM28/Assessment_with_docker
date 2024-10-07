import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Post, Comment
from .forms import PostForm  # Adjust import based on your form's location
from django.http import JsonResponse


class AddPostViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.url = reverse("addpost")

    def test_add_post_authenticated(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            self.url,
            {
                "title": "Test Post",
                "description": "This is a test post description.",
                "timestamp": "2024-10-04 12:00:00",  # Ensure correct format
                "status": "Ongoing",  # Ensure it matches model choices
            },
        )

        if response.status_code != 302:
            print(response.context["form"].errors)

        self.assertEqual(response.status_code, 302)  # Expect redirect if successful

    def test_add_post_unauthenticated(self):
        response = self.client.post(
            self.url,
            {
                "title": "Test Post",
                "description": "This should not work.",
                "timestamp": "2024-01-01 00:00:00",
                "status": "Ongoing",
            },
        )

        self.assertEqual(response.status_code, 302)  # Check for redirect to login
        self.assertRedirects(response, "/login/")  # Ensure it redirects to login page

    def test_add_post_invalid_form(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            self.url,
            {
                "title": "",  # Invalid title
                "description": "",
                "timestamp": "",
                "status": "",
            },
        )

        self.assertEqual(response.status_code, 200)  # Should return to the form page
        # self.assertTemplateUsed(response, 'blog/addpost.html')  # Ensure the correct template is used
        self.assertTrue(
            response.context["form"].errors
        )  # Check that there are form errors


class UpdatePostViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.post = Post.objects.create(
            title="Updated Title", description="Updated description"
        )
        self.url = reverse("updatepost", kwargs={"id": self.post.id})

    def test_update_post_authenticated(self):
        # Log in the user
        self.client.login(username="testuser", password="testpassword")

        # Send a GET request to load the update form
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, 200
        )  # Expect the update form to load successfully

        # Update data to post
        data = {
            "title": "Updated Title",
            "description": "Updated description",
        }

        # Send a POST request to update the post
        response = self.client.post(self.url, data)

        # Verify that the post was updated
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Updated Title")
        self.assertEqual(self.post.description, "Updated description")

    def test_update_post_invalid_form(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            self.url, {"title": ""}
        )  # Invalid data (title is required)
        self.assertEqual(
            response.status_code, 200
        )  # Should return the form with errors

        form = response.context.get("form")
        self.assertTrue(form.errors)
        self.assertIn("title", form.errors)

    def test_update_post_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, "/login/", fetch_redirect_response=False)


class DeletePostViewTests(TestCase):
    def setUp(self):
        # Create a user for authentication
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

        # Create a sample post to be deleted
        self.post = Post.objects.create(
            title="Test Post",
            description="Test description",
            status="Ongoing",
        )

    def test_delete_post_authenticated(self):
        # Log in the user
        self.client.login(username="testuser", password="testpassword")

        # Define the URL for deleting the post
        url = reverse("deletepost", kwargs={"id": self.post.id})

        # Send a POST request to delete the post
        response = self.client.post(url)

        # Check that the user is redirected to the dashboard after a successful deletion
        self.assertRedirects(response, "/dashboard/")

        # Verify that the post no longer exists
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(pk=self.post.id)

    def test_delete_post_unauthenticated(self):
        # Define the URL for deleting the post
        url = reverse("deletepost", kwargs={"id": self.post.id})

        # Send a POST request to delete the post without logging in
        response = self.client.post(url)

        # Check that the unauthenticated user is redirected to the login page
        self.assertRedirects(response, "/login/")

        # Verify that the post still exists
        post_exists = Post.objects.filter(pk=self.post.id).exists()
        self.assertTrue(post_exists)


class AddCommentViewTests(TestCase):
    def setUp(self):
        # Create a user for authentication
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

        # Create a sample post to add comments to
        self.post = Post.objects.create(
            title="Test Post",
            description="Test description",
            status="Ongoing",
        )

        # Log in the user
        self.client.login(username="testuser", password="testpassword")

    def test_add_comment_success(self):
        # Define the URL for adding a comment
        url = reverse("add_comment")

        # Define the data to be sent in the POST request
        data = {"post_id": self.post.id, "content": "This is a test comment."}

        # Send a POST request to add the comment
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Verify that the response indicates success
        response_data = json.loads(response.content)
        self.assertEqual(response_data["message"], "Comment added successfully")

        # Verify that the comment was added to the database
        comment_exists = Comment.objects.filter(
            post=self.post, user=self.user, content="This is a test comment."
        ).exists()
        self.assertTrue(comment_exists)


class GetCommentsViewTests(TestCase):
    def setUp(self):
        # Create a user for authentication
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

        # Create a sample post to add comments to
        self.post = Post.objects.create(
            title="Test Post",
            description="Test description",
            status="Ongoing",
        )

        # Create some comments for the post
        Comment.objects.create(post=self.post, user=self.user, content="First comment")
        Comment.objects.create(post=self.post, user=self.user, content="Second comment")

    def test_get_comments_success(self):
        # Define the URL for getting comments, passing the post ID as an argument
        url = reverse("get_comments", args=[self.post.id])

        # Send a GET request to retrieve comments for the post
        response = self.client.get(url)

        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Parse the response content
        response_data = json.loads(response.content)

        # Verify that the response contains the correct number of comments
        self.assertEqual(len(response_data["comments"]), 2)

        # Verify that the content of the comments matches what was added
        self.assertEqual(response_data["comments"][0]["content"], "Second comment")
        self.assertEqual(response_data["comments"][1]["content"], "First comment")

    def test_get_comments_no_comments(self):
        # Create a new post with no comments
        new_post = Post.objects.create(
            title="New Post",
            description="New post description",
            status="Ongoing",
        )

        # Define the URL for getting comments for the new post
        url = reverse("get_comments", args=[new_post.id])

        # Send a GET request to retrieve comments for the new post
        response = self.client.get(url)

        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Parse the response content
        response_data = json.loads(response.content)

        # Verify that the response contains an empty list of comments
        self.assertEqual(response_data["comments"], [])


class GetCommentsViewTests(TestCase):
    def setUp(self):
        # Create a user for authentication
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

        # Create a sample post to add comments to
        self.post = Post.objects.create(
            title="Test Post",
            description="Test description",
            status="Ongoing",
        )

        # Create some comments for the post
        Comment.objects.create(post=self.post, user=self.user, content="First comment")
        Comment.objects.create(post=self.post, user=self.user, content="Second comment")

    def test_get_comments_success(self):
        # Define the URL for getting comments, passing the post ID as an argument
        url = reverse("get_comments", args=[self.post.id])

        # Send a GET request to retrieve comments for the post
        response = self.client.get(url)

        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Parse the response content
        response_data = json.loads(response.content)

        # Verify that the response contains the correct number of comments
        self.assertEqual(len(response_data["comments"]), 2)

        # Verify that the content of the comments matches what was added
        self.assertEqual(response_data["comments"][0]["content"], "Second comment")
        self.assertEqual(response_data["comments"][1]["content"], "First comment")

    def test_get_comments_no_comments(self):
        # Create a new post with no comments
        new_post = Post.objects.create(
            title="New Post",
            description="New post description",
            status="Ongoing",
        )

        # Define the URL for getting comments for the new post
        url = reverse("get_comments", args=[new_post.id])

        # Send a GET request to retrieve comments for the new post
        response = self.client.get(url)

        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Parse the response content
        response_data = json.loads(response.content)

        # Verify that the response contains an empty list of comments
        self.assertEqual(response_data["comments"], [])
