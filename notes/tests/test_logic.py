from http import HTTPStatus

from django.test import Client, TestCase
from notes.tests.test_routes import User
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

from pytils.translit import slugify


class TestCommentCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }
        cls.NOTES_ADD_URL = reverse('notes:add')
        cls.AUTH_LOGIN_URL = reverse('users:login')
        cls.NOTES_EDIT_URL = reverse('notes:edit', args=(cls.note.slug,))
        cls.NOTES_DELETE_URL = reverse('notes:delete', args=(cls.note.slug,))
        cls.NOTES_SUCCESS_URL = reverse('notes:success')

    def test_anonymous_user_cant_create_note(self):
        # 1.1 Анонимный пользователь не может создать заметку.
        response = self.client.post(self.NOTES_ADD_URL, data=self.form_data)
        self.assertRedirects(
            response,
            f'{self.AUTH_LOGIN_URL}?next={self.NOTES_ADD_URL}'
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_user_can_create_note(self):
        # 1.2 Залогиненный пользователь может создать заметку.
        response = self.author_client.post(
            self.NOTES_ADD_URL,
            data=self.form_data
        )
        self.assertRedirects(response, self.NOTES_SUCCESS_URL)
        self.assertEqual(Note.objects.count(), 2)
        note_new = Note.objects.order_by('id').last()
        self.assertEqual(note_new.title, self.form_data['title'])
        self.assertEqual(note_new.text, self.form_data['text'])
        self.assertEqual(note_new.slug, self.form_data['slug'])
        self.assertEqual(note_new.author, self.author)

    def test_not_unique_slug(self):
        # 2. Невозможно создать две заметки с одинаковым slug.
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(
            self.NOTES_ADD_URL,
            data=self.form_data
        )
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        # 3. Если при создании заметки не заполнен slug, то он формируется
        # автоматически, с помощью функции pytils.translit.slugify.
        self.form_data.pop('slug')
        response = self.author_client.post(
            self.NOTES_ADD_URL,
            data=self.form_data
        )
        self.assertRedirects(response, self.NOTES_SUCCESS_URL)
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.order_by('id').last()
        self.assertEqual(new_note.slug, slugify(self.form_data['title']))

    def test_author_can_delete_note(self):
        # 4.1 Пользователь может удалять свои заметки.
        response = self.author_client.delete(self.NOTES_DELETE_URL)
        self.assertRedirects(response, self.NOTES_SUCCESS_URL)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cant_delete_note_of_another_user(self):
        # 4.2 Пользователь не может удалять чужие заметки.
        response = self.reader_client.delete(self.NOTES_DELETE_URL)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        # 4.3 Пользователь может редактировать свои заметки.
        response = self.author_client.post(
            self.NOTES_EDIT_URL,
            data=self.form_data
        )
        self.assertRedirects(response, self.NOTES_SUCCESS_URL)
        self.assertEqual(Note.objects.count(), 1)
        note_new = Note.objects.get()
        self.assertEqual(note_new.title, self.form_data['title'])
        self.assertEqual(note_new.text, self.form_data['text'])
        self.assertEqual(note_new.slug, self.form_data['slug'])

    def test_user_cant_edit_note_of_another_user(self):
        # 4.4 Пользователь не может редактировать чужие заметки.
        response = self.reader_client.post(
            self.NOTES_EDIT_URL,
            data=self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_old = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_old.title)
        self.assertEqual(self.note.text, note_old.text)
        self.assertEqual(self.note.slug, note_old.slug)
