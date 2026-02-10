from .models import Obra

def recent_obras(request):
    """Return last 6 obras for navbar quick access."""
    try:
        obras = list(Obra.objects.filter(ativo=True).order_by('-created_at')[:6])
    except Exception:
        obras = []
    return {'recent_obras': obras}
