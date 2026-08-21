import logging

from django_tasks import task

from forum.models import Comment

logger = logging.getLogger(__name__)


@task
def notify_new_comment(comment_id):
    comment = Comment.objects.select_related("topic", "author").get(id=comment_id)
    logger.info(
        "New comment by %s on topic %r: %s",
        comment.author,
        comment.topic.title,
        comment.body,
    )
