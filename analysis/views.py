from django.shortcuts import render
from django.shortcuts import get_object_or_404, render
from .models import Actor, Gender
from django.http import JsonResponse

def actors(request):
    filter_params = {}

    name = request.GET.get('name')
    if name:
        filter_params['name__icontains'] = name

    gender = request.GET.get('gender')
    if gender and gender != 'none':
        filter_params['gender'] = gender

    actors_queryset = Actor.objects.filter(**filter_params).distinct()
    gender_options = [('none', 'Todos')] + list(Gender.choices)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        actors_list = [
            {
                'id': actor.id, 
                'name': actor.name,
                'gender': actor.gender,
                'principalImage': actor.principalImage.url if actor.principalImage else ''
            } for actor in actors_queryset
        ]
        return JsonResponse({'actors': actors_list})
    
    return render(request, 'actors.html', {'actors': actors_queryset, 'genders': gender_options})

def actor_detail(request, actor_id):
    actor = get_object_or_404(Actor, pk=actor_id)

    return render(request, 'actor_detail.html', {'actor': actor})