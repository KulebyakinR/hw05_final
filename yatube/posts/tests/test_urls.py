from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user_author,
        )

        cls.INDEX = reverse('posts:index')
        cls.GROUP_LIST = reverse(
            'posts:group_list', kwargs={'slug': cls.group.slug}
        )
        cls.POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )
        cls.PROFILE = reverse(
            'posts:profile', kwargs={'username': cls.post.author}
        )
        cls.POST_CREATE = reverse('posts:post_create')
        cls.POST_EDIT = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.id}
        )
        cls.UNEXISTING_PAGE = '/unexistint_page/'
        cls.LOGIN = reverse('users:login')

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.user)

    def test_url_exists_at_guest_client(self):
        """Проверка доступа страниц для гостя"""
        guest_client_url_code = (
            (self.guest_client, self.INDEX, HTTPStatus.OK),
            (self.guest_client, self.GROUP_LIST, HTTPStatus.OK),
            (self.guest_client, self.PROFILE, HTTPStatus.OK),
            (self.guest_client, self.POST_DETAIL, HTTPStatus.OK),
            (self.guest_client, self.POST_EDIT, HTTPStatus.FOUND),
            (self.guest_client, self.POST_CREATE, HTTPStatus.FOUND),
            (self.guest_client, self.UNEXISTING_PAGE, HTTPStatus.NOT_FOUND),
        )
        for client, url, code in guest_client_url_code:
            with self.subTest(url=url):
                self.assertEqual(client.get(url).status_code, code)

    def test_url_exists_at_author_client(self):
        """Проверка доступа страниц для автора"""
        author_client_url_code = (
            (self.author_client, self.INDEX, HTTPStatus.OK),
            (self.author_client, self.GROUP_LIST, HTTPStatus.OK),
            (self.author_client, self.PROFILE, HTTPStatus.OK),
            (self.author_client, self.POST_DETAIL, HTTPStatus.OK),
            (self.author_client, self.POST_EDIT, HTTPStatus.OK),
            (self.author_client, self.POST_CREATE, HTTPStatus.OK),
            (self.author_client, self.UNEXISTING_PAGE, HTTPStatus.NOT_FOUND),
        )
        for client, url, code in author_client_url_code:
            with self.subTest(url=url):
                self.assertEqual(client.get(url).status_code, code)

    def test_url_exists_at_not_author_client(self):
        """Проверка доступа страниц для авторизованного, не автора"""
        not_author_client_url_code = (
            (self.not_author_client, self.INDEX, HTTPStatus.OK),
            (self.not_author_client, self.GROUP_LIST, HTTPStatus.OK),
            (self.not_author_client, self.PROFILE, HTTPStatus.OK),
            (self.not_author_client, self.POST_DETAIL, HTTPStatus.OK),
            (self.not_author_client, self.POST_EDIT, HTTPStatus.FOUND),
            (self.not_author_client, self.POST_CREATE, HTTPStatus.OK),
            (self.not_author_client, self.UNEXISTING_PAGE,
                HTTPStatus.NOT_FOUND)
        )
        for client, url, code in not_author_client_url_code:
            with self.subTest(url=url):
                self.assertEqual(client.get(url).status_code, code)
