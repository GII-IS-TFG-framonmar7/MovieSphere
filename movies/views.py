from django.apps import apps
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.db import IntegrityError
from .models import Movie, Genre, Review
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import UserEditForm, CustomUserCreationForm
from django.utils import timezone
from django.contrib import messages
from django.db.models import Avg
from django.http import JsonResponse

def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {
            'form': CustomUserCreationForm
        })
    else:
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                return redirect('home')
            except IntegrityError:
                return render(request, 'signup.html', {
                    'form': form,
                    'error': 'Username already exists'
                })
        else:
            return render(request, 'signup.html', {
                'form': form,
                'error': 'Please correct the error below'
            })
        
def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': AuthenticationForm
        })
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'signin.html', {
                'form': AuthenticationForm,
                'error': 'Username or password is incorrect'
            })
        else:
            login(request, user)
            return redirect('home')
        
def signout(request):
    logout(request)
    return redirect('home')
        
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            new_password = form.cleaned_data['password']
            if new_password:
                user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            return redirect('home')
    else:
        form = UserEditForm(instance=request.user)

    return render(request, 'edit_profile.html', {'form': form})
              
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

    return render(request, 'movie_detail.html', {'movie': movie, 'average_rating': average_rating, 'rating_range': rating_range, 'number_of_reviews': reviews.count})


@login_required
def create_review(request, movie_id):
    my_app_config = apps.get_app_config('movies')
    toxic_model = my_app_config.toxic_model
    toxic_vectorizer = my_app_config.toxic_vectorizer
    offensive_model = my_app_config.offensive_model
    offensive_vectorizer = my_app_config.offensive_vectorizer
    hate_model = my_app_config.hate_model
    hate_vectorizer = my_app_config.hate_vectorizer

    movie = get_object_or_404(Movie, pk=movie_id)
    if request.method == 'POST':
        body = request.POST.get('body')
        rating = int(request.POST.get('rating'))
        hateScore = 0

        for model, vectorizer in [(toxic_model, toxic_vectorizer), (offensive_model, offensive_vectorizer), (hate_model, hate_vectorizer)]:
            body_vectorized = vectorizer.transform([body])
            hateScore += model.predict(body_vectorized)[0]

        if hateScore < 1:
            state = Review.State.PUBLISHED
            messages.success(request, '¡Tu reseña ha sido publicada!')
        elif 1 <= hateScore < 3:
            state = Review.State.IN_REVIEW
            messages.warning(request, 'Tu reseña está pendiente de aprobación.')
        else:
            state = Review.State.DELETED
            messages.error(request, 'Tu reseña no se ha publicado debido a contenido inapropiado.')
        
        review = Review(
            body=body,
            rating=rating,
            publicationDate=timezone.now(),
            state=state,
            user=request.user,
            movie=movie,
            hateScore=hateScore
        )
        review.save()
        
        return redirect('movie_detail', movie_id=movie.id)
    else:
        messages.error(request, 'Error al publicar tu reseña.')
        return redirect('movie_detail', movie_id=movie.id)

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