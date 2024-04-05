from django import template
from django.utils.timesince import timesince as timesince_
from django.utils import timezone
from django.utils.timezone import is_naive, make_aware, get_default_timezone


register = template.Library()

@register.filter
def times(n, value):
    try:
        n = int(n)
    except (ValueError, TypeError):
        return value
    
    return str(value) * n

@register.filter(name='sub')
def sub(value, arg):
    try:
        return value - arg
    except TypeError:
        return 0
    