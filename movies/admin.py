from django.contrib import admin

from .models import Genre, Movie, Actor, Performance, Image

admin.site.register(Genre)
admin.site.register(Movie)
admin.site.register(Actor)
admin.site.register(Performance)
admin.site.register(Image)