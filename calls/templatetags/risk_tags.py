from django import template

register = template.Library()


@register.filter
def risk_color(risk):
    colors = {
        'low': 'success',
        'moderate': 'warning',
        'high': 'danger',
    }
    return colors.get(risk.lower(), 'secondary')
