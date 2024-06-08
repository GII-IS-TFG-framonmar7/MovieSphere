from django.contrib import admin

from .models import Genre, Movie, Performance, Emotion, Analysis, HomeImage, Review, Actor

admin.site.register(Genre)
admin.site.register(Movie)
admin.site.register(Actor)
admin.site.register(Performance)
admin.site.register(Emotion)
admin.site.register(Analysis)
admin.site.register(HomeImage)
admin.site.register(Review)