from django import template
from django.forms.boundfield import BoundField
from calls.models import SiteConfig
from django.templatetags.static import static
from datetime import timedelta


register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    if isinstance(field, BoundField):
        return field.as_widget(attrs={"class": css_class})
    return field


@register.simple_tag
def get_site_config():
    return SiteConfig.load()


@register.simple_tag
def get_logo_url():
    config = SiteConfig.objects.first()
    if config and config.logo:
        return config.logo.url
    return static('images/default-favicon.png')  # fallback


@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def contains(set_or_list, value):
    return str(value) in str(set_or_list)


@register.filter
def add_days(value, days):
    return value + timedelta(days=int(days))


@register.filter
def filter_weekends(day_list):
    return [d for d in day_list if d.weekday() >= 5]