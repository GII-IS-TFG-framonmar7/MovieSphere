from django.dispatch import receiver
from django.db.models.signals import post_delete
from .models import Actor
from .utils import delete_images


@receiver(post_delete, sender=Actor)
def appmodel_delete_images(sender, **kwargs):
    delete_images(kwargs['instance'].principalImage.name)