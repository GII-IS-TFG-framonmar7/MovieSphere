from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from news.models import New
from movies.models import Review
from django.contrib.sessions.models import Session
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class Strike(models.Model):    
    date_issued = models.DateField(
        default=timezone.now,
        validators=[MinValueValidator(date(1888, 1, 1)), MaxValueValidator(date.today())]
    )
    expiration_date = models.DateField(
        validators=[MinValueValidator(date(1888, 1, 1)), MaxValueValidator(date.today() + relativedelta(years=1))]
    )
    review = models.OneToOneField(Review, on_delete=models.CASCADE, null=True, related_name='strike')
    new = models.OneToOneField(New, on_delete=models.CASCADE, null=True, related_name='strike')
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
            if self.review:
                text_content = strip_tags(render_to_string('email/strike_notification.html', {'user': self.user, 'sample': self.review}))
                html_content = render_to_string('email/strike_notification.html', {'user': self.user, 'sample': self.review})
            else:
                text_content = strip_tags(render_to_string('email/strike_notification.html', {'user': self.user, 'sample': self.new}))
                html_content = render_to_string('email/strike_notification.html', {'user': self.user, 'sample': self.new})
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [self.user.email]
            msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            if current_strikes >= 3:
                self.user.profile.is_banned = True
                self.user.profile.save()

                # Force logout
                sessions = Session.objects.filter(session_key__in=[
                    session.session_key for session in Session.objects.all()
                    if session.get_decoded().get('_auth_user_id') == str(self.user.id)
                ])
                if sessions:
                    sessions.delete()

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
    
