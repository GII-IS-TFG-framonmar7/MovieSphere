from django.db import models

class Gender(models.TextChoices):
    MAN = 'MAN', 'Hombre'
    WOMAN = 'WOMAN', 'Mujer'
    OTHER = 'OTHER', 'Otro'

class Actor(models.Model):
    name = models.CharField(max_length=255)
    gender = models.CharField(
        max_length=50,
        choices=Gender.choices,
        default=Gender.MAN,
    )
    birthday = models.DateField()
    nationality = models.CharField(max_length=255)
    principalImage = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.name
    