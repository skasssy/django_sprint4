from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.forms import ModelForm
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from blog.models import Post, Category, Comment
from blog.forms import CommentForm


class IndexListView(ListView):
    model = Post
    paginate_by = settings.POSTS_PER_PAGE
    template_name = 'blog/index.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        return Post.objects.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        ).select_related('category', 'author', 'location'
                         ).annotate(comment_count=Count('comment')
                                    ).order_by('-pub_date')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        queryset = Post.objects.select_related('category', 'author', 'location').prefetch_related(
            Prefetch('comment', queryset=Comment.objects.order_by('created_at'))
        )

        if self.request.user.is_authenticated:
            return queryset.filter(
                Q(is_published=True, category__is_published=True,
                  pub_date__lte=timezone.now()) |
                Q(author=self.request.user)
            )
        return queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comment'] = self.object.comment.all()
        return context


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )

    post_list = Post.objects.select_related(
        'author', 'location'
    ).filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(comment_count=Count('comment')
               ).order_by('-pub_date')
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'category': category, 'page_obj': page_obj}
    return render(request, template, context)


User = get_user_model()


class ProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = Post.objects.filter(author=self.object
        ).select_related(
            'author', 'category', 'location'
        ).annotate(
            comment_count=Count('comment')
        ).order_by('-pub_date')
        paginator = Paginator(posts, settings.POSTS_PER_PAGE)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'email']
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username':
                                                    self.request.user.username})


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'text', 'category', 'location',
              'pub_date', 'image']
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        if Post.objects.filter(
            author=self.request.user,
            title=form.instance.title,
            pub_date=form.instance.pub_date,
            text=form.instance.text
        ).exists():
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})


class PostUpdateView(UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'text', 'category', 'location', 'pub_date', 'image']
    template_name = 'blog/create.html'

    def test_func(self):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return self.request.user.is_authenticated and post.author == self.request.user

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'post_id': self.object.pk})

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return post

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('blog:post_detail', post_id=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})

    def get_object(self, queryset=None):
        post = get_object_or_404(
            Post,
            pk=self.kwargs['post_id'],
            author=self.request.user
        )
        return post


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['text']
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.object.post.pk})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    fields = ['text']
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        comment = get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post__pk=self.kwargs['post_id'],
            author=self.request.user
        )
        return comment

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'post_id': self.object.post.pk})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        comment = get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post__pk=self.kwargs['post_id'],
            author=self.request.user
        )
        return comment

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'post_id': self.object.post.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop('form', None)
        context['comment'] = self.get_object()
        return context
