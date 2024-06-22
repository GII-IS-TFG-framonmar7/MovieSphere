from django.contrib import admin

from .models import Strike, UserProfile

admin.site.register(UserProfile)
admin.site.register(Strike)