from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )

    def test_pages_availability(self):
        # 1. Главная страница доступна анонимному пользователю.
        # 5. Страницы регистрации пользователей, входа в учётную запись и
        # выхода из неё доступны всем пользователям.
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        # 2. Аутентифицированному пользователю доступна страница со списком
        # заметок notes/, страница успешного добавления заметки done/, страница
        # добавления новой заметки add/.
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.OK),
        )
        urls = (
            ('notes:list'),
            ('notes:success'),
            ('notes:add'),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=None)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_availability_for_author_notes(self):
        # 3. Страницы отдельной заметки, удаления и редактирования заметки
        # доступны только автору заметки. Если на эти страницы попытается
        # зайти другой пользователь — вернётся ошибка 404.
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        urls = (
            ('notes:detail'),
            ('notes:edit'),
            ('notes:delete'),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, kwargs={'slug': self.notes.slug})
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        # 4. При попытке перейти на страницу списка заметок, страницу успешного
        # добавления записи, страницу добавления заметки, отдельной заметки,
        # редактирования или удаления заметки анонимный пользователь
        # перенаправляется на страницу логина.
        login_url = reverse('users:login')
        urls = (
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
            ('notes:detail', {'slug': self.notes.slug}),
            ('notes:edit', {'slug': self.notes.slug}),
            ('notes:delete', {'slug': self.notes.slug}),
        )
        for name, kwargs in urls:
            with self.subTest(name=name):
                url = reverse(name, kwargs=kwargs)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
