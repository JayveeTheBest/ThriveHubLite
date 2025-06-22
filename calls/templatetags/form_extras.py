from django import template
from calls.models import SiteConfig

register = template.Library()


@register.filter(name='add_class')
def add_class(value, css_class):
    return value.as_widget(attrs={'class': css_class})


@register.simple_tag
def get_site_config():
    return SiteConfig.load()
