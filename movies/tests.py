from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.apps import apps
from djmoney.money import Money
from movies.models import Review, Image, Movie, Genre, Actor, Gender, Performance
from django.utils import timezone
from news.models import New, Category
from unittest.mock import patch
from movies.views import calculate_hate_score

class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('home')

        # Crear usuario de prueba
        self.user = User.objects.create_user(username='testuser', password='12345')

        # Crear categoría de prueba
        self.category = Category.objects.create(name='Test Category')

        # Crear datos de prueba
        self.new = New.objects.create(
            title="Test News", 
            body="This is a test news", 
            publicationDate="2023-01-01T00:00:00Z", 
            author=self.user,
            category=self.category,
            photo="http://example.com/photo.jpg"
        )

        self.movie = Movie.objects.create(
            title="Test Movie",
            director="Director 1",
            releaseYear=2023,
            image="http://example.com/movie_image.jpg",
            duration=120,
            country="Country 1",
            budget=Money(100000, 'USD'),
            revenue=Money(150000, 'USD'),
        )
        self.review1 = Review.objects.create(
            movie=self.movie, 
            user=self.user, 
            body="Review 1", 
            rating=5, 
            publicationDate="2023-01-01"
        )
        self.review2 = Review.objects.create(
            movie=self.movie, 
            user=self.user, 
            body="Review 2", 
            rating=4, 
            publicationDate="2023-01-02"
        )
        self.image = Image.objects.create(url="http://example.com/image.jpg")

    def test_home_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_home_view_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('latest_new', response.context)
        self.assertIn('latest_reviews', response.context)
        self.assertIn('carousel_images', response.context)
        self.assertEqual(len(response.context['latest_reviews']), 2)
        self.assertEqual(len(response.context['carousel_images']), 1)

class MoviesViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('movies')

        # Crear usuario de prueba
        self.user = User.objects.create_user(username='testuser', password='12345')

        # Crear datos de prueba
        self.genre = Genre.objects.create(name="Action")
        self.movie1 = Movie.objects.create(
            title="Movie 1",
            director="Director 1",
            releaseYear=2023,
            image="http://example.com/image1.jpg",
            duration=120,
            country="Country 1",
            budget=Money(100000, 'USD'),
            revenue=Money(150000, 'USD'),
        )
        self.movie1.genres.add(self.genre)

        self.movie2 = Movie.objects.create(
            title="Movie 2",
            director="Director 2",
            releaseYear=2023,
            image="http://example.com/image2.jpg",
            duration=100,
            country="Country 2",
            budget=Money(200000, 'USD'),
            revenue=Money(250000, 'USD'),
        )

    def test_movies_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_movies_view_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('movies', response.context)
        self.assertIn('genres', response.context)
        self.assertEqual(response.context['movies'].count(), 2)

    def test_movies_view_filter_by_genre(self):
        response = self.client.get(self.url, {'genre': 'Action'})
        self.assertEqual(response.context['movies'].count(), 1)
        self.assertEqual(response.context['movies'].first(), self.movie1)

    def test_movies_view_filter_by_director(self):
        response = self.client.get(self.url, {'director': 'Director 2'})
        self.assertEqual(response.context['movies'].count(), 1)
        self.assertEqual(response.context['movies'].first(), self.movie2)

class MovieDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')

        self.movie = Movie.objects.create(
            title="Movie Detail",
            director="Director Detail",
            releaseYear=2023,
            image="http://example.com/movie_detail_image.jpg",
            duration=110,
            country="Country Detail",
            budget=Money(300000, 'USD'),
            revenue=Money(400000, 'USD'),
        )
        self.url = reverse('movie_detail', args=[self.movie.id])

        self.review1 = Review.objects.create(
            movie=self.movie, 
            user=self.user, 
            body="Review 1", 
            rating=5, 
            state=Review.State.PUBLISHED,
            publicationDate="2023-01-01"
        )
        self.review2 = Review.objects.create(
            movie=self.movie, 
            user=self.user, 
            body="Review 2", 
            rating=4, 
            state=Review.State.PUBLISHED,
            publicationDate="2023-01-02"
        )

    def test_movie_detail_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_movie_detail_view_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('movie', response.context)
        self.assertIn('average_rating', response.context)
        self.assertIn('rating_range', response.context)
        self.assertIn('number_of_reviews', response.context)
        self.assertIn('last_review', response.context)
        self.assertEqual(response.context['movie'], self.movie)
        self.assertEqual(response.context['average_rating'], 4.5)
        self.assertEqual(response.context['number_of_reviews'](), 2)
        self.assertEqual(response.context['last_review'], self.review2)

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
        body = "No me ha gustado la peli"
        score = calculate_hate_score(body)
        self.assertLessEqual(score, 1)

        body = "basura de peli, espantosa, lo PEOR!"
        score = calculate_hate_score(body)
        self.assertGreaterEqual(score, 2)

class MovieReviewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.movie = Movie.objects.create(
            title="Test Movie",
            director="Director 1",
            releaseYear=2023,
            image="http://example.com/movie_image.jpg",
            duration=120,
            country="Country 1",
            budget=Money(100000, 'USD'),
            revenue=Money(150000, 'USD'),
        )
        self.review1 = Review.objects.create(
            movie=self.movie, 
            user=self.user, 
            body="Good review", 
            rating=5, 
            state=Review.State.PUBLISHED,
            publicationDate=timezone.now()
        )
        self.review2 = Review.objects.create(
            movie=self.movie, 
            user=self.user, 
            body="Bad review", 
            rating=1, 
            state=Review.State.PUBLISHED,
            publicationDate=timezone.now()
        )
        self.url = reverse('movie_reviews', args=[self.movie.id])

    def test_movie_reviews_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_movie_reviews_view_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('movie', response.context)
        self.assertIn('reviews', response.context)
        self.assertIn('average_rating', response.context)
        self.assertEqual(response.context['movie'], self.movie)
        self.assertEqual(response.context['average_rating'], 3)

    def test_movie_reviews_view_filter_by_rating(self):
        response = self.client.get(self.url, {'rating': 5})
        self.assertEqual(response.context['reviews'].count(), 1)
        self.assertEqual(response.context['reviews'].first(), self.review1)

class ViewDraftReviewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.movie = Movie.objects.create(
            title="Test Movie",
            director="Director 1",
            releaseYear=2023,
            image="http://example.com/movie_image.jpg",
            duration=120,
            country="Country 1",
            budget=Money(100000, 'USD'),
            revenue=Money(150000, 'USD'),
        )
        self.draft_review = Review.objects.create(
            movie=self.movie, 
            user=self.user, 
            body="Draft review", 
            rating=3, 
            state=Review.State.IN_DRAFT
        )
        self.url = reverse('draft_reviews')
        self.client.login(username='testuser', password='12345')

    def test_view_draft_reviews_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_draft_reviews_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('reviews', response.context)
        self.assertIn('show_drafts', response.context)
        self.assertEqual(response.context['reviews'].count(), 1)
        self.assertEqual(response.context['reviews'].first(), self.draft_review)

class CreateReviewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.movie = Movie.objects.create(
            title="Test Movie",
            director="Director 1",
            releaseYear=2023,
            image="http://example.com/movie_image.jpg",
            duration=120,
            country="Country 1",
            budget=Money(100000, 'USD'),
            revenue=Money(150000, 'USD'),
        )
        self.publishUrl = reverse('publish_review', args=[self.movie.id])
        self.draftUrl = reverse('save_draft', args=[self.movie.id])
        self.client.login(username='testuser', password='12345')

    @patch('movies.views.calculate_hate_score')
    def test_create_review_published(self, mock_calculate_hate_score):
        mock_calculate_hate_score.return_value = 0
        response = self.client.post(self.publishUrl, {'body': 'Good review', 'rating': 5})
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get(movie=self.movie)
        self.assertEqual(review.state, Review.State.PUBLISHED)
        self.assertEqual(review.hateScore, 0)

    @patch('movies.views.calculate_hate_score')
    def test_create_review_in_review(self, mock_calculate_hate_score):
        mock_calculate_hate_score.return_value = 2
        response = self.client.post(self.publishUrl, {'body': 'Mild review', 'rating': 3})
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get(movie=self.movie)
        self.assertEqual(review.state, Review.State.IN_REVIEW)
        self.assertEqual(review.hateScore, 2)

    @patch('movies.views.calculate_hate_score')
    def test_create_review_forbidden(self, mock_calculate_hate_score):
        mock_calculate_hate_score.return_value = 3
        response = self.client.post(self.publishUrl, {'body': 'Bad review', 'rating': 1})
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get(movie=self.movie)
        self.assertEqual(review.state, Review.State.FORBIDDEN)
        self.assertEqual(review.hateScore, 3)

    def test_create_review_draft(self):
        response = self.client.post(self.draftUrl, {'body': 'Draft review', 'rating': 3})
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get(movie=self.movie)
        self.assertEqual(review.body, 'Draft review')
        self.assertEqual(review.state, Review.State.IN_DRAFT)

class UpdateReviewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.other_user = User.objects.create_user(username='otheruser', password='12345')
        self.admin_user = User.objects.create_superuser(username='adminuser', password='12345')
        self.movie = Movie.objects.create(
            title="Test Movie",
            director="Director 1",
            releaseYear=2023,
            image="http://example.com/movie_image.jpg",
            duration=120,
            country="Country 1",
            budget=Money(100000, 'USD'),
            revenue=Money(150000, 'USD'),
        )
        self.review = Review.objects.create(
            movie=self.movie, 
            user=self.user, 
            body="Initial draft review", 
            rating=5, 
            state=Review.State.IN_DRAFT,
            publicationDate=timezone.now()
        )
        self.publishUrl = reverse('update_publish_review', args=[self.review.id])
        self.draftUrl = reverse('update_draft_review', args=[self.review.id])
        self.client.login(username='testuser', password='12345')

    def test_update_review_draft(self):
        response = self.client.post(self.draftUrl, {'body': 'Updated draft review', 'rating': 4})
        self.assertEqual(response.status_code, 302)
        self.review.refresh_from_db()
        self.assertEqual(self.review.body, 'Updated draft review')
        self.assertEqual(self.review.state, Review.State.IN_DRAFT)

    def test_update_review_not_draft(self):
        self.review.state = Review.State.PUBLISHED
        self.review.save()
        response = self.client.post(self.publishUrl, {'body': 'Attempt to update published review', 'rating': 3})
        self.assertEqual(response.status_code, 403)

    def test_admin_update_review(self):
        self.client.login(username='adminuser', password='12345')
        response = self.client.post(self.publishUrl, {'body': 'Admin updated review', 'rating': 5})
        self.assertEqual(response.status_code, 302)
        self.review.refresh_from_db()
        self.assertEqual(self.review.body, 'Admin updated review')

    def test_update_review_other_user(self):
        self.client.login(username='otheruser', password='12345')
        response = self.client.post(self.draftUrl, {'body': 'Other user trying to update review', 'rating': 3})
        self.assertEqual(response.status_code, 403)

class DeleteReviewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.other_user = User.objects.create_user(username='otheruser', password='12345')
        self.admin_user = User.objects.create_superuser(username='adminuser', password='12345')
        self.movie = Movie.objects.create(
            title="Test Movie",
            director="Director 1",
            releaseYear=2023,
            image="http://example.com/movie_image.jpg",
            duration=120,
            country="Country 1",
            budget=Money(100000, 'USD'),
            revenue=Money(150000, 'USD'),
        )
        self.review = Review.objects.create(
            movie=self.movie, 
            user=self.user, 
            body="Review to be deleted", 
            rating=5, 
            state=Review.State.IN_DRAFT
        )
        self.url = reverse('delete_review', args=[self.review.id])
        self.client.login(username='testuser', password='12345')

    def test_delete_review_draft(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.review.refresh_from_db()
        self.assertEqual(self.review.state, Review.State.DELETED)

    def test_delete_review_not_draft(self):
        self.review.state = Review.State.PUBLISHED
        self.review.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_admin_delete_review(self):
        self.client.login(username='adminuser', password='12345')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.review.refresh_from_db()
        self.assertEqual(self.review.state, Review.State.DELETED)

    def test_delete_review_other_user(self):
        self.client.login(username='otheruser', password='12345')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

class ActorsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.actor1 = Actor.objects.create(
            name="Actor 1",
            gender=Gender.MAN,
            birthday=timezone.now().date(),
            nationality="Nationality 1",
            principalImage="http://example.com/actor1.jpg",
            height=180,
            weight=75,
            hair_color="Brown",
            eye_color="Blue"
        )
        self.actor2 = Actor.objects.create(
            name="Actor 2",
            gender=Gender.WOMAN,
            birthday=timezone.now().date(),
            nationality="Nationality 2",
            principalImage="http://example.com/actor2.jpg",
            height=170,
            weight=65,
            hair_color="Black",
            eye_color="Green"
        )
        self.url = reverse('actors')

    def test_actors_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_actors_view_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('actors', response.context)
        self.assertIn('genders', response.context)
        self.assertEqual(response.context['actors'].count(), 2)

    def test_actors_view_filter_by_name(self):
        response = self.client.get(self.url, {'name': 'Actor 1'})
        self.assertEqual(response.context['actors'].count(), 1)
        self.assertEqual(response.context['actors'].first(), self.actor1)

    def test_actors_view_filter_by_gender(self):
        response = self.client.get(self.url, {'gender': Gender.WOMAN})
        self.assertEqual(response.context['actors'].count(), 1)
        self.assertEqual(response.context['actors'].first(), self.actor2)

class ActorDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear película para la performance
        self.movie = Movie.objects.create(
            title="Test Movie",
            director="Director 1",
            releaseYear=2023,
            image="http://example.com/movie_image.jpg",
            duration=120,
            country="Country 1",
            budget=Money(100000, 'USD'),
            revenue=Money(150000, 'USD'),
        )

        self.actor = Actor.objects.create(
            name="Actor Detail",
            gender=Gender.MAN,
            birthday=timezone.now().date(),
            nationality="Nationality Detail",
            principalImage="http://example.com/actor_detail.jpg",
            height=180,
            weight=75,
            hair_color="Brown",
            eye_color="Blue"
        )
        self.performance = Performance.objects.create(
            actor=self.actor,
            movie=self.movie,
            characterName="Main Role",
            screenTime=90.5
        )
        self.url = reverse('actor_detail', args=[self.actor.id])

    def test_actor_detail_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_actor_detail_view_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('actor', response.context)
        self.assertIn('performances', response.context)
        self.assertEqual(response.context['actor'], self.actor)
        self.assertEqual(response.context['performances'].count(), 1)
        self.assertEqual(response.context['performances'].first(), self.performance)
