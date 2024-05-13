from django.apps import apps
from django.shortcuts import render
from django.shortcuts import get_object_or_404, render, redirect
from .models import New, Category
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from .models import New, Category
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from .forms import CategoryForm

# Create your views here.

def news(request):
    filter_params = {}

    category_name = request.GET.get('category')
    if category_name and category_name != 'none':
        filter_params['category__name'] = category_name

    title = request.GET.get('title')
    if title:
        filter_params['title__icontains'] = title

    news_queryset = New.objects.filter(**filter_params, state=New.State.PUBLISHED).distinct()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        news_list = [
            {
                'id': new.id, 
                'title': new.title, 
                'image': new.photo.url if new.photo else ''
            } for new in news_queryset
        ]
        return JsonResponse({'news': news_list})
    
    categories = Category.objects.all()
    user_is_writer = request.user.groups.filter(name='Writer').exists()
    return render(request, 'news.html', {'news': news_queryset, 'categories': categories, 'user_is_writer': user_is_writer})

def new_detail(request, new_id):
    new = get_object_or_404(New, pk=new_id)

    return render(request, 'new_detail.html', {'new': new})

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
def create_new(request, is_draft=False):
    if request.method == 'POST':
        title = request.POST.get('title')
        body = request.POST.get('body')
        photo = request.FILES.get('photo')
        category = Category.objects.get(id=request.POST.get('category'))
        hateScore = 0

        new = New(
            title=title,
            body=body,
            photo=photo,
            category=category,
            author=request.user,
            hateScore=hateScore
        )

        if is_draft:
            new.state = New.State.IN_DRAFT
            new.save()
            messages.info(request, 'Tu noticia ha sido guardada como borrador.')
            return redirect('draft_news')
        else:
            hateScore = 2*calculate_hate_score(body) + calculate_hate_score(title)
            new.hateScore = hateScore

            if hateScore < 3:
                new.state = New.State.PUBLISHED
                new.publicationDate = timezone.now()
                new.save()
                messages.success(request, '¡Tu noticia ha sido publicada!')
                return redirect('new_detail', new_id=new.id)
            elif 3 <= hateScore < 7:
                new.state = New.State.IN_REVIEW
                new.save()
                messages.warning(request, 'Tu noticia está pendiente de aprobación.')
                return redirect('news')
            else:
                new.state = New.State.FORBIDDEN
                new.save()
                messages.error(request, 'Tu noticia no se ha publicado debido a contenido inapropiado.')
                return redirect('news')
    else:
        messages.error(request, 'Error al publicar tu noticia.')
        return redirect('new_detail', new_id=new.id)

@login_required
def update_new(request, new_id, is_draft=False):
    new = get_object_or_404(New, id=new_id)
    new_title = request.POST.get('title')
    new_body = request.POST.get('body')
    print(request.FILES.get('photo'))
    new_photo = request.FILES.get('photo', None)
    new_category = Category.objects.get(id=request.POST.get('category'))

    if request.method == 'POST':
        new.title = new_title
        new.body = new_body
        print(new_photo)
        if new_photo:
            new.photo = new_photo
        new.category = new_category
        if is_draft:
            messages.success(request, 'Noticia actualizada correctamente.')
            new.save()
            return redirect('draft_news')
        else:
            hateScore = 2*calculate_hate_score(new_body) + calculate_hate_score(new_title)
            new.hateScore = hateScore

            if hateScore < 3:
                new.state = New.State.PUBLISHED
                new.publicationDate = timezone.now()
                new.save()
                messages.success(request, '¡Tu noticia ha sido publicada!')
                return redirect('new_detail', new_id=new.id)
            elif 3 <= hateScore < 7:
                new.state = New.State.IN_REVIEW
                new.save()
                messages.warning(request, 'Tu noticia está pendiente de aprobación.')
                return redirect('news')
            else:
                new.state = New.State.FORBIDDEN
                new.save()
                messages.error(request, 'Tu noticia no se ha publicado debido a contenido inapropiado.')
                return redirect('news')
    else:
        messages.error(request, 'No se pudo actualizar la noticia.')
        return redirect('some_view_for_new_details', new_id=new.id)
    
@login_required
def delete_new(request, new_id):
    new = get_object_or_404(New, id=new_id)
    if request.method == 'POST':
        new.state = New.State.DELETED
        new.save()
        messages.success(request, 'La noticia ha sido eliminada con éxito.')
        return redirect('draft_news')
    else:
        messages.error(request, 'No se pudo eliminar la noticia.')
        return redirect('draft_news')
    
@login_required
def view_draft_news(request):
    news = New.objects.filter(author=request.user, state=New.State.IN_DRAFT)
    categories = Category.objects.all()
    
    return render(request, 'draft_news.html', {'news': news, 'categories': categories})

def load_category_data(request):
    categories = Category.objects.all()
    return JsonResponse({
        'html': render_to_string('partials/category_list.html', {'categories': categories}, request=request)
    })

def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'form_is_valid': True,
                'html_category_list': render_to_string('partials/category_list.html', {
                    'categories': Category.objects.all()
                })
            })
        else:
            return JsonResponse({
                'form_is_valid': False,
                'is_creating': True,
                'html_form': render_to_string('partials/category_form.html', {
                    'form': form,
                    'is_creating': True
                })
            })
    else:
        form = CategoryForm()
        html_form = render_to_string('partials/category_form.html', {
            'form': form,
            'is_creating': True
        })
        return JsonResponse({'html_form': html_form})

def category_update(request, id):
    category = Category.objects.get(pk=id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return JsonResponse({'form_is_valid': True})
        else:
            return JsonResponse({
                'form_is_valid': False,
                'is_creating': False,
                'category_id': category.id,
                'html_form': render_to_string('partials/category_form.html', {
                    'form': form,
                    'is_creating': False
                })
            })
    else:
        form = CategoryForm(instance=category)
        html_form = render_to_string('partials/category_form.html', {
            'form': form,
            'is_creating': False
        })
        return JsonResponse({'html_form': html_form})

def category_delete(request, id):
    category = Category.objects.get(id=id)
    category.delete()
    return JsonResponse({'success': True})
