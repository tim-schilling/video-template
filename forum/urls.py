from django.urls import path

from forum.views import (
    CommentCreateView,
    TopicCreateView,
    TopicDetailView,
    TopicListView,
)

urlpatterns = [
    path("", TopicListView.as_view(), name="topic-list"),
    path("topics/new/", TopicCreateView.as_view(), name="topic-create"),
    path("topics/<int:pk>/", TopicDetailView.as_view(), name="topic-detail"),
    path(
        "topics/<int:pk>/comments/",
        CommentCreateView.as_view(),
        name="comment-create",
    ),
]
