from django import template
from datetime import date, timedelta

register = template.Library()


@register.filter(name='minutes')
def convert_sec_to_min(value):
    tmin = value / 60
    ending = '' if tmin == 1 else 's'
    if tmin.is_integer():
        tmin = int(tmin)
    tmin = round(tmin, 1)
    return '{} minute{}'.format(tmin, ending)
