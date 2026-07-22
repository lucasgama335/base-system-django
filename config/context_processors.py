from django.conf import settings


def export_settings(request):
    return {
        'APP_NAME': getattr(settings, 'APP_NAME', 'Instituto Paulo Gomes')
    }