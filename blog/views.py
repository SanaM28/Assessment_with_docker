from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.shortcuts import render, HttpResponseRedirect
from .forms import SignUpForm, LoginForm, PostForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Post, Comment
from django.contrib.auth.models import Group
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
import logging

logger = logging.getLogger("blog")


def home(request):
    """
    Displays the home page of the blog application.

    This function retrieves all blog posts from the database and renders the home page template,
    passing the list of posts as a context variable.

    Parameters:
    request (HttpRequest): The HTTP request object that contains metadata about the request.

    Returns:
    HttpResponse: A response to render the home page template with the list of blog posts.
    """
    logger.info(
        f"User {request.user.username} is authenticated and trying to add a post."
    )

    try:
        posts = Post.objects.all().order_by("-timestamp")
        logger.debug(f"Successfully retrieved {posts.count()} posts from the database.")
    except Exception as e:
        logger.error(f"An error occurred while retrieving blog posts:{str(e)}")

    return render(request, "blog/home.html", {"posts": posts})


def about(request):
    """
    Renders the about page.

    This view renders the about page that provides information about the blog.

    Parameters:
    request (HttpRequest): The HTTP request object that contains metadata about the request.

    Returns:
    HttpResponse: A response that renders the about page.
    """
    logger.info(
        "User %s accessed the about page.",
        request.user.username if request.user.is_authenticated else "Anonymous",
    )
    return render(request, "blog/about.html")


def contact(request):
    """
    Renders the contact page.

    This view renders the contact page, allowing users to view contact information.

    Parameters:
    request (HttpRequest): The HTTP request object that contains metadata about the request.

    Returns:
    HttpResponse: A response that renders the contact page.
    """
    logger.info(
        f"User {'Anonymous' if not request.user.is_authenticated else request.user.username} accessed the contact page."
    )

    return render(request, "blog/contact.html")


def dashboard(request):
    """
    Renders the dashboard page for authenticated users.

    This view checks if the user is authenticated. If authenticated, it retrieves
    all blog posts, the user's full name, and their group memberships, and renders
    the dashboard page. If the user is not authenticated, they are redirected to the login page.

    Parameters:
    request (HttpRequest): The HTTP request object that contains metadata about the request.

    Returns:
    HttpResponse: A response that renders the dashboard page with user-specific information if authenticated.
    HttpResponseRedirect: A redirect to the login page if the user is unauthenticated.
    """
    if request.user.is_authenticated:
        logger.info(f"User {request.user.username} accessed the dashboard page.")

        posts = Post.objects.all()
        user = request.user
        full_name = user.get_full_name()
        groups = user.groups.all()
        return render(
            request,
            "blog/dashboard.html",
            {"posts": posts, "full_name": full_name, "groups": groups},
        )
    else:
        logger.warning("Unauthenticated user tried to access the dashboard page.")
        return HttpResponseRedirect("/login/")


def user_signup(request):
    """
    Handles user sign-up.

    This view handles both GET and POST requests for user registration.
    If the request is a POST and the form is valid, it creates a new user, adds them to the "Author" group,
    displays a success message, and redirects to the home page.
    If the request is a GET, it displays the registration form.

    Parameters:
    request (HttpRequest): The HTTP request object that contains metadata about the request.

    Returns:
    HttpResponse: A response to render the sign-up form or to redirect to the home page after successful registration.
    """
    if request.method == "POST":
        logger.info("Handling POST request for user sign-up.")
        form = SignUpForm(request.POST)
        if form.is_valid():
            logger.debug("Sign-up form is valid. Creating a new user.")
            messages.success(request, "Congratulation !! You have become an author.")
            user = form.save()
            group = Group.objects.get(name="Author")
            user.groups.add(group)
            logger.info(
                f"User {user.username} signed up successfully and added to 'Author' group."
            )
            return HttpResponseRedirect("/")
    else:
        logger.info("Handling GET request for user sign-up.")
        form = SignUpForm()
    return render(request, "blog/signup.html", {"form": form})


def user_login(request):
    """
    Handles user login.

    This view handles both GET and POST requests for user login.
    If the user is already authenticated, they are redirected to the dashboard.
    If the request is a POST, it validates the login form and authenticates the user.
    If the credentials are valid, the user is logged in and redirected to the dashboard.
    If the request is a GET, it displays the login form.

    Parameters:
    request (HttpRequest): The HTTP request object that contains metadata about the request.

    Returns:
    HttpResponse: A response to render the login form or to redirect to the dashboard after successful login.
    """
    if not request.user.is_authenticated:
        if request.method == "POST":
            logger.info("Handling POST request for user login.")
            form = LoginForm(request=request, data=request.POST)
            if form.is_valid():
                user_name = form.cleaned_data["username"]
                user_password = form.cleaned_data["password"]
                user = authenticate(username=user_name, password=user_password)
                if user is not None:
                    login(request, user)
                    logger.info(f"User {user.username} logged in successfully.")
                    messages.success(request, "LoggedIn successfully")
                    return HttpResponseRedirect("/dashboard/")
        else:
            logger.info("Handling GET request for user login.")
            form = LoginForm()
        return render(request, "blog/login.html", {"form": form})
    else:
        logger.info(
            f"User {request.user.username} is already authenticated. Redirecting to dashboard."
        )
        return HttpResponseRedirect("/dashboard/")


def user_logout(request):
    """
    Handles user logout.

    This view logs out the currently authenticated user and redirects them to the home page.

    Parameters:
    request (HttpRequest): The HTTP request object that contains metadata about the request.

    Returns:
    HttpResponseRedirect: A redirect to the home page after successful logout.
    """

    if request.user.is_authenticated:
        logger.info(f"User {request.user.username} is logging out.")
    else:
        logger.warning("Unauthenticated user tried to access the logout view.")

    logout(request)
    logger.info("User logged out successfully.")
    return HttpResponseRedirect("/")


def add_post(request):
    """
    Handles adding a new blog post.

    This view checks if the user is authenticated and handles GET and POST requests.
    If the request is a GET request, it displays the form for adding a new post.
    If the request is a POST request, it processes the form data to add the post,
    validates the form, saves the post, and broadcasts the post to a WebSocket group
    for real-time updates.

    Parameters:
    request (HttpRequest): The HTTP request object that contains metadata about the request.

    Returns:
    HttpResponse: A response to render the add post form on a GET request.
    HttpResponseRedirect: A redirect to the home page after successfully adding a post, or
                          a redirect to the login page if the user is unauthenticated.
    """
    if request.user.is_authenticated:
        logger.info(
            "User %s is authenticated and trying to add a post.", request.user.username
        )
        if request.method == "POST":
            logger.debug("Handling POST request for adding a post.")
            form = PostForm(request.POST)
            if form.is_valid():
                logger.debug("Post form is valid. Extracting form data.")
                title = form.cleaned_data["title"]
                description = form.cleaned_data["description"]
                timestamp = form.cleaned_data["timestamp"]
                status = form.cleaned_data["status"]
                post = Post(
                    title=title,
                    description=description,
                    timestamp=timestamp,
                    status=status,
                )

                try:
                    post.save()
                    logger.info(
                        "Post titled '%s' added successfully by user %s.",
                        title,
                        request.user.username,
                    )
                except Exception as e:
                    logger.error("Error occurred while saving post: %s", str(e))
                    return render(
                        request,
                        "blog/addpost.html",
                        {
                            "form": form,
                            "error": "An error occurred while saving the post.",
                        },
                    )

                # Broadcast the new post to the WebSocket group
                logger.debug("Broadcasting the new post to the WebSocket group.")
                channel_layer = get_channel_layer()
                try:
                    async_to_sync(channel_layer.group_send)(
                        "blog_updates",
                        {
                            "type": "blog_post_update",  # Ensure this matches the consumer's method name
                            "data": {
                                "id": post.id,
                                "title": post.title,
                                "description": post.description,
                                "timestamp": post.timestamp.strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "status": post.status,
                            },
                        },
                    )
                    logger.info(
                        "Successfully broadcasted post titled '%s' to WebSocket group.",
                        title,
                    )
                except Exception as e:
                    logger.error(
                        "Error occurred while broadcasting the post: %s", str(e)
                    )

                return HttpResponseRedirect("/")
            else:
                logger.warning(
                    "Form data is not valid. User %s attempted to submit an invalid form.",
                    request.user.username,
                )
        else:
            logger.debug("Handling GET request for displaying the add post form.")
            form = PostForm()
        return render(request, "blog/addpost.html", {"form": form})
    else:
        logger.warning("Unauthenticated user tried to access the add post page.")
        return HttpResponseRedirect("/login/")


def update_post(request, id):
    """
    Handles updating an existing blog post.

    This view allows an authenticated user to update an existing blog post.
    If the request is a POST, it validates and saves the form data and broadcasts the update via WebSocket.
    If the request is a GET, it displays the form with the existing post data.

    Parameters:
    request (HttpRequest): The HTTP request object that contains metadata about the request.
    id (int): The ID of the post to be updated.

    Returns:
    HttpResponse: A response to render the update post form.
    HttpResponseRedirect: A redirect to the dashboard after successful update.
    """
    if request.user.is_authenticated:
        logger.info(
            f"User {request.user.username} is attempting to update post with ID {id}."
        )
        if request.method == "POST":
            try:
                post = Post.objects.get(pk=id)
            except Post.DoesNotExist:
                logger.error(f"Post with ID {id} does not exist.")
                return HttpResponseRedirect("/dashboard/")
            logger.info(f"Handling POST request to update post with ID {id}.")
            form = PostForm(request.POST, instance=post)
            if form.is_valid():
                logger.debug("Update form is valid. Saving post.")
                form.save()

                logger.debug(
                    f"Broadcasting updated post with ID {post.id} to the WebSocket group."
                )
                channel_layer = get_channel_layer()
                try:
                    async_to_sync(channel_layer.group_send)(
                        "blog_updates",
                        {
                            "type": "blog_post_edit",  # Ensure this matches the consumer's method name
                            "data": {
                                "id": post.id,
                                "title": post.title,
                                "description": post.description,
                                "timestamp": post.timestamp.strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "status": post.status,
                            },
                        },
                    )
                    logger.info(
                        f"Successfully broadcasted updated post with ID {post.id} to WebSocket group."
                    )
                except Exception as e:
                    logger.error(
                        f"Error occurred while broadcasting updated post: {str(e)}"
                    )
                # return HttpResponseRedirect("/dashboard/")
                return HttpResponseRedirect("/")
        else:
            logger.info(
                f"Handling GET request to display the update form for post with ID {id}."
            )
            post = Post.objects.get(pk=id)
            form = PostForm(instance=post)
        return render(request, "blog/updatepost.html", {"form": form})
    else:
        logger.warning("Unauthenticated user tried to access the update post view.")
        return HttpResponseRedirect("/login/")


def delete_post(request, id):
    """
    Handles the deletion of a blog post.

    This view allows an authenticated user to delete an existing blog post.
    If the request is a POST, it deletes the specified post and broadcasts the deletion via WebSocket.

    Parameters:
    request (HttpRequest): The HTTP request object that contains metadata about the request.
    id (int): The ID of the post to be deleted.

    Returns:
    HttpResponseRedirect: A redirect to the dashboard after successful deletion.
    """
    if request.user.is_authenticated:
        logger.info(
            f"User {request.user.username} is attempting to delete post with ID {id}."
        )
        if request.method == "POST":

            try:
                post = Post.objects.get(pk=id)
            except Post.DoesNotExist:
                logger.error(f"Post with ID {id} does not exist.")
                return HttpResponseRedirect("/dashboard/")

            post.delete()

            logger.info(f"Post with ID {id} deleted successfully.")
            # Broadcast the delete post to the WebSocket group
            logger.debug(
                f"Broadcasting deletion of post with ID {id} to the WebSocket group."
            )
            channel_layer = get_channel_layer()
            try:
                async_to_sync(channel_layer.group_send)(
                    "blog_updates",  # Use the same group name as in the consumer
                    {
                        "type": "blog_delete_post",  # Ensure this matches the consumer's method name
                        "data": {
                            "id": id,  # Include the post ID for reference
                        },
                    },
                )
                logger.info(
                    f"Successfully broadcasted deletion of post with ID {id} to WebSocket group."
                )
            except Exception as e:
                logger.error(
                    f"Error occurred while broadcasting deletion of post: {str(e)}"
                )
            return HttpResponseRedirect("/dashboard/")
    else:
        logger.warning("Unauthenticated user tried to access the delete post view.")
        return HttpResponseRedirect("/login/")


@login_required
@require_POST
def add_comment(request):
    """
    Handles adding a comment to a blog post.

    This view processes a POST request to add a comment to a specified blog post.
    It validates the input, saves the comment to the database, and broadcasts the new comment
    via WebSocket to update clients in real-time.

    Parameters:
    request (HttpRequest): The HTTP request object containing the comment data.

    Returns:
    JsonResponse: A JSON response indicating the success or failure of the comment addition.
    """
    # Get data from POST request
    data = json.loads(request.body)
    post_id = data.get("post_id")
    content = data.get("content")

    # Validate input
    if not post_id or not content:
        logger.warning("Invalid input: post_id or content is missing.")
        return JsonResponse({"error": "Invalid input"}, status=400)

    # Save comment to the database

    try:
        post = Post.objects.get(id=post_id)
        comment = Comment(post=post, user=request.user, content=content)
        comment.save()
    except Post.DoesNotExist:
        logger.error(f"Post with ID {post_id} does not exist.")
        return JsonResponse({"error": "Post not found"}, status=404)
    except Exception as e:
        logger.error(f"Error occurred while saving comment: {str(e)}")
        return JsonResponse({"error": "Failed to add comment"}, status=500)

    # Broadcast comment to WebSocket group
    channel_layer = get_channel_layer()

    # Debugging log
    logger.debug(
        "Broadcasting new comment to WebSocket group.",
        extra={
            "post_id": post_id,
            "user": request.user.username,
            "content": content,
            "timestamp": comment.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        },
    )

    async_to_sync(channel_layer.group_send)(
        "blog_updates",
        {
            "type": "new_comment",
            "data": {
                "post_id": post_id,
                "user": request.user.username,
                "content": content,
                "timestamp": comment.timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),  # Assuming Comment model has timestamp
            },
        },
    )

    logger.info("New comment broadcasted successfully.")

    return JsonResponse({"message": "Comment added successfully"})


def get_comments(request, post_id):
    """
    Retrieves comments for a specific blog post.

    This view fetches all comments associated with the specified post ID,
    orders them by timestamp in descending order, and returns them as a JSON response.

    Parameters:
    request (HttpRequest): The HTTP request object.
    post_id (int): The ID of the blog post for which comments are to be retrieved.

    Returns:
    JsonResponse: A JSON response containing the list of comments for the specified post.
    """
    comments = Comment.objects.filter(post_id=post_id).order_by("-timestamp")

    if not comments.exists():
        logger.warning(f"No comments found for post ID {post_id}.")
        return JsonResponse(
            {"comments": []}
        )  # Return an empty list if no comments are found.

    comments_data = [
        {
            "user": comment.user.username,
            "content": comment.content,
            "timestamp": comment.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for comment in comments
    ]

    logger.info(f"Retrieved {len(comments_data)} comments for post ID {post_id}.")
    return JsonResponse({"comments": comments_data})
