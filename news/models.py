from django.apps import apps
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class New(models.Model):
    class State(models.TextChoices):
        PUBLISHED = 'PUBLISHED', 'Published'
        IN_DRAFT = 'IN_DRAFT', 'In Draft'
        IN_REVIEW = 'IN_REVIEW', 'In Review'
        FORBIDDEN = 'FORBIDDEN', 'Forbidden'
        DELETED = 'DELETED', 'Deleted'
        
    title = models.CharField(max_length=100, unique=True)
    body = models.TextField()
    photo = models.ImageField(upload_to='images/')
    publicationDate = models.DateTimeField(
        blank=True, null=True    
    )
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    hateScore = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10000)]
    )
    state = models.CharField(
        max_length=50,
        choices=State.choices,
        default=State.IN_REVIEW,
    )

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if not is_new:
            old_new = New.objects.get(pk=self.pk)
            old_state = old_new.state
            if old_new.photo and old_new.photo != self.photo:
                old_new.photo.delete(save=False)
        else:
            old_state = None
        
        super().save(*args, **kwargs)

        should_create_strike = (
            (is_new and self.state == self.State.FORBIDDEN) or
            (not is_new and old_state != self.state and self.state == self.State.FORBIDDEN)
        )

        Strike = apps.get_model('users', 'Strike')
        # Check if a strike already exists for this new
        strike_exists = Strike.objects.filter(new=self).exists()

        if should_create_strike and not strike_exists:
            Strike.objects.create(new=self, user=self.author)
        elif should_create_strike and strike_exists:
            raise ValidationError("This new already has an associated strike and cannot generate another.")

    def __str__(self):
        return self.title