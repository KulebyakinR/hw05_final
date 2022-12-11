from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Group, Post, Follow
from .utils import get_page_context

User = get_user_model()

CACHE_TIME = 20


@cache_page(20)
def index(request):
    context = {
        'group_link': 'group_link',
        'author_link': 'author_link',
        'page_obj': get_page_context(Post.objects.all(), request)
    }
    return render(request, 'posts/index.html', context)


def group_list(request, slug):
    group = get_object_or_404(Group, slug=slug)
    context = {
        'group': group,
        'author_link': 'author_link',
        'group_link': 'group_link',
        'page_obj': get_page_context(group.posts.all(), request)
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    following = user.is_authenticated and user.following.exists()
    context = {
        'author': author,
        'page_obj': get_page_context(author.posts.all(), request),
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(data=request.POST or None)
    comments = post.comments.all()
    following = (
        request.user.is_authenticated
        and post.author.following.filter(user=request.user).exists()
    )
    context = {
        "post": post,
        'form': form,
        'comments': comments,
        'following': following,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    post = Post(author=request.user)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:profile', request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': 'is_edit',
    }
    return render(
        request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follower = Follow.objects.filter(user=request.user).values('author')
    post_list = Post.objects.filter(author__in=follower)
    context = {
        'page_obj': get_page_context(post_list, request),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
        return redirect(
            'posts:profile',
            username=username
        )
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def profile_unfollow(request, username):
    user = request.user
    Follow.objects.get(user=user, author__username=username).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
