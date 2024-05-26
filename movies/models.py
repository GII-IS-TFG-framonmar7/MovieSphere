from datetime import date
from django.apps import apps
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from djmoney.models.fields import MoneyField
from django.core.validators import MinValueValidator, MaxValueValidator

def movie_directory_path(instance, filename):
    return f'images/movies/{instance.movie.id}/{filename}'

class Gender(models.TextChoices):
    MAN = 'MAN', 'Hombre'
    WOMAN = 'WOMAN', 'Mujer'
    OTHER = 'OTHER', 'Otro'

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    
class Actor(models.Model):
    name = models.CharField(max_length=100)
    gender = models.CharField(
        max_length=50,
        choices=Gender.choices,
        default=Gender.MAN,
    )
    birthday = models.DateField(
        validators=[MinValueValidator(date(1888, 1, 1)), MaxValueValidator(date.today())]
    )
    nationality = models.CharField(max_length=100)
    principalImage = models.ImageField(upload_to='images/')
    height = models.DecimalField(max_digits=5, decimal_places=2)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    hair_color = models.CharField(max_length=50)
    eye_color = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if not is_new:
            old_actor = Actor.objects.get(pk=self.pk)
            if old_actor.principalImage and old_actor.principalImage != self.principalImage:
                old_actor.principalImage.delete(save=False)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=100)
    director = models.CharField(max_length=100)
    releaseYear = models.PositiveIntegerField(
        validators=[MinValueValidator(1888), MaxValueValidator(2200)],
    )
    image = models.ImageField(upload_to='images/')
    duration = models.PositiveIntegerField(
        help_text="Duración en minutos",
        validators=[MinValueValidator(1), MaxValueValidator(600)],
    )
    country = models.CharField(max_length=100)
    budget = MoneyField(
        max_digits=14, decimal_places=2, default_currency='USD',
        validators=[MinValueValidator(0)]
    )
    revenue = MoneyField(
        max_digits=14, decimal_places=2, default_currency='USD',
        validators=[MinValueValidator(0)]
    )
    genres = models.ManyToManyField(Genre, related_name='movies')
    actors = models.ManyToManyField(Actor, through='Performance')

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if not is_new:
            old_movie = Movie.objects.get(pk=self.pk)
            if old_movie.image and old_movie.image != self.image:
                old_movie.image.delete(save=False)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
class Review(models.Model):
    class State(models.TextChoices):
        PUBLISHED = 'PUBLISHED', 'Published'
        IN_DRAFT = 'IN_DRAFT', 'In Draft'
        IN_REVIEW = 'IN_REVIEW', 'In Review'
        FORBIDDEN = 'FORBIDDEN', 'Forbidden'
        DELETED = 'DELETED', 'Deleted'

    body = models.TextField()
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    publicationDate = models.DateField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(date(1888, 1, 1)), MaxValueValidator(date.today())]
    )
    hateScore = models.IntegerField(
        default=0
    )
    state = models.CharField(
        max_length=50,
        choices=State.choices,
        default=State.IN_REVIEW,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if not is_new:
            old_review = Review.objects.get(pk=self.pk)
            old_state = old_review.state
        else:
            old_state = None
        
        super().save(*args, **kwargs)


        should_create_strike = (
            (is_new and self.state == self.State.FORBIDDEN) or
            (not is_new and old_state != self.state and self.state == self.State.FORBIDDEN)
        )

        Strike = apps.get_model('users', 'Strike')
        # Check if a strike already exists for this review
        strike_exists = Strike.objects.filter(review=self).exists()

        if should_create_strike and not strike_exists:
            Strike.objects.create(review=self, user=self.user)
        elif should_create_strike and strike_exists:
            raise ValidationError("This review already has an associated strike and cannot generate another.")

    def __str__(self):
        return f'{self.state}: {self.user.username} for {self.movie.title}'
    
class Performance(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)
    characterName = models.CharField(max_length=100)
    screenTime = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        validators=[MinValueValidator(0), MaxValueValidator(10000)]
    )

    def __str__(self):
        return f'{self.actor.name} as {self.characterName} in {self.movie.title}'
    
class Image(models.Model):
    url = models.ImageField(upload_to='images/')

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if not is_new:
            old_image = Image.objects.get(pk=self.pk)
            if old_image.url and old_image.url != self.url:
                old_image.url.delete(save=False)
        
        super().save(*args, **kwargs)
