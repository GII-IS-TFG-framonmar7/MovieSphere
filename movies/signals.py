from django.apps import apps
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from .models import HomeImage, Movie, Performance, Actor
from .utils import delete_images
import os
from django.conf import settings
from django.utils.text import slugify
import shutil
import cv2
import numpy as np
from .utils import (load_joblib, load_yolo_model, calculate_frame_statistics, update_performance_instance, check_files_exist)

@receiver(post_save, sender=Movie)
def create_movie_directory(sender, instance, created, **kwargs):
    if created:
        directory_name = slugify(instance.title.replace(" ", "_"))
        new_path = os.path.join(settings.MEDIA_ROOT, f'images/movies/{directory_name}')
        os.makedirs(new_path, exist_ok=True)

@receiver(post_delete, sender=Movie)
def delete_movie_images(sender, instance, **kwargs):
    directory_name = slugify(instance.title.replace(" ", "_"))
    movie_path = os.path.join(settings.MEDIA_ROOT, f'images/movies/{directory_name}')
    if os.path.exists(movie_path):
        shutil.rmtree(movie_path)
        print(f"Deleted directory {movie_path}")
    else:
        print(f"The directory {movie_path} does not exist")

@receiver(post_save, sender=Performance)
def performance_post_save(sender, instance, created, **kwargs):
    if instance.screenTime:
        return
    
    post_save.disconnect(performance_post_save, sender=Performance)

    try:
        resources_path = os.path.join(settings.BASE_DIR, 'ai_models', 'resources')
        yolo_path = os.path.join(resources_path, 'yolo')
        
        # Archivos de modelos
        actor_model_filename = f"{slugify(instance.actor.name.replace(' ', '_')).lower()}_detection.joblib"
        actor_model_full_path = os.path.join(resources_path, actor_model_filename)
        happy_model_full_path = os.path.join(resources_path, "happy_detection.joblib")
        sad_model_full_path = os.path.join(resources_path, "sad_detection.joblib")
        angry_model_full_path = os.path.join(resources_path, "angry_detection.joblib")

        # Archivos de YOLO
        yolo_files = [
            os.path.join(yolo_path, 'yolov3-face.cfg'),
            os.path.join(yolo_path, 'yolov3-face.weights'),
            os.path.join(yolo_path, 'face.names')
        ]

        # Verificar que todos los archivos existen
        check_files_exist([actor_model_full_path, happy_model_full_path, sad_model_full_path, angry_model_full_path] + yolo_files)

        if os.path.exists(actor_model_full_path):
            actor_model = load_joblib(actor_model_full_path)
            happy_model = load_joblib(happy_model_full_path)
            sad_model = load_joblib(sad_model_full_path)
            angry_model = load_joblib(angry_model_full_path)

            face_net, face_classes, face_output_layers = load_yolo_model('yolov3-face.cfg', 'yolov3-face.weights', 'face.names')

            frames_dir = os.path.join(settings.MEDIA_ROOT, f"images/movies/{slugify(instance.movie.title.replace(' ', '_')).lower()}")
            frame_files = [f for f in os.listdir(frames_dir) if os.path.isfile(os.path.join(frames_dir, f))]

            statistics = calculate_frame_statistics(frame_files, frames_dir, actor_model, happy_model, sad_model, angry_model, face_net, face_output_layers)

            update_performance_instance(instance, statistics)
    finally:
        post_save.connect(performance_post_save, sender=Performance)

@receiver(post_delete, sender=HomeImage)
def appmodel_delete_images(sender, **kwargs):
    delete_images(kwargs['instance'].url.name)

@receiver(post_delete, sender=Movie)
def appmodel_delete_images(sender, **kwargs):
    delete_images(kwargs['instance'].image.name)

@receiver(post_delete, sender=Actor)
def appmodel_delete_images(sender, **kwargs):
    delete_images(kwargs['instance'].principalImage.name)