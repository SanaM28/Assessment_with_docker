from django.conf import settings
from django.contrib import admin
from django.urls import path
from blog import views
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("signup/", views.user_signup, name="signup"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("addpost/", views.add_post, name="addpost"),
    path("updatepost/<int:id>", views.update_post, name="updatepost"),
    path("deletepost/<int:id>", views.delete_post, name="deletepost"),
    path("add_comment/", views.add_comment, name="add_comment"),
    path("comments/<int:post_id>/", views.get_comments, name="get_comments"),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root="/home/user/Documents/LIVE_BLOG/Blog_App/miniblog/blog/static/",
    )
