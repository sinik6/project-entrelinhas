"""Para onde o servidor pode enviar push (spec 010, CTL-81): só serviços conhecidos, só HTTPS, nunca IP nem host interno.

O endereço da assinatura vem do navegador de quem se inscreve, ou seja, de fora: sem esta lista o servidor poderia ser levado
a chamar qualquer endereço (SSRF).
"""

import ipaddress
from urllib.parse import urlsplit

HOSTS_EXATOS = frozenset(
    {"fcm.googleapis.com", "updates.push.services.mozilla.com", "web.push.apple.com"}
)
SUFIXOS = (".push.apple.com", ".notify.windows.com")
TAMANHO_MAXIMO = 2048


def endpoint_permitido(endpoint) -> bool:
    if not isinstance(endpoint, str) or not endpoint or len(endpoint) > TAMANHO_MAXIMO:
        return False
    if endpoint != endpoint.strip():
        return False
    try:
        partes = urlsplit(endpoint)
        porta = partes.port
    except ValueError:
        return False
    if partes.scheme != "https" or partes.username or partes.password or "@" in partes.netloc:
        return False
    if porta not in (None, 443):
        return False
    host = (partes.hostname or "").lower()
    if not host or host.endswith("."):
        return False
    try:
        ipaddress.ip_address(host)
        return False  # IP, de qualquer tipo
    except ValueError:
        pass
    return host in HOSTS_EXATOS or any(host.endswith(s) and len(host) > len(s) for s in SUFIXOS)
