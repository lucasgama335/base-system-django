from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard_view(request):
    """
    Página inicial do sistema. 
    Centraliza os indicadores e a navegação principal.
    """
    # Como a view está protegida, você tem a garantia de que request.user 
    # é um objeto User válido (e não um AnonymousUser).
    context = {
        "user_name": request.user.first_name
    }
    return render(request, "core/dashboard/dashboard.html", context)
