from django.apps import apps
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=255)
    director = models.CharField(max_length=255)
    releaseYear = models.PositiveIntegerField()
    image = models.ImageField(upload_to='images/')
    duration = models.PositiveIntegerField(help_text="Duración en minutos")
    country = models.CharField(max_length=255)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    revenue = models.DecimalField(max_digits=12, decimal_places=2)
    genres = models.ManyToManyField(Genre, related_name='movies')
    actors = models.ManyToManyField('Actor', through='Performance')

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
    rating = models.PositiveIntegerField()
    publicationDate = models.DateField(blank=True, null=True)
    hateScore = models.IntegerField(default=0)
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
    
class Actor(models.Model):
    name = models.CharField(max_length=255)
    birthday = models.DateField()
    nationality = models.CharField(max_length=255)
    principalImage = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.name
    
class Performance(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)
    characterName = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.actor.name} as {self.characterName} in {self.movie.title}'
    
class Image(models.Model):
    url = models.ImageField(upload_to='images/')
