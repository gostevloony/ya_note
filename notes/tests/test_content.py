from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note
from notes.tests.test_routes import User


class TestContent(TestCase):
    NOTES_LIST_URL = reverse('notes:list')
    NOTES_ADD_URL = reverse('notes:add')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.author_logged = Client()
        cls.reader_logged = Client()
        cls.author_logged.force_login(cls.author)
        cls.reader_logged.force_login(cls.reader)
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=cls.author,
        )
        cls.notes_edit_url = reverse('notes:edit', args=(cls.notes.slug,))

    def test_notes_list_for_different_users(self):
        # 1. Отдельная заметка передается на страницу со списком заметок
        # в списке object_list в словаре context.
        # 2. В список заметок одного пользователя не попадают заметки
        # другого пользователя.
        users_statuses = (
            (self.author_logged, True),
            (self.reader_logged, False),
        )
        for user, status in users_statuses:
            with self.subTest():
                response = user.get(self.NOTES_LIST_URL)
                object_list = response.context['object_list']
                self.assertEqual(self.notes in object_list, status)

    def test_anonymous_client_has_no_form(self):
        # 3. На страницы создания и редактирования заметки передаются формы.
        for url in (self.NOTES_ADD_URL, self.notes_edit_url):
            with self.subTest():
                response = self.author_logged.get(url)
                self.assertIn('form', response.context)
