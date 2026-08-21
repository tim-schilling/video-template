from django.test import TestCase

from forum.tests.factories import CommentFactory, TopicFactory


class TopicModelTests(TestCase):
    def test_str_returns_title(self):
        topic = TopicFactory(title="My topic")
        self.assertEqual(str(topic), "My topic")


class CommentModelTests(TestCase):
    def setUp(self):
        self.topic = TopicFactory()

    def test_str_includes_author_and_topic(self):
        comment = CommentFactory(topic=self.topic)
        self.assertIn(str(comment.author), str(comment))
        self.assertIn(str(self.topic), str(comment))

    def test_comments_are_ordered_by_created_at(self):
        first = CommentFactory(topic=self.topic)
        second = CommentFactory(topic=self.topic)
        third = CommentFactory(topic=self.topic)

        ordered_ids = list(self.topic.comments.values_list("id", flat=True))

        self.assertEqual(ordered_ids, [first.id, second.id, third.id])
