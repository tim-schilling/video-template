from django.contrib import admin

from forum.models import Comment, Topic


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "created_at"]
    list_filter = ["author"]
    search_fields = ["title", "body"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["topic", "author", "created_at"]
    list_filter = ["author"]
    search_fields = ["body"]
