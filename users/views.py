from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.contrib import messages
from .forms import CustomAuthenticationForm, UserEditForm, CustomUserCreationForm
from django.contrib.auth import logout

# Create your views here.

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
                    'error': 'El nombre de usuario ya existe'
                })
        else:
            return render(request, 'signup.html', {
                'form': form,
                'error': 'Por favor, corrige el siguiente error'
            })
        
def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': CustomAuthenticationForm
        })
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'signin.html', {
                'form': CustomAuthenticationForm,
                'error': 'El nombre de usuario o la contraseña son incorrectas'
            })
        elif hasattr(user, 'profile') and user.profile.is_banned:
            return render(request, 'signin.html', {
                'form': CustomAuthenticationForm(),
                'error': 'Tu cuenta ha sido suspendida. Por favor, contacta al soporte para más información.'
            })
        else:
            login(request, user)
            return redirect('home')
        
def signout(request):
    logout(request)
    return redirect('home')
        
@login_required
def edit_profile(request):
    if request.method == 'GET':
        return render(request, 'edit_profile.html', {
            'form': UserEditForm(instance=request.user)
        })
    else:
        form = UserEditForm(request.POST, instance=request.user)

        if form.is_valid():
            try:
                form.save()
                messages.success(request, '¡Tu perfil ha sido actualizado con éxito!')
                return redirect('home')
            except IntegrityError:
                return render(request, 'edit_profile.html', {
                    'form': form,
                    'error': 'El nombre de usuario ya existe'
                })
        else:
            return render(request, 'edit_profile.html', {
                'form': form,
                'error': 'Por favor, corrige el siguiente error'
            })

@login_required
def change_password(request):
    messages.success(request, "¡Tu contraseña ha sido cambiada con éxito!")
    return redirect(('signin'))

def about_us(request):
    return render(request, 'about_us.html')