import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        image = 'posts/small.gif'

        form_data = {
            "text": "Тестовый текст",
            "group": self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True)
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        last_post = Post.objects.latest('pub_date')
        dict_form_data = {
            last_post.text: form_data['text'],
            last_post.group: self.group,
            last_post.author: self.user,
            last_post.image: image,
        }
        for key_form_data, expected_object in dict_form_data.items():
            with self.subTest(expected_object=expected_object):
                self.assertEqual(key_form_data, expected_object)

    def test_edit_form(self):
        """Проверка измения записи в БД при редактировании поста"""
        self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        post_new_data = {
            'text': 'Другой текст поста',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ), data=post_new_data
        )
        self.assertTrue(Post.objects.filter(
            text=post_new_data['text'],
            group=post_new_data['group'],
        ).exists()
        )

    def test_add_comment(self):
        TEXT = 'Текст комментария'
        comments_count = Comment.objects.count()
        post_id = self.post.id
        form_data = {
            'text': TEXT
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(post_id,)),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=TEXT,
                author=self.user,
            ).exists()
        )
