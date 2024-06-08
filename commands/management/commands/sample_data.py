import os
import shutil
from datetime import datetime
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from movies.models import Movie, Genre, HomeImage, Gender, Actor, Performance, Review
from news.models import New, Category
from django.conf import settings
from djmoney.money import Money
from django.utils.timezone import make_aware

class Command(BaseCommand):
    help = 'Populate the database with initial data'

    def restore_images(self, backup_dir='backup_images'):
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                src_path = os.path.join(root, file)
                relative_path = os.path.relpath(src_path, backup_dir)
                dst_path = os.path.join(settings.MEDIA_ROOT, 'images', relative_path)
                if not os.path.exists(os.path.dirname(dst_path)):
                    os.makedirs(os.path.dirname(dst_path))
                shutil.copy(src_path, dst_path)

    def handle(self, *args, **kwargs):
        User.objects.all().delete()
        Group.objects.all().delete()
        Genre.objects.all().delete()
        Category.objects.all().delete()
        HomeImage.objects.all().delete()
        New.objects.all().delete()
        Actor.objects.all().delete()
        Movie.objects.all().delete()
        Performance.objects.all().delete()

        self.restore_images()

        texts_under_101_characters = ['Texto de prueba', 'Conestetextotratamosdeprobarellimitesuperiorde100caracteressssssssssssssssssssssssssssssssssssssssss', 'Conestetextotratamosdeprobarellimitesuperiorde99caracteressssssssssssssssssssssssssssssssssssssssss', 'A', 'Ab', '<h1>hola</h1>', '<script>alert("hola")</script>', '你好', 'Здравейте']
        texts_under_51_characters = ['Texto de prueba', 'Conestetextoprobamosellimitesuperiorde50caracteres', 'Conestetextprobamosellimitesuperiorde49caracteres', 'A', 'Ab', '<h1>hola</h1>', '<script>alert("hola")</script>', '你好', 'Здравейте']
        dates_before_today = [
            make_aware(datetime(2020, 4, 4)), 
            make_aware(datetime.now()), 
            make_aware(datetime.now() - relativedelta(seconds=1)), 
            make_aware(datetime(1888, 1, 1)), 
            make_aware(datetime(1888, 1, 1) + relativedelta(seconds=1))
        ]
        dates_before_2200 = [
            make_aware(datetime(2020, 4, 4)), 
            make_aware(datetime(2200, 1, 1)), 
            make_aware(datetime(2200, 1, 1) - relativedelta(seconds=1)), 
            make_aware(datetime(1888, 1, 1)), 
            make_aware(datetime(1888, 1, 1) + relativedelta(seconds=1))
        ]
        years_before_2200 = [2020, 2200, 2199, 1888, 1889]
        amounts_under_14_digits = [100.00, 999999999999.99, 999999999999.98, 0.00, 0.01]
        amounts_under_5_digits = [80.00, 999.99, 999.98, 0.00, 0.01]
        numbers_under_601 = [300, 600, 599, 1, 2]
        numbers_under_10001 = [300, 10000, 9999, 0, 1]

        # Users
        users = [
            {'username': 'administrator1', 'email': 'administrator1@example.com', 'password': 'administrator1', 'first_name': 'Admin', 'last_name': 'User', 'is_superuser': True, 'is_staff': True},
            {'username': 'writer1', 'email': 'writer1@example.com', 'password': 'writer1', 'first_name': 'Writer', 'last_name': 'User', 'is_superuser': False, 'is_staff': False},
            {'username': 'writer2', 'email': 'writer2@example.com', 'password': 'writer2', 'first_name': 'Writer', 'last_name': 'User', 'is_superuser': False, 'is_staff': False},
            {'username': 'authenticated1', 'email': 'authenticated1@example.com', 'password': 'authenticated1', 'first_name': 'Authenticated', 'last_name': 'User', 'is_superuser': False, 'is_staff': False},
            {'username': 'authenticated2', 'email': 'authenticated2@example.com', 'password': 'authenticated2', 'first_name': 'Authenticated', 'last_name': 'User', 'is_superuser': False, 'is_staff': False}
        ]

        created_users = {}
        for user_data in users:
            user, created = User.objects.get_or_create(username=user_data['username'], defaults=user_data)
            if created:
                user.set_password(user_data['password'])
                user.is_superuser = user_data['is_superuser']
                user.is_staff = user_data['is_staff']
                user.save()
            else:
                self.stdout.write(self.style.WARNING(f'User {user.username} already exists'))
            created_users[user_data['username']] = user

        # Groups
        groups = ['Writer']
        for group in groups:
            writer_group, created = Group.objects.get_or_create(name=group)

        created_users['writer1'].groups.add(writer_group)
        created_users['writer2'].groups.add(writer_group)

        # Genres
        for genre in texts_under_51_characters:
            Genre.objects.get_or_create(name=genre)

        # Categories
        for category in texts_under_51_characters:
            Category.objects.get_or_create(name=category)

        # Images
        images = [
            'images/1638571307676.jpg',
            'images/Conoce-a-los-actores-mejores-pagados-de-Hollywood-en-lo-que-va-del-2022.jpg'
        ]
        for image_url in images:
            HomeImage.objects.get_or_create(url=image_url)

        # News
        for text in texts_under_101_characters:
            New.objects.get_or_create(
                title=text,
                body='Texto de prueba',
                photo='images/chufo-llorens-desti-herois-destino-heroes-efe.jpeg',
                publicationDate=make_aware(datetime(2020, 4, 4)),
                category=Category.objects.get(name='Texto de prueba'),
                author=created_users['writer1'],
                state=New.State.PUBLISHED
            )
        for date in dates_before_today:
            New.objects.get_or_create(
                title='Texto de prueba',
                body='Texto de prueba',
                photo='images/chufo-llorens-desti-herois-destino-heroes-efe.jpeg',
                publicationDate=date,
                category=Category.objects.get(name='Texto de prueba'),
                author=created_users['writer1'],
                state=New.State.IN_DRAFT
            )

        # Actors
        for text in texts_under_101_characters:
            Actor.objects.get_or_create(
                name=text,
                gender=Gender.MAN,
                birthday=make_aware(datetime(2020, 4, 4)),
                nationality='Texto de prueba',
                principalImage='images/002_078f6fe5.jpg',
                height=1.80,
                weight=80.0,
                hair_color='Texto de prueba',
                eye_color='Texto de prueba'
            )
        for date in dates_before_today:
            Actor.objects.get_or_create(
                name='Texto de prueba',
                gender=Gender.MAN,
                birthday=date,
                nationality='Texto de prueba',
                principalImage='images/002_078f6fe5.jpg',
                height=1.80,
                weight=80.0,
                hair_color='Texto de prueba',
                eye_color='Texto de prueba'
            )
        for text in texts_under_101_characters:
            Actor.objects.get_or_create(
                name='Texto de prueba',
                gender=Gender.WOMAN,
                birthday=make_aware(datetime(2020, 4, 4)),
                nationality='Texto de prueba',
                principalImage='images/002_078f6fe5.jpg',
                height=1.80,
                weight=80.0,
                hair_color='Texto de prueba',
                eye_color='Texto de prueba'
            )
        for amount in amounts_under_5_digits:
            Actor.objects.get_or_create(
                name='Texto de prueba',
                gender=Gender.WOMAN,
                birthday=make_aware(datetime(2020, 4, 4)),
                nationality='Texto de prueba',
                principalImage='images/002_078f6fe5.jpg',
                height=amount,
                weight=80.0,
                hair_color='Texto de prueba',
                eye_color='Texto de prueba'
            )
        for amount in amounts_under_5_digits:
            Actor.objects.get_or_create(
                name='Texto de prueba',
                gender=Gender.WOMAN,
                birthday=make_aware(datetime(2020, 4, 4)),
                nationality='Texto de prueba',
                principalImage='images/002_078f6fe5.jpg',
                height=1.80,
                weight=amount,
                hair_color='Texto de prueba',
                eye_color='Texto de prueba'
            )
        for text in texts_under_51_characters:
            Actor.objects.get_or_create(
                name='Texto de prueba',
                gender=Gender.WOMAN,
                birthday=make_aware(datetime(2020, 4, 4)),
                nationality='Texto de prueba',
                principalImage='images/002_078f6fe5.jpg',
                height=1.80,
                weight=80.0,
                hair_color=text,
                eye_color='Texto de prueba'
            )
        for text in texts_under_51_characters:
            Actor.objects.get_or_create(
                name='Texto de prueba',
                gender=Gender.WOMAN,
                birthday=make_aware(datetime(2020, 4, 4)),
                nationality='Texto de prueba',
                principalImage='images/002_078f6fe5.jpg',
                height=1.80,
                weight=80.0,
                hair_color='Texto de prueba',
                eye_color=text
            )

        # Movies
        for text in texts_under_101_characters:
            movie, created = Movie.objects.get_or_create(
                title=text,
                director='Texto de prueba',
                releaseYear=2020,
                image='images/MV5BMjI3ODkzNDk5MF5BMl5BanBnXkFtZTgwNTEyNjY2NDM@._V1_FMjpg_UX1000_.jpg',
                duration=10,
                country='Texto de prueba',
                budget=Money(100000, 'EUR'),
                revenue=Money(150000, 'EUR')
            )
            if created:
                genre = Genre.objects.get(name='Texto de prueba')
                movie.genres.add(genre)
        for text in texts_under_101_characters:
            movie, created = Movie.objects.get_or_create(
                title='Texto de prueba',
                director=text,
                releaseYear=2020,
                image='images/MV5BMjI3ODkzNDk5MF5BMl5BanBnXkFtZTgwNTEyNjY2NDM@._V1_FMjpg_UX1000_.jpg',
                duration=10,
                country='Texto de prueba',
                budget=Money(100000, 'EUR'),
                revenue=Money(150000, 'EUR')
            )
            if created:
                genre = Genre.objects.get(name='Texto de prueba')
                movie.genres.add(genre)
        for year in years_before_2200:
            movie, created = Movie.objects.get_or_create(
                title='Texto de prueba',
                director='Texto de prueba',
                releaseYear=year,
                image='images/MV5BMjI3ODkzNDk5MF5BMl5BanBnXkFtZTgwNTEyNjY2NDM@._V1_FMjpg_UX1000_.jpg',
                duration=10,
                country='Texto de prueba',
                budget=Money(100000, 'EUR'),
                revenue=Money(150000, 'EUR')
            )
            if created:
                genre = Genre.objects.get(name='Texto de prueba')
                movie.genres.add(genre)
        for number in numbers_under_601:
            movie, created = Movie.objects.get_or_create(
                title='Texto de prueba',
                director='Texto de prueba',
                releaseYear=2020,
                image='images/MV5BMjI3ODkzNDk5MF5BMl5BanBnXkFtZTgwNTEyNjY2NDM@._V1_FMjpg_UX1000_.jpg',
                duration=number,
                country='Texto de prueba',
                budget=Money(100000, 'EUR'),
                revenue=Money(150000, 'EUR')
            )
            if created:
                genre = Genre.objects.get(name='Texto de prueba')
                movie.genres.add(genre)
        for text in texts_under_101_characters:
            movie, created = Movie.objects.get_or_create(
                title='Texto de prueba',
                director='Texto de prueba',
                releaseYear=2020,
                image='images/MV5BMjI3ODkzNDk5MF5BMl5BanBnXkFtZTgwNTEyNjY2NDM@._V1_FMjpg_UX1000_.jpg',
                duration=10,
                country=text,
                budget=Money(100000, 'EUR'),
                revenue=Money(150000, 'EUR')
            )
            if created:
                genre = Genre.objects.get(name='Texto de prueba')
                movie.genres.add(genre)
        for amount in amounts_under_14_digits:
            movie, created = Movie.objects.get_or_create(
                title='Texto de prueba',
                director='Texto de prueba',
                releaseYear=2020,
                image='images/MV5BMjI3ODkzNDk5MF5BMl5BanBnXkFtZTgwNTEyNjY2NDM@._V1_FMjpg_UX1000_.jpg',
                duration=10,
                country='Texto de prueba',
                budget=Money(amount, 'USD'),
                revenue=Money(150000, 'USD')
            )
            if created:
                genre = Genre.objects.get(name='Texto de prueba')
                movie.genres.add(genre)
        for amount in amounts_under_14_digits:
            movie, created = Movie.objects.get_or_create(
                title='Texto de prueba',
                director='Texto de prueba',
                releaseYear=2020,
                image='images/MV5BMjI3ODkzNDk5MF5BMl5BanBnXkFtZTgwNTEyNjY2NDM@._V1_FMjpg_UX1000_.jpg',
                duration=10,
                country='Texto de prueba',
                budget=Money(100000, 'USD'),
                revenue=Money(amount, 'USD')
            )
            if created:
                genre = Genre.objects.get(name='Texto de prueba')
                movie.genres.add(genre)

        # Performances
        for text in texts_under_101_characters:
            movie = Movie.objects.filter(title='Texto de prueba').first()
            actor = Actor.objects.filter(name='Texto de prueba').first()
            Performance.objects.get_or_create(
                movie=movie,
                actor=actor,
                characterName=text,
                screenTime=300
            )
        for number in numbers_under_10001:
            movie = Movie.objects.filter(title='Texto de prueba').first()
            actor = Actor.objects.filter(name='Texto de prueba').first()
            Performance.objects.get_or_create(
                movie=movie,
                actor=actor,
                characterName='Texto de prueba',
                screenTime=number
            )

        # Reviews
        for i in range(1, 6):
            user = User.objects.get(username='authenticated1')
            movie = Movie.objects.filter(title='Texto de prueba').first()
            Review.objects.get_or_create(
                body='Texto de prueba',
                rating=i,
                publicationDate=make_aware(datetime(2020, 4, 4)),
                hateScore=0,
                state=Review.State.PUBLISHED,
                user=user,
                movie=movie
            )
        for date in dates_before_2200:
            user = User.objects.get(username='authenticated1')
            movie = Movie.objects.filter(title='Texto de prueba').first()
            Review.objects.get_or_create(
                body='Texto de prueba',
                rating=3,
                publicationDate=date,
                hateScore=0,
                state=Review.State.PUBLISHED,
                user=user,
                movie=movie
            )

        self.stdout.write(self.style.SUCCESS('Database populated successfully'))
