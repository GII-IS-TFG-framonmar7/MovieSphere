from django.conf import settings
import os
import cv2
import joblib
import numpy as np
from slugify import slugify
from .models import Emotion, Analysis

def delete_images(image_path):
    full_path = os.path.join(settings.MEDIA_ROOT, image_path)
    try:
        os.remove(full_path)
    except FileNotFoundError:
        print(f"El archivo {full_path} no existe.")

def check_files_exist(files):
    for file in files:
        if not os.path.exists(file):
            raise FileNotFoundError(f"File not found: {file}")

def load_joblib(path):
    return joblib.load(path)

def load_yolo_model(cfg_name, weights_name, names_name):
    resources_path = os.path.join(settings.BASE_DIR, 'ai_models', 'resources')
    yolo_path = os.path.join(resources_path, 'yolo')
    cfg_path = os.path.join(yolo_path, cfg_name)
    weights_path = os.path.join(yolo_path, weights_name)
    names_path = os.path.join(yolo_path, names_name)

    net = cv2.dnn.readNet(weights_path, cfg_path)
    with open(names_path, 'r') as f:
        classes = [line.strip() for line in f.readlines()]

    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    return net, classes, output_layers

def detect_faces(image, net, output_layers, threshold=0.7):
    height, width = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    boxes = []
    confidences = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > threshold:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))

    indices = cv2.dnn.NMSBoxes(boxes, confidences, threshold, 0.4)
    faces = [(boxes[i], confidences[i]) for i in indices]
    return faces

def calculate_frame_statistics(frame_files, frames_dir, actor_model, happy_model, sad_model, angry_model, face_net, face_output_layers):
    actor_threshold = 0.7; actor_frame_count = 0
    happy_threshold = 0.7; happy_frame_count = 0
    angry_threshold = 0.7; angry_frame_count = 0
    sadness_threshold = 0.8; sadness_frame_count = 0

    for index, frame_file in enumerate(frame_files):  # Para cada frame
        frame_path = os.path.join(frames_dir, frame_file)
        image = cv2.imread(frame_path)

        faces = detect_faces(image, face_net, face_output_layers, threshold=0.7)
        actor_prediction = None
        happy_prediction = None
        angry_prediction = None
        sad_prediction = None

        for (box, confidence) in faces:  # Para cada rostro en el frame 
            x, y, w, h = box
            face = image[y:y + h, x:x + w]
            processed_face = preprocess_face_for_actor_model(face)

            # Hacer la predicción usando el modelo de detección de actores
            actor_prediction = actor_model.predict(processed_face)

            if actor_prediction > actor_threshold:  # Si el rostro es del actor
                actor_frame_count += 1

                processed_face = preprocess_face_for_emotion_model(face)
                happy_prediction = happy_model.predict(processed_face)
                angry_prediction = angry_model.predict(processed_face)
                sad_prediction = sad_model.predict(processed_face)

                if happy_prediction > happy_threshold:
                    happy_frame_count += 1
                if angry_prediction > angry_threshold:
                    angry_frame_count += 1
                if sad_prediction > sadness_threshold:
                    sadness_frame_count += 1

                break

    total_frames = len(frame_files)
    statistics = {
        'total_frames': total_frames,
        'actor_frame_count': actor_frame_count,
        'happy_frame_count': happy_frame_count,
        'angry_frame_count': angry_frame_count,
        'sadness_frame_count': sadness_frame_count
    }
    return statistics

def preprocess_face_for_actor_model(face):
    processed_face = cv2.resize(face, (100, 100))
    processed_face = cv2.cvtColor(processed_face, cv2.COLOR_BGR2GRAY)
    processed_face = processed_face.reshape(-1, 100, 100, 1) / 255.0
    return processed_face

def preprocess_face_for_emotion_model(face):
    processed_face = cv2.resize(face, (48, 48))
    processed_face = cv2.cvtColor(processed_face, cv2.COLOR_BGR2GRAY)
    processed_face = processed_face.reshape(-1, 48, 48, 1) / 255.0
    return processed_face

def update_performance_instance(instance, statistics):
    total_frames = statistics['total_frames']
    actor_frame_percentage = statistics['actor_frame_count'] / total_frames
    happy_frame_percentage = statistics['happy_frame_count'] / total_frames
    sad_frame_percentage = statistics['sadness_frame_count'] / total_frames
    angry_frame_percentage = statistics['angry_frame_count'] / total_frames

    movie_duration = instance.movie.duration * 60
    appearance_time = movie_duration * actor_frame_percentage
    happy_time = movie_duration * happy_frame_percentage
    sad_time = movie_duration * sad_frame_percentage
    angry_time = movie_duration * angry_frame_percentage

    instance.screenTime = round(appearance_time, 2)
    instance.save()

    # Crear análisis para emociones
    create_emotion_analysis(instance, 'Felicidad', happy_time)
    create_emotion_analysis(instance, 'Tristeza', sad_time)
    create_emotion_analysis(instance, 'Enfado', angry_time)

def create_emotion_analysis(instance, emotion_name, result):
    try:
        emotion = Emotion.objects.get(name=emotion_name)
        Analysis.objects.update_or_create(
            performance=instance,
            emotion=emotion,
            defaults={'result': round(result, 2)}
        )
    except Emotion.DoesNotExist:
        print(f'Emotion {emotion_name} does not exist in the database.')
