from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.contrib.auth.models import User
from django.apps import apps
from djmoney.money import Money
from movies.models import Review, HomeImage, Movie, Genre, Actor, Gender, Performance
from movies.utils import (
    check_files_exist,
    detect_faces,
    calculate_frame_statistics
)
from django.utils import timezone
from news.models import New, Category
from unittest.mock import patch
from movies.views import calculate_hate_score
from datetime import date
import numpy as np
import cv2
import os

class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('home')
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.category = Category.objects.create(name='Test Category')
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
            state=Review.State.PUBLISHED,
            rating=5, 
            publicationDate="2023-01-01"
        )
        self.review2 = Review.objects.create(
            movie=self.movie, 
            user=self.user, 
            body="Review 2",
            state=Review.State.PUBLISHED,
            rating=4, 
            publicationDate="2023-01-02"
        )
        self.image = HomeImage.objects.create(url="http://example.com/image.jpg")

    def tearDown(self):
        Movie.objects.all().delete()

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
        
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.genre = Genre.objects.create(name="Action")
        self.movie1 = Movie.objects.create(
            title="Movie 1",
            director="Director 1",
            releaseYear=2023,
            image="http://example.com/movie_image.jpg",
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
            image="http://example.com/movie_image.jpg",
            duration=100,
            country="Country 2",
            budget=Money(200000, 'USD'),
            revenue=Money(250000, 'USD'),
        )

    def tearDown(self):
        Movie.objects.all().delete()

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
            title="Test Movie",
            director="Director Detail",
            releaseYear=2023,
            image="http://example.com/movie_image.jpg",
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

    def tearDown(self):
        Movie.objects.all().delete()

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

    def tearDown(self):
        Movie.objects.all().delete()

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

    def tearDown(self):
        Movie.objects.all().delete()

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

    def tearDown(self):
        Movie.objects.all().delete()

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

    def tearDown(self):
        Movie.objects.all().delete()

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

    def tearDown(self):
        Movie.objects.all().delete()

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

class PerformancePostSaveTest(TestCase):

    def setUp(self):
        self.check_files_exist_patcher = patch('movies.signals.check_files_exist')
        self.load_joblib_patcher = patch('movies.signals.load_joblib')
        self.load_yolo_model_patcher = patch('movies.signals.load_yolo_model')
        self.calculate_frame_statistics_patcher = patch('movies.signals.calculate_frame_statistics')
        self.update_performance_instance_patcher = patch('movies.signals.update_performance_instance')

        self.mock_check_files_exist = self.check_files_exist_patcher.start()
        self.mock_load_joblib = self.load_joblib_patcher.start()
        self.mock_load_yolo_model = self.load_yolo_model_patcher.start()
        self.mock_calculate_frame_statistics = self.calculate_frame_statistics_patcher.start()
        self.mock_update_performance_instance = self.update_performance_instance_patcher.start()

        self.mock_load_yolo_model.return_value = (MagicMock(), ['face'], ['layer1', 'layer2'])

        self.actor1 = Actor.objects.create(
            name="Will Smith",
            gender="Male",
            birthday=date(1990, 1, 1),
            nationality="Test Nationality",
            principalImage="path/to/image.jpg",
            height=180.0,
            weight=75.0,
            hair_color="Brown",
            eye_color="Blue"
        )
        self.actor2 = Actor.objects.create(
            name="Macaulay Culkin",
            gender="Male",
            birthday=date(1990, 1, 1),
            nationality="Test Nationality",
            principalImage="path/to/image.jpg",
            height=180.0,
            weight=75.0,
            hair_color="Brown",
            eye_color="Blue"
        )
        self.movie = Movie.objects.create(
            title="Test Movie",
            director="Test Director",
            releaseYear=2023,
            image="path/to/movie_image.jpg",
            duration=120,
            country="Test Country",
            budget=100000,
            revenue=150000
        )
        self.performance1 = Performance.objects.create(
            actor=self.actor1,
            movie=self.movie,
            screenTime=None
        )
        self.performance2 = Performance.objects.create(
            actor=self.actor2,
            movie=self.movie,
            screenTime=None
        )

    def tearDown(self):
        Movie.objects.all().delete()
        patch.stopall()

    def reset_mocks(self):
        self.mock_check_files_exist.reset_mock()
        self.mock_load_joblib.reset_mock()
        self.mock_load_yolo_model.reset_mock()
        self.mock_calculate_frame_statistics.reset_mock()
        self.mock_update_performance_instance.reset_mock()

    def test_performance_post_save_without_screenTime_and_with_valid_actor(self):
        self.reset_mocks()
        self.performance1.screenTime = None
        self.performance1.save()
        self.mock_check_files_exist.assert_called()
        self.mock_load_joblib.assert_called()
        self.mock_load_yolo_model.assert_called()
        self.mock_calculate_frame_statistics.assert_called()
        self.mock_update_performance_instance.assert_called()

    def test_performance_post_save_without_screenTime_and_with_invalid_actor(self):
        self.reset_mocks()
        self.performance2.screenTime = None
        self.performance2.save()
        self.mock_check_files_exist.assert_not_called()
        self.mock_load_joblib.assert_not_called()
        self.mock_load_yolo_model.assert_not_called()
        self.mock_calculate_frame_statistics.assert_not_called()
        self.mock_update_performance_instance.assert_not_called()

    def test_performance_post_save_with_screenTime(self):
        self.reset_mocks()
        self.performance1.screenTime = 50
        self.performance1.save()
        self.mock_check_files_exist.assert_not_called()
        self.mock_load_joblib.assert_not_called()
        self.mock_load_yolo_model.assert_not_called()
        self.mock_calculate_frame_statistics.assert_not_called()
        self.mock_update_performance_instance.assert_not_called()

class UtilsTestCase(TestCase):

    def setUp(self):
        self.files = ['file1.jpg', 'file2.jpg']
        for file in self.files:
            open(file, 'a').close()

        self.image = np.zeros((416, 416, 3), dtype=np.uint8)
        self.net = MagicMock()
        self.output_layers = ['layer1', 'layer2']

        self.frame_files = ['frame1.jpg', 'frame2.jpg']
        self.frames_dir = '.'
        for file in self.frame_files:
            cv2.imwrite(file, np.zeros((416, 416, 3), dtype=np.uint8))
        self.actor_model = MagicMock()
        self.happy_model = MagicMock()
        self.sad_model = MagicMock()
        self.angry_model = MagicMock()
        self.face_net = MagicMock()
        self.face_output_layers = ['layer1', 'layer2']

    def tearDown(self):
        for file in self.files:
            if os.path.exists(file):
                os.remove(file)

            for file in self.frame_files:
                if os.path.exists(file):
                    os.remove(file)

    @patch('os.path.exists', return_value=True)
    def test_all_files_exist(self, mock_exists):
        check_files_exist(self.files)
        mock_exists.assert_any_call('file1.jpg')
        mock_exists.assert_any_call('file2.jpg')

    @patch('os.path.exists', side_effect=[True, False])
    def test_some_files_missing(self, mock_exists):
        with self.assertRaises(FileNotFoundError):
            check_files_exist(self.files)

    @patch('cv2.dnn.blobFromImage')
    def test_detect_faces(self, mock_blobFromImage):
        mock_blobFromImage.return_value = MagicMock()
        self.net.forward.return_value = [
            np.array([[
                0.5, 0.5, 0.1, 0.1, 0, 0.9
            ]])
        ]
        faces = detect_faces(self.image, self.net, self.output_layers, threshold=0.7)
        self.assertIsInstance(faces, list)
        self.assertGreaterEqual(len(faces), 1)

    @patch('cv2.imread', return_value=np.zeros((416, 416, 3), dtype=np.uint8))
    @patch('movies.utils.detect_faces', return_value=[((0, 0, 50, 50), 0.9)])
    @patch('movies.utils.preprocess_face_for_actor_model', return_value=np.zeros((1, 100, 100, 1)))
    @patch('movies.utils.preprocess_face_for_emotion_model', return_value=np.zeros((1, 48, 48, 1)))
    def test_calculate_frame_statistics(self, mock_preprocess_face_for_emotion_model, mock_preprocess_face_for_actor_model, mock_detect_faces, mock_imread):
        self.actor_model.predict.return_value = 0.8
        self.happy_model.predict.return_value = 0.8
        self.sad_model.predict.return_value = 0.9
        self.angry_model.predict.return_value = 0.8

        statistics = calculate_frame_statistics(self.frame_files, self.frames_dir, self.actor_model, self.happy_model, self.sad_model, self.angry_model, self.face_net, self.face_output_layers)
        
        self.assertEqual(statistics['total_frames'], 2)
        self.assertEqual(statistics['actor_frame_count'], 2)
        self.assertEqual(statistics['happy_frame_count'], 2)
        self.assertEqual(statistics['angry_frame_count'], 2)
        self.assertEqual(statistics['sadness_frame_count'], 2)
    