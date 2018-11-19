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

@register.filter(name='format_datetime')
def format_datetime(value):
    hours, rem = divmod(value.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return '{}:{}:{}.{}'.format(hours, minutes, seconds, value.microseconds)



@register.inclusion_tag('decoding_app/tags/BluePlayer.html')
def bp(*args, **kwargs):
    return {}

@register.inclusion_tag('decoding_app/tags/BluePlayers.html')
def bps(*args, **kwargs):
    return {}

@register.inclusion_tag('decoding_app/tags/OrangePlayer.html')
def op(*args, **kwargs):
    return {}