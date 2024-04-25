from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ValidationError

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

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

        # Check if a strike already exists for this review
        strike_exists = Strike.objects.filter(review=self).exists()

        if should_create_strike and not strike_exists:
            Strike.objects.create(review=self, user=self.user)
        elif should_create_strike and strike_exists:
            raise ValidationError("This review already has an associated strike and cannot generate another.")

    def __str__(self):
        return f'{self.state}: {self.user.username} for {self.movie.title}'
    
class Strike(models.Model):    
    date_issued = models.DateField(default=timezone.now)
    expiration_date = models.DateField()
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='strike')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='warnings')

    def save(self, *args, **kwargs):
        if not self.pk:
            self.expiration_date = self.date_issued + relativedelta(months=3)

        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            current_strikes = Strike.objects.filter(
                user=self.user, 
                date_issued__lte=timezone.now(), 
                expiration_date__gt=timezone.now()
            ).count()

            subject = 'Incumplimiento de las políticas de comunidad'
            text_content = strip_tags(render_to_string('email/strike_notification.html', {'user': self.user, 'review': self.review}))
            html_content = render_to_string('email/strike_notification.html', {'user': self.user, 'review': self.review})
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [self.user.email]
            msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            if current_strikes >= 3:
                self.user.profile.is_banned = True
                self.user.profile.save()

                subject = 'Esto es embarazoso...'
                text_content = strip_tags(render_to_string('email/ban_notification.html', {'user': self.user}))
                html_content = render_to_string('email/ban_notification.html', {'user': self.user})
                from_email = settings.EMAIL_HOST_USER
                recipient_list = [self.user.email]
                msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
                msg.attach_alternative(html_content, "text/html")
                msg.send()
    
    def __str__(self):
        return f'Strike for {self.user.username} on {self.date_issued.strftime("%Y-%m-%d")}'
    
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
