from django import forms

from forum.models import Comment, Topic


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ["title", "body"]


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
