import shutil
import tempfile
from django.conf import settings

from django.core.cache import cache
from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Group, Post, Follow
from django.core.cache import cache
from django.test import TestCase, Client, override_settings


User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        cls.group_2 = Group.objects.create(
            title="Тестовая группа2",
            slug="test_slug_2",
            description="Тестовое описание 2",
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.image = 'posts/small.gif'
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def check_contex(self, context_page):
        context_index = {
            context_page.author.username: self.post.author.username,
            context_page.text: self.post.text,
            context_page.group.title: self.post.group.title,
            context_page.image: self.image
        }
        for context_object, expected_object in context_index.items():
            with self.subTest(expected_object=expected_object):
                self.assertEqual(context_object, expected_object)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse("posts:group_list", kwargs={"slug": "test_slug"}):
                "posts/group_list.html",
            reverse("posts:profile", kwargs={"username": "auth"}):
                "posts/profile.html",
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}):
                "posts/post_detail.html",
            reverse("posts:post_edit", kwargs={"post_id": self.post.id}):
                "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
            self.guest_client.get('/unexistint_page/'): "core/404.html",
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон posts:index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        context_page = response.context["page_obj"][0]
        self.check_contex(context_page)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон posts:group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        object_list = response.context['page_obj'].object_list
        expected_posts = list(self.group.posts.all())
        self.assertListEqual(expected_posts, object_list)
        context_page = response.context["page_obj"].object_list[0]
        self.check_contex(context_page)
        self.assertEqual(context_page.group, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон posts:profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(
                'posts:profile',
                kwargs={"username": self.post.author.username},
            )
        )
        object_list = response.context['page_obj'].object_list
        expected_posts = list(Post.objects.filter(author=self.user))
        self.assertListEqual(expected_posts, object_list)
        context_page = response.context["page_obj"].object_list[0]
        self.check_contex(context_page)
        self.assertEqual(context_page.author, self.post.author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон posts:post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={"post_id": self.post.id},
            )
        )
        context_page = response.context["post"]
        self.check_contex(context_page)

    def test_post_create_page_show_correct_context(self):
        """Шаблон posts:post_create  сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_create',
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон posts:post_edit  сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={"post_id": self.post.id},
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_new_post_display(self):
        """Созданный пост появляется на главной, в группе и пройфайле"""
        self.new_post = Post.objects.create(
            text='Новейший пост',
            author=self.user,
            group=self.group_2
        )
        group = self.group_2
        user = self.user
        post = self.new_post
        page_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': group.slug}),
            reverse('posts:profile', kwargs={'username': user.username})
        ]
        for page in page_names:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                context_post = response.context['page_obj'][0]
                self.assertEqual(context_post, post)

    def test_post_corrct_not_appear(self):
        """Пост НЕ отображается в группе, к которой он не пренадлежит"""
        self.new_post = Post.objects.create(
            text='Новейший пост',
            author=self.user,
            group=self.group_2
        )
        group = self.group
        post = self.new_post
        page = reverse("posts:group_list", kwargs={"slug": group.slug})
        response = self.authorized_client.get(page)
        context_post = response.context['page_obj'][0]
        self.assertNotEqual(context_post, post)

    def test_cache_Index_page(self):
        new_post = Post.objects.create(
            text='New post',
            author=self.user
        )
        actual_page = self.authorized_client.get(
            reverse('posts:index')
        ).content
        new_post.delete()
        cached_page = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertEqual(actual_page, cached_page)
        cache.clear()
        cleared_page = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(actual_page, cleared_page)

    def test_autorized_user_get_and_remove_follow(self):
        """ Авторизованный пользователь может подписываться на других
            пользователей и удалять их из подписок.
        """
        following = User.objects.create(username='following')
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username': following})
        )
        self.assertIs(
            Follow.objects.filter(user=self.user, author=following).exists(),
            True
        )
        self.authorized_client.post(
            reverse('posts:profile_unfollow', kwargs={'username': following})
        )
        self.assertIs(
            Follow.objects.filter(user=self.user, author=following).exists(),
            False
        )

    def test_new_post_to_followers(self):
        user = User.objects.create_user(username='username')
        authorized_client = Client()
        authorized_client.force_login(user)
        Follow.objects.create(
            user=self.user,
            author=user
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        actual_count = len(response.context['page_obj'])
        Post.objects.create(
            text='Text',
            author=user,
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        new_count = len(response.context['page_obj'])
        self.assertTrue(
            new_count == actual_count + 1
        )

    def test_new_post_not_followers(self):
        user = User.objects.create_user(username='username')
        authorized_client = Client()
        authorized_client.force_login(user)
        Follow.objects.create(
            user=self.user,
            author=user
        )
        response = authorized_client.get(
            reverse('posts:follow_index')
        )
        actual_count = len(response.context['page_obj'])
        Post.objects.create(
            text='Text',
            author=user,
        )
        response = authorized_client.get(
            reverse('posts:follow_index')
        )
        new_count = len(response.context['page_obj'])
        self.assertEqual(actual_count, new_count)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )

        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'0123456789012345Тестовый пост{str(i)}',
                group=cls.group,
            )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        templates_pages_names = {
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": "test_slug"}),
            reverse("posts:profile", kwargs={"username": "auth"}),
        }
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        templates_pages_names = {
            reverse("posts:index") + '?page=2',
            reverse("posts:group_list", kwargs={"slug": "test_slug"})
            + '?page=2',
            reverse("posts:profile", kwargs={"username": "auth"}) + '?page=2',
        }
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 3)
