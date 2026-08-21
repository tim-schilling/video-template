from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from forum.models import Comment, Topic
from forum.tests.factories import CommentFactory, TopicFactory, UserFactory

IMMEDIATE_TASKS = {
    "default": {"BACKEND": "django_tasks.backends.immediate.ImmediateBackend"}
}


class SignUpViewTests(TestCase):
    def test_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "password1": "a-very-strong-password",
                "password2": "a-very-strong-password",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username="newuser").exists())
        self.assertIn("_auth_user_id", self.client.session)


class TopicListViewTests(TestCase):
    def test_list_view_returns_200(self):
        TopicFactory.create_batch(3)

        response = self.client.get(reverse("topic-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["topics"]), 3)


class TopicDetailViewTests(TestCase):
    def test_detail_view_shows_comments_in_order(self):
        topic = TopicFactory()
        first = CommentFactory(topic=topic)
        second = CommentFactory(topic=topic)

        response = self.client.get(reverse("topic-detail", args=[topic.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["comments"]), [first, second])


class TopicCreateViewTests(TestCase):
    def test_requires_login(self):
        response = self.client.get(reverse("topic-create"))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_user_can_create_topic(self):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.post(
            reverse("topic-create"), {"title": "Hello", "body": "World"}
        )

        self.assertEqual(response.status_code, 302)
        created = Topic.objects.get(title="Hello")
        self.assertEqual(created.author, user)


@override_settings(TASKS=IMMEDIATE_TASKS)
class CommentCreateViewTests(TestCase):
    def test_requires_login(self):
        topic = TopicFactory()
        response = self.client.get(reverse("comment-create", args=[topic.pk]))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_user_can_comment_and_task_is_enqueued(self):
        topic = TopicFactory()
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.post(
            reverse("comment-create", args=[topic.pk]), {"body": "Nice topic"}
        )

        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.get(topic=topic, author=user)
        self.assertEqual(comment.body, "Nice topic")
