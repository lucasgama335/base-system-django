from django.conf import settings
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def get_ratelimit_ip(group, request):
    """
    Retorna o IP real do cliente adaptando-se dinamicamente ao ambiente
    com base na configuração NUM_PROXIES do settings.py.
    """
    # Busca a configuração do settings, se não existir assume 0 (desenvolvimento)
    num_proxies = getattr(settings, 'NUM_PROXIES', 0)
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    
    # Se estamos em produção (num_proxies > 0) e o cabeçalho existe
    if num_proxies > 0 and x_forwarded_for:
        ips = [ip.strip() for ip in x_forwarded_for.split(',')]
        if len(ips) >= num_proxies:
            # Seleciona o IP correto descartando os proxies conhecidos à direita
            return ips[-num_proxies - 1]
            
    # Fallback para desenvolvimento local ou requisições diretas sem proxy
    return request.META.get('REMOTE_ADDR')

def redirect_safe_next_url(request, route):
    # Redireciona o usuário para a url que ele estava tentando entrar ou caso seja inválida para a url da dashboard    
    next_url = request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)

    return redirect(route)