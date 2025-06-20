from .utils import get_primary_color
from .models import SiteConfig


def site_config(request):
    try:
        config = SiteConfig.objects.first()
    except SiteConfig.DoesNotExist:
        config = None
    return {
        'site_config': config,
        'primary_color': get_primary_color()
    }
