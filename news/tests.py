from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.apps import apps
from news.models import New, Category
from unittest.mock import patch
from news.views import calculate_hate_score
from news.forms import CategoryForm
from django.template.loader import render_to_string

# --------------------------------------------------- Listado de noticias --------------------------------------------------- #
class NewsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.category = Category.objects.create(name="Tech")
        self.new1 = New.objects.create(
            title="News 1",
            body="Body of News 1",
            photo="http://example.com/photo1.jpg",
            category=self.category,
            author=self.user,
            state=New.State.PUBLISHED
        )
        self.new2 = New.objects.create(
            title="News 2",
            body="Body of News 2",
            photo="http://example.com/photo2.jpg",
            category=self.category,
            author=self.user,
            state=New.State.PUBLISHED
        )
        self.url = reverse('news')

    def test_news_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_news_view_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('news', response.context)
        self.assertIn('categories', response.context)
        self.assertEqual(response.context['news'].count(), 2)

    def test_news_view_filter_by_category(self):
        response = self.client.get(self.url, {'category': 'Tech'})
        self.assertEqual(response.context['news'].count(), 2)

# --------------------------------------------------- Detalle de noticia --------------------------------------------------- #
class NewDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.category = Category.objects.create(name="Tech")
        self.new = New.objects.create(
            title="News Detail",
            body="Body of News Detail",
            photo="http://example.com/photo.jpg",
            category=self.category,
            author=self.user,
            state=New.State.PUBLISHED
        )
        self.url = reverse('new_detail', args=[self.new.id])

    def test_new_detail_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_new_detail_view_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('new', response.context)
        self.assertEqual(response.context['new'], self.new)

# --------------------------------------------------- Puntuación de odio --------------------------------------------------- #
class CalculateHateScoreTest(TestCase):
    def setUp(self):
        self.app_config = apps.get_app_config('ai_models')
        self.toxic_model = self.app_config.toxic_model
        self.toxic_vectorizer = self.app_config.toxic_vectorizer
        self.offensive_model = self.app_config.offensive_model
        self.offensive_vectorizer = self.app_config.offensive_vectorizer
        self.hate_model = self.app_config.hate_model
        self.hate_vectorizer = self.app_config.hate_vectorizer

    def test_calculate_hate_score(self):
        title = 'Qué injusticia'
        body = "La entrega de premios me ha parecido injusta. ¡Debería haber ganado Will Smith!"
        score = 2*calculate_hate_score(body) + calculate_hate_score(title)
        self.assertLessEqual(score, 2)

        title = 'Basura total'
        body = "ASCO de premios como ha podido ganar ese inutil?? no me lo puedo creer BASTA YA que basura de industria y que basura de premios"
        score = 2*calculate_hate_score(body) + calculate_hate_score(title)
        self.assertGreaterEqual(score, 7)

# --------------------------------------------------- Listado de noticias en borrador --------------------------------------------------- #
class ViewDraftNewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.writer_group = Group.objects.create(name='Writer')
        self.user.groups.add(self.writer_group)
        self.category = Category.objects.create(name="Tech")
        self.new = New.objects.create(
            title="Draft News",
            body="Body of Draft News",
            photo="http://example.com/photo.jpg",
            category=self.category,
            author=self.user,
            state=New.State.IN_DRAFT
        )
        self.url = reverse('draft_news')
        self.client.login(username='testuser', password='12345')

    def test_view_draft_news_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_draft_news_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('news', response.context)
        self.assertIn('categories', response.context)
        self.assertEqual(response.context['news'].count(), 1)
        self.assertEqual(response.context['news'].first(), self.new)

# --------------------------------------------------- Creación de noticias --------------------------------------------------- #
class CreateNewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.writer_group = Group.objects.create(name='Writer')
        self.user.groups.add(self.writer_group)
        self.category = Category.objects.create(name="Tech")
        self.publishUrl = reverse('publish_new')
        self.draftUrl = reverse('draft_new')
        self.client.login(username='testuser', password='12345')

    @patch('news.views.calculate_hate_score')
    def test_create_new_published(self, mock_calculate_hate_score):
        mock_calculate_hate_score.return_value = 0
        response = self.client.post(self.publishUrl, {
            'title': 'Good new',
            'body': 'Test Body',
            'photo': 'test.jpg',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 302)
        new = New.objects.get(title='Good new')
        self.assertEqual(new.state, New.State.PUBLISHED)
        self.assertEqual(new.hateScore, 0)

    @patch('news.views.calculate_hate_score')
    def test_create_new_in_review(self, mock_calculate_hate_score):
        mock_calculate_hate_score.return_value = 1
        response = self.client.post(self.publishUrl, {
            'title': 'Mild new',
            'body': 'Test Body',
            'photo': 'test.jpg',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 302)
        new = New.objects.get(title='Mild new')
        self.assertEqual(new.state, New.State.IN_REVIEW)
        self.assertEqual(new.hateScore, 3)

    @patch('news.views.calculate_hate_score')
    def test_create_new_forbidden(self, mock_calculate_hate_score):
        mock_calculate_hate_score.return_value = 3
        response = self.client.post(self.publishUrl, {
            'title': 'Bad new',
            'body': 'Test Body',
            'photo': 'test.jpg',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 302)
        new = New.objects.get(title='Bad new')
        self.assertEqual(new.state, New.State.FORBIDDEN)
        self.assertEqual(new.hateScore, 9)

    def test_create_new_draft(self):
        response = self.client.post(self.draftUrl, {
            'title': 'Draft new',
            'body': 'Test Body',
            'photo': 'test.jpg',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 302)
        new = New.objects.get(title='Draft new')
        self.assertEqual(new.body, 'Test Body')
        self.assertEqual(new.state, New.State.IN_DRAFT)

# --------------------------------------------------- Actualización de noticias --------------------------------------------------- #
class UpdateNewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.other_user = User.objects.create_user(username='otheruser', password='12345')
        self.admin_user = User.objects.create_superuser(username='adminuser', password='12345')
        self.writer_group = Group.objects.create(name='Writer')
        self.user.groups.add(self.writer_group)
        self.category = Category.objects.create(name="Tech")
        self.new = New.objects.create(
            title="Initial Title",
            body="Initial Body",
            photo="http://example.com/photo.jpg",
            category=self.category,
            author=self.user,
            state=New.State.IN_DRAFT
        )
        self.publishUrl = reverse('update_publish_new', args=[self.new.id])
        self.draftUrl = reverse('update_draft_new', args=[self.new.id])
        self.client.login(username='testuser', password='12345')

    def test_update_new_draft(self):
        response = self.client.post(self.draftUrl, {
            'title': 'Updated Title',
            'body': 'Updated Body',
            'photo': 'test.jpg',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 302)
        self.new.refresh_from_db()
        self.assertEqual(self.new.title, 'Updated Title')
        self.assertEqual(self.new.body, 'Updated Body')
        self.assertEqual(self.new.state, New.State.IN_DRAFT)

    def test_update_new_not_draft(self):
        self.new.state = New.State.PUBLISHED
        self.new.save()
        response = self.client.post(self.publishUrl, {
            'title': 'Updated Title',
            'body': 'Updated Body',
            'photo': 'test.jpg',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 403)

    def test_admin_update_new(self):
        self.client.login(username='adminuser', password='12345')
        response = self.client.post(self.draftUrl, {
            'title': 'Updated Title',
            'body': 'Updated Body',
            'photo': 'test.jpg',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 302)
        self.new.refresh_from_db()
        self.assertEqual(self.new.title, 'Updated Title')
        self.assertEqual(self.new.body, 'Updated Body')

    def test_update_new_other_user(self):
        self.client.login(username='otheruser', password='12345')
        response = self.client.post(self.draftUrl, {
            'title': 'Updated Title',
            'body': 'Updated Body',
            'photo': 'test.jpg',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 403)

# --------------------------------------------------- Eliminación de noticias --------------------------------------------------- #
class DeleteNewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.other_user = User.objects.create_user(username='otheruser', password='12345')
        self.admin_user = User.objects.create_superuser(username='adminuser', password='12345')
        self.writer_group = Group.objects.create(name='Writer')
        self.user.groups.add(self.writer_group)
        self.category = Category.objects.create(name="Tech")
        self.new = New.objects.create(
            title="News to be deleted",
            body="Body of News to be deleted",
            photo="http://example.com/photo.jpg",
            category=self.category,
            author=self.user,
            state=New.State.IN_DRAFT
        )
        self.url = reverse('delete_new', args=[self.new.id])
        self.client.login(username='testuser', password='12345')

    def test_delete_new_draft(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.new.refresh_from_db()
        self.assertEqual(self.new.state, New.State.DELETED)

    def test_delete_new_not_draft(self):
        self.new.state = New.State.PUBLISHED
        self.new.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_admin_delete_new(self):
        self.client.login(username='adminuser', password='12345')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.new.refresh_from_db()
        self.assertEqual(self.new.state, New.State.DELETED)

    def test_delete_new_other_user(self):
        self.client.login(username='otheruser', password='12345')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

# --------------------------------------------------- Listado de categorías --------------------------------------------------- #
class LoadCategoryDataTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.writer_group = Group.objects.create(name='Writer')
        self.user.groups.add(self.writer_group)
        self.category = Category.objects.create(name="Tech")
        self.url = reverse('category_load')
        self.client.login(username='testuser', password='12345')

    def test_category_load_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_category_load_content(self):
        response = self.client.get(self.url)
        categories_html = render_to_string('partials/category_list.html', {'categories': Category.objects.all()})
        self.assertJSONEqual(response.content, {'html': categories_html})

# --------------------------------------------------- Creación de categorías --------------------------------------------------- #
class CategoryCreateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.writer_group = Group.objects.create(name='Writer')
        self.user.groups.add(self.writer_group)
        self.url = reverse('category_create')
        self.client.login(username='testuser', password='12345')

    def test_category_create_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form_html = render_to_string('partials/category_form.html', {'form': CategoryForm(), 'is_creating': True})
        self.assertJSONEqual(response.content, {'html_form': form_html})

    def test_category_create_post_valid(self):
        response = self.client.post(self.url, {'name': 'New Category'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'form_is_valid': True, 'html_category_list': render_to_string('partials/category_list.html', {'categories': Category.objects.all()})})

    def test_category_create_post_invalid(self):
        response = self.client.post(self.url, {'name': ''})
        self.assertEqual(response.status_code, 200)
        form_html = render_to_string('partials/category_form.html', {'form': CategoryForm({'name': ''}), 'is_creating': True})
        self.assertJSONEqual(response.content, {'form_is_valid': False, 'is_creating': True, 'html_form': form_html})

# --------------------------------------------------- Actualización de categorías --------------------------------------------------- #
class CategoryUpdateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.writer_group = Group.objects.create(name='Writer')
        self.user.groups.add(self.writer_group)
        self.category = Category.objects.create(name="Tech")
        self.url = reverse('category_update', args=[self.category.id])
        self.client.login(username='testuser', password='12345')

    def test_category_update_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form_html = render_to_string('partials/category_form.html', {'form': CategoryForm(instance=self.category), 'is_creating': False})
        self.assertJSONEqual(response.content, {'html_form': form_html})

    def test_category_update_post_valid(self):
        response = self.client.post(self.url, {'name': 'Updated Category'})
        self.assertEqual(response.status_code, 200)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated Category')
        self.assertJSONEqual(response.content, {'form_is_valid': True})

    def test_category_update_post_invalid(self):
        response = self.client.post(self.url, {'name': ''})
        self.assertEqual(response.status_code, 200)
        form_html = render_to_string('partials/category_form.html', {'form': CategoryForm({'name': ''}), 'is_creating': False})
        self.assertJSONEqual(response.content, {'form_is_valid': False, 'is_creating': False, 'category_id': self.category.id, 'html_form': form_html})

# --------------------------------------------------- Eliminación de categorías --------------------------------------------------- #
class CategoryDeleteTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.writer_group = Group.objects.create(name='Writer')
        self.user.groups.add(self.writer_group)
        self.category = Category.objects.create(name="Tech")
        self.url = reverse('category_delete', args=[self.category.id])
        self.client.login(username='testuser', password='12345')

    def test_category_delete(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})
        with self.assertRaises(Category.DoesNotExist):
            Category.objects.get(id=self.category.id)
