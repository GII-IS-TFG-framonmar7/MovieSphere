import os
import shutil
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from movies.models import Movie, Genre, Image, Gender, Actor, Performance, Review
from news.models import New, Category
from django.conf import settings
from djmoney.money import Money

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
        Image.objects.all().delete()
        New.objects.all().delete()
        Actor.objects.all().delete()
        Movie.objects.all().delete()
        Performance.objects.all().delete()

        self.restore_images()

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
        genres = ['Drama', 'Comedia', 'Aventura', 'Terror', 'Ciencia Ficción', 'Musical']
        for genre in genres:
            Genre.objects.get_or_create(name=genre)

        # Categories
        categories = ['Estrenos', 'Entrevistas', 'Premios', 'Rumores']
        for category in categories:
            Category.objects.get_or_create(name=category)

        # Images
        images = [
            'images/1638571307676.jpg',
            'images/Conoce-a-los-actores-mejores-pagados-de-Hollywood-en-lo-que-va-del-2022.jpg'
        ]
        for image_url in images:
            Image.objects.get_or_create(url=image_url)

        # News
        news = [
            {
                'title': "El esperado estreno de 'El Destino de los Héroes' arrasa en taquilla",
                'body': (
                    "La nueva película de acción y aventuras 'El Destino de los Héroes' ha roto récords de taquilla en su primer fin de semana, recaudando 150 millones de dólares a nivel mundial.\n"
                    "Dirigida por el aclamado cineasta John Matthews, la película sigue la historia de un grupo de héroes que deben unirse para salvar al mundo de una antigua amenaza.\n"
                    "Con un elenco estelar que incluye a Emma Stone, Chris Hemsworth y Idris Elba, 'El Destino de los Héroes' ha sido elogiada por su impresionante cinematografía, efectos visuales y emocionantes secuencias de acción.\n"
                    "Los críticos y fanáticos coinciden en que esta película es una de las mejores del año, destacando su narrativa emocionante y actuaciones excepcionales.\n"
                    "Sin duda, 'El Destino de los Héroes' se perfila como un fuerte contendiente para la temporada de premios."
                ),
                'photo': 'images/chufo-llorens-desti-herois-destino-heroes-efe.jpeg',
                'publicationDate': timezone.now(),
                'category': Category.objects.get(name='Estrenos'),
                'author': created_users['writer1'],
                'state': New.State.PUBLISHED
            },
            {
                'title': "Entrevista exclusiva con Sofia Coppola: 'Siempre busco contar historias auténticas'",
                'body': (
                    "En una entrevista exclusiva con nuestra revista, la renombrada directora Sofia Coppola nos habla sobre su último proyecto, 'Las luces de Tokio', una conmovedora historia que explora la vida de una joven expatriada en Japón.\n"
                    "Coppola, conocida por su estilo visual distintivo y narrativas introspectivas, comparte cómo su propia experiencia de vida influye en su trabajo.\n"
                    "'Siempre busco contar historias auténticas que resuenen con la audiencia', comenta Coppola.\n"
                    "'Las luces de Tokio' no es una excepción; es una película que captura la belleza y la soledad de la vida en una ciudad extranjera.\n"
                    "La directora también nos revela detalles sobre el proceso de filmación en locaciones icónicas de Tokio y su colaboración con el talentoso elenco, encabezado por Elle Fanning y Ken Watanabe.\n"
                    "La película ha recibido críticas positivas por su sensibilidad y profundidad emocional, consolidando a Coppola como una de las voces más originales del cine contemporáneo."
                ),
                'photo': 'images/Sofia-coppola-1.jpg',
                'publicationDate': timezone.now(),
                'category': Category.objects.get(name='Entrevistas'),
                'author': created_users['writer1'],
                'state': New.State.PUBLISHED
            },
            {
                'title': "La Academia anuncia los nominados a los Premios Oscar 2024: 'Caminos Cruzados' lidera con 12 nominaciones",
                'body': (
                    "La Academia de Artes y Ciencias Cinematográficas ha anunciado hoy los nominados a los Premios Oscar 2024, y la película 'Caminos Cruzados' ha emergido como la gran favorita con 12 nominaciones, incluyendo Mejor Película, Mejor Director para Martin Scorsese, y Mejor Actor para Leonardo DiCaprio.\n"
                    "Este drama épico, que narra las vidas entrelazadas de varias personas a lo largo de tres décadas, ha sido elogiado por su compleja narrativa y actuaciones magistrales.\n"
                    "Otras películas destacadas en la lista de nominaciones incluyen 'La revolución de los robots', una innovadora película de ciencia ficción con 9 nominaciones, y 'La melodía del corazón', una conmovedora historia musical que ha obtenido 7 nominaciones.\n"
                    "La ceremonia de los Oscar, que se llevará a cabo el próximo 25 de febrero, promete ser una noche inolvidable, celebrando lo mejor del cine mundial.\n"
                    "Los fanáticos ya están ansiosos por ver quiénes se llevarán a casa las codiciadas estatuillas doradas."
                ),
                'photo': 'images/ganadores-premios-oscar-2024-65ee7f8605f59.jpg',
                'publicationDate': timezone.now(),
                'category': Category.objects.get(name='Premios'),
                'author': created_users['writer2'],
                'state': New.State.PUBLISHED
            }
        ]
        for news_item in news:
            New.objects.get_or_create(
                title=news_item['title'],
                body=news_item['body'],
                photo=news_item['photo'],
                publicationDate=news_item['publicationDate'],
                category=news_item['category'],
                author=news_item['author'],
                state=news_item['state']
            )

        # Actors
        actors = [
            {
                'name': "Will Smith",
                'gender': Gender.MAN,
                'birthday': "1968-10-25",
                'nationality': 'Estadounidense',
                'principalImage': 'images/002_078f6fe5.jpg',
                'height': 1.88,
                'weight': 82.0,
                'hair_color': 'Negro',
                'eye_color': 'Marrón'
            },
            {
                'name': "Michael Carlyle Hall",
                'gender': Gender.MAN,
                'birthday': "1971-02-01",
                'nationality': 'Estadounidense',
                'principalImage': 'images/181107-teeman-michael-c-hall-tease_moezke.jpg',
                'height': 1.77,
                'weight': 80.0,
                'hair_color': 'Castaño',
                'eye_color': 'Verde'
            },
            {
                'name': "Ian McKellen",
                'gender': Gender.MAN,
                'birthday': "1939-05-25",
                'nationality': 'Británica',
                'principalImage': 'images/SDCC13_-_Ian_McKellen_ZcpUBfs_0KFHrV1.jpg',
                'height': 1.80,
                'weight': 78.0,
                'hair_color': 'Gris',
                'eye_color': 'Azul'
            }
        ]
        for actor in actors:
            Actor.objects.get_or_create(
                name=actor['name'],
                gender=actor['gender'],
                birthday=actor['birthday'],
                nationality=actor['nationality'],
                principalImage=actor['principalImage'],
                height=actor['height'],
                weight=actor['weight'],
                hair_color=actor['hair_color'],
                eye_color=actor['eye_color'],
            )

        # Movies
        genres_map = {genre.name: genre for genre in Genre.objects.all()}
        movies = [
            {
                'title': "Noche de juegos",
                'director': "John Francis Daley",
                'releaseYear': 2018,
                'image': 'images/MV5BMjI3ODkzNDk5MF5BMl5BanBnXkFtZTgwNTEyNjY2NDM@._V1_FMjpg_UX1000_.jpg',
                'duration': 100,
                'country': "Estados Unidos",
                'budget': Money(37000000, 'USD'),
                'revenue': Money(117700000, 'USD'),
                'genres': ['Comedia']
            },
            {
                'title': "El señor de los anillos",
                'director': "Peter Jackson",
                'releaseYear': 2001,
                'image': 'images/El_seanor_de_los_anillos_La_comunidad_del_anillo-744631610-large.jpg',
                'duration': 178,
                'country': "Nueva Zelanda",
                'budget': Money(93000000, 'USD'),
                'revenue': Money(871530324, 'USD'),
                'genres': ["Aventura", "Fantasía"]
            },
            {
                'title': "Bad Boys: Ride Or Die",
                'director': "Adil El Arbi, Bilall Fallah",
                'releaseYear': 2024,
                'image': 'images/maxresdefault.jpg',
                'duration': 3,
                'country': "Estados Unidos",
                'budget': Money(90000000, 'USD'),
                'revenue': Money(0, 'USD'),
                'genres': ["Acción", "Comedia"]
            }
        ]
        for movie_data in movies:
            movie, created = Movie.objects.get_or_create(
                title=movie_data['title'],
                director=movie_data['director'],
                releaseYear=movie_data['releaseYear'],
                image=movie_data['image'],
                duration=movie_data['duration'],
                country=movie_data['country'],
                budget=movie_data['budget'],
                revenue=movie_data['revenue']
            )
            if created:
                for genre_name in movie_data['genres']:
                    genre = genres_map.get(genre_name)
                    if genre:
                        movie.genres.add(genre)

        # Performances
        performances = [
            {
                'movie': "Bad Boys: Ride Or Die",
                'actor': "Will Smith",
                'characterName': 'Michael Eugene "Mike" Lowrey',
                'screenTime': 66
            },
            {
                'movie': "El señor de los anillos",
                'actor': "Ian McKellen",
                'characterName': 'Gandalf',
                'screenTime': 4260
            },
            {
                'movie': "Noche de juegos",
                'actor': "Michael Carlyle Hall",
                'characterName': 'The Bulgarian',
                'screenTime': 370
            }
        ]
        for performance in performances:
            movie = Movie.objects.get(title=performance['movie'])
            actor = Actor.objects.get(name=performance['actor'])
            Performance.objects.get_or_create(
                movie=movie,
                actor=actor,
                characterName=performance['characterName'],
                screenTime=performance['screenTime']
            )

        # Reviews
        reviews = [
            {
                'body': "Muy buena película, muy recomendada.",
                'rating': 4,
                'publicationDate': timezone.now(),
                'hateScore': 0,
                'state': Review.State.PUBLISHED,
                'user': 'authenticated1',
                'movie': 'Bad Boys: Ride Or Die'
            },
            {
                'body': "No me ha gustado, es muy aburrida.",
                'rating': 2,
                'publicationDate': timezone.now(),
                'hateScore': 0,
                'state': Review.State.PUBLISHED,
                'user': 'authenticated2',
                'movie': 'Bad Boys: Ride Or Die'
            },
            {
                'body': "¡Una obra maestra!",
                'rating': 5,
                'publicationDate': timezone.now(),
                'hateScore': 0,
                'state': Review.State.PUBLISHED,
                'user': 'authenticated1',
                'movie': 'El señor de los anillos'
            }
        ]
        for review in reviews:
            user = User.objects.get(username=review['user'])
            movie = Movie.objects.get(title=review['movie'])
            Review.objects.get_or_create(
                body=review['body'],
                rating=review['rating'],
                publicationDate=review['publicationDate'],
                hateScore=review['hateScore'],
                state=review['state'],
                user=user,
                movie=movie
            )

        self.stdout.write(self.style.SUCCESS('Database populated successfully'))
