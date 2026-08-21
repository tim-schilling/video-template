import factory
from django.contrib.auth import get_user_model

from forum.models import Comment, Topic


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"user{n}")


class TopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Topic

    title = factory.Sequence(lambda n: f"Topic {n}")
    body = "Topic body"
    author = factory.SubFactory(UserFactory)


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    topic = factory.SubFactory(TopicFactory)
    author = factory.SubFactory(UserFactory)
    body = "Comment body"
