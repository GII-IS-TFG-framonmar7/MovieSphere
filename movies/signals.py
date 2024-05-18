from django.apps import apps
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from .models import Image, Movie, Performance
from .utils import delete_images
import os
from django.conf import settings
from django.utils.text import slugify
import shutil
import cv2
import numpy as np
from joblib import load as load_joblib

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
    post_save.disconnect(performance_post_save, sender=Performance)

    try:
        resources_path = os.path.join(settings.BASE_DIR, 'ai_models', 'resources')
        actor_model_filename = f"{slugify(instance.actor.name.replace(' ', '_')).lower()}_detection.joblib"
        actor_model_full_path = os.path.join(resources_path, actor_model_filename)

        if os.path.exists(actor_model_full_path):
            actor_model = load_joblib(actor_model_full_path)

            # Rutas para archivos de YOLO
            yolo_path = os.path.join(resources_path, 'yolo')
            cfg_path = os.path.join(yolo_path, 'yolov3.cfg')
            weights_path = os.path.join(yolo_path, 'yolov3.weights')
            names_path = os.path.join(yolo_path, 'coco.names')

            net, classes = load_yolo_model(cfg_path, weights_path, names_path)
            layer_names = net.getLayerNames()
            output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

            # Enumerar todos los fotogramas extraídos
            frames_dir = os.path.join(settings.MEDIA_ROOT, f"images/movies/{slugify(instance.movie.title.replace(' ', '_')).lower()}")
            if os.path.exists(frames_dir) and os.path.isdir(frames_dir):
                frame_files = [f for f in os.listdir(frames_dir) if os.path.isfile(os.path.join(frames_dir, f))]
                if frame_files:
                    human_threshold = 0.8
                    actor_threshold = 0.75
                    actor_frame_count = 0

                    for index, frame_file in enumerate(frame_files): # Para cada frame
                        frame_path = os.path.join(frames_dir, frame_file)
                        image = cv2.imread(frame_path)
                        print(frame_path)

                        detected, detection = detect_human(image, net, output_layers, human_threshold)
                        prediction = None

                        if detected: # Si aparece un ser humano
                            processed_image = cv2.resize(image, (100, 100))
                            processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
                            processed_image = processed_image.reshape(-1, 100, 100, 1) / 255.0  # Normalizar

                            # Hacer la predicción usando el modelo de detección de actores
                            prediction = actor_model.predict(processed_image)

                            if prediction > actor_threshold:
                                actor_frame_count += 1

                    total_frames = len(frame_files)
                    actor_frame_percentage = actor_frame_count / total_frames

                    movie_duration = instance.movie.duration * 60
                    appearance_time = movie_duration * actor_frame_percentage
                    instance.screenTime = round(appearance_time, 2)
                    instance.save()
    finally:
        post_save.connect(performance_post_save, sender=Performance)

def load_yolo_model(cfg_path, weights_path, names_path):
    net = cv2.dnn.readNet(weights_path, cfg_path)
    with open(names_path, 'r') as f:
        classes = f.read().strip().split('\n')
    return net, classes

def detect_human(frame, net, output_layers, threshold=0.8):
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > threshold and class_id == 0:  # Clase 0 es 'person'
                return True, detection
    return False, None

@receiver(post_delete, sender=Image)
def appmodel_delete_images(sender, **kwargs):
    delete_images(kwargs['instance'].url.name)

@receiver(post_delete, sender=Movie)
def appmodel_delete_images(sender, **kwargs):
    delete_images(kwargs['instance'].image.name)