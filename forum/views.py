from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from forum.forms import CommentForm, TopicForm
from forum.models import Topic
from forum.tasks import notify_new_comment


class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("topic-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class TopicListView(ListView):
    model = Topic
    context_object_name = "topics"
    paginate_by = 20


class TopicDetailView(DetailView):
    model = Topic
    context_object_name = "topic"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.comments.select_related("author")
        context["comment_form"] = CommentForm()
        return context


class TopicCreateView(LoginRequiredMixin, CreateView):
    model = Topic
    form_class = TopicForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class CommentCreateView(LoginRequiredMixin, CreateView):
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        self.topic = get_object_or_404(Topic, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.topic = self.topic
        form.instance.author = self.request.user
        response = super().form_valid(form)
        notify_new_comment.enqueue(self.object.id)
        return response

    def get_success_url(self):
        return self.topic.get_absolute_url()

    def form_invalid(self, form):
        return redirect(self.topic.get_absolute_url())
