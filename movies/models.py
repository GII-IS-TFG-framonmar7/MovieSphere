from django.db import models

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
