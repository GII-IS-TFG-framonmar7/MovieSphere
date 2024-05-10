from django.apps import apps
from django.shortcuts import get_object_or_404, render, redirect
from .models import Movie, Genre, Review, Image
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.db.models import Avg
from django.http import JsonResponse

def home(request):
    # Obtener modelos de las aplicaciones
    New = apps.get_model('news', 'New')
    Review = apps.get_model('movies', 'Review')
    Image = apps.get_model('movies', 'Image')
    
    # Obtener conjuntos de consultas
    new_queryset = New.objects.filter().order_by('-publicationDate').distinct()[:1]  # Última noticia
    reviews_queryset = Review.objects.filter().order_by('-publicationDate').distinct()[:2]  # Últimas 2 reseñas
    images_queryset = Image.objects.filter().distinct()  # Todas las imágenes para el carrusel

    # Crear listas para el contexto
    latest_new = new_queryset.first() if new_queryset else None
    reviews_list = [{'movie': review.movie, 'user': review.user, 'body': review.body, 'rating': review.rating, 'publicationDate': review.publicationDate} for review in reviews_queryset]
    images_list = [{'index': index + 1, 'url': image.url} for index, image in enumerate(images_queryset)]

    context = {
        'latest_new': latest_new,
        'latest_reviews': reviews_list,
        'carousel_images': images_list,
    }

    return render(request, 'home.html', context)
              
def movies(request):
    filter_params = {}

    genre_name = request.GET.get('genre')
    if genre_name and genre_name != 'none':
        filter_params['genres__name'] = genre_name

    title = request.GET.get('title')
    if title:
        filter_params['title__icontains'] = title

    director_name = request.GET.get('director')
    if director_name:
        filter_params['director__icontains'] = director_name

    actor_name = request.GET.get('actor')
    if actor_name:
        filter_params['actors__name__icontains'] = actor_name

    movies_queryset = Movie.objects.filter(**filter_params).distinct()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        movies_list = [
            {
                'id': movie.id, 
                'title': movie.title, 
                'image_url': movie.image.url if movie.image else ''
            } for movie in movies_queryset
        ]
        return JsonResponse({'movies': movies_list})
    
    genres = Genre.objects.all()
    return render(request, 'movies.html', {'movies': movies_queryset, 'genres': genres})

def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    reviews = Review.objects.filter(movie=movie, state=Review.State.PUBLISHED)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    rating_range = range(1, 6)
    last_review = reviews.last()

    return render(request, 'movie_detail.html', {'movie': movie, 'average_rating': average_rating, 'rating_range': rating_range, 'number_of_reviews': reviews.count, 'last_review': last_review})

def calculate_hate_score(body):
    my_app_config = apps.get_app_config('ai_models')
    toxic_model = my_app_config.toxic_model
    toxic_vectorizer = my_app_config.toxic_vectorizer
    offensive_model = my_app_config.offensive_model
    offensive_vectorizer = my_app_config.offensive_vectorizer
    hate_model = my_app_config.hate_model
    hate_vectorizer = my_app_config.hate_vectorizer

    hate_score = 0

    for model, vectorizer in [(toxic_model, toxic_vectorizer), (offensive_model, offensive_vectorizer), (hate_model, hate_vectorizer)]:
        body_vectorized = vectorizer.transform([body])
        hate_score += model.predict(body_vectorized)[0]

    return hate_score

@login_required
def create_review(request, movie_id, is_draft=False):
    movie = get_object_or_404(Movie, pk=movie_id)
    if request.method == 'POST':
        body = request.POST.get('body')
        rating = request.POST.get('rating')
        hateScore = 0

        review = Review(
            body=body,
            rating=rating,
            user=request.user,
            movie=movie,
            hateScore=hateScore
        )

        if is_draft:
            review.state = Review.State.IN_DRAFT
            review.save()
            messages.info(request, 'Tu reseña ha sido guardada como borrador.')
            return redirect('movie_detail', movie_id=movie.id)
        else:
            hateScore = calculate_hate_score(body)
            review.hateScore = hateScore

            if hateScore < 1:
                review.state = Review.State.PUBLISHED
                review.publicationDate = timezone.now()
                messages.success(request, '¡Tu reseña ha sido publicada!')
            elif 1 <= hateScore < 3:
                review.state = Review.State.IN_REVIEW
                messages.warning(request, 'Tu reseña está pendiente de aprobación.')
            else:
                review.state = Review.State.FORBIDDEN
                messages.error(request, 'Tu reseña no se ha publicado debido a contenido inapropiado.')

            review.save()
        
        return redirect('movie_detail', movie_id=movie.id)
    else:
        messages.error(request, 'Error al publicar tu reseña.')
        return redirect('movie_detail', movie_id=movie.id)
    
@login_required
def update_review(request, review_id, is_draft=False):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    new_rating = request.POST.get('rating')
    new_body = request.POST.get('body')

    if request.method == 'POST':
        review.rating = new_rating
        review.body = new_body
        if is_draft:
            messages.success(request, 'Reseña actualizada correctamente.')
            review.save()
            return redirect('draft_reviews')
        else:
            hateScore = calculate_hate_score(new_body)
            review.hateScore = hateScore

            if hateScore < 1:
                review.state = Review.State.PUBLISHED
                review.publicationDate = timezone.now()
                messages.success(request, 'Reseña publicada exitosamente.')
                review.save()
                return redirect('movie_reviews', movie_id=review.movie.id)
            elif 1 <= hateScore < 3:
                review.state = Review.State.IN_REVIEW
                messages.warning(request, 'Tu reseña está pendiente de aprobación.')
                review.save()
                return redirect('movie_detail', movie_id=review.movie.id)
            else:
                review.state = Review.State.FORBIDDEN
                messages.error(request, 'Tu reseña no se ha publicado debido a contenido inapropiado.')
                review.save()
                return redirect('movie_detail', movie_id=review.movie.id)
    else:
        messages.error(request, 'No se pudo actualizar la reseña.')
        return redirect('some_view_for_review_details', review_id=review.id)
    
@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    if request.method == 'POST':
        review.state = Review.State.DELETED
        review.save()
        messages.success(request, 'La reseña ha sido eliminada con éxito.')
        return redirect('draft_reviews')
    else:
        messages.error(request, 'No se pudo eliminar la reseña.')
        return redirect('draft_reviews')

def movie_reviews(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    reviews = Review.objects.filter(movie=movie, state=Review.State.PUBLISHED)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    rating = request.GET.get('rating')
    if rating:
        reviews = reviews.filter(rating=rating)
    
    context = {
        'movie': movie,
        'reviews': reviews,
        'average_rating': average_rating
    }
    
    return render(request, 'movie_reviews.html', context)

@login_required
def view_draft_reviews(request):
    draft_reviews = Review.objects.filter(user=request.user, state=Review.State.IN_DRAFT)
    for review in draft_reviews:
        print(review)
    
    return render(request, 'movie_reviews.html', {'reviews': draft_reviews, 'show_drafts': True})