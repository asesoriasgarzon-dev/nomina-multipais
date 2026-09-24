"""Detección de idioma por ubicación real del visitante (geolocalización por
IP), para la página de entrada y el panel consolidado — donde no hay todavía
un país de contexto (a diferencia de un formulario de país específico, donde
el idioma correcto es el de ESE país, sin importar dónde esté físicamente
quien lo llena).

Usa ip-api.com (gratis, sin API key, ~45 consultas/minuto — de sobra para el
tráfico interno de 14 países). Nota de privacidad: esto envía la IP del
visitante a ese servicio externo solo para resolver su país; no se envía
ningún otro dato del sistema.
"""

import ipaddress

import requests

PAIS_A_IDIOMA = {
    "US": "en",
    "PR": "en",
    "BR": "pt",
    "HK": "zh-hk",
    "CN": "zh",
    "CO": "es", "MX": "es", "PE": "es", "CL": "es", "AR": "es", "EC": "es",
    "VE": "es", "PA": "es", "CR": "es", "HN": "es", "GT": "es", "SV": "es",
    "NI": "es", "DO": "es", "PY": "es", "UY": "es", "BO": "es", "ES": "es",
}

_cache = {}


def _es_ip_privada(ip):
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return True


def idioma_por_ip(ip, timeout=1.5):
    """Devuelve el código de idioma según el país de `ip`, o None si no se
    puede determinar (IP privada/local — típico en desarrollo — o el
    servicio de geolocalización falla). Nunca lanza excepción: un fallo aquí
    nunca debe romper ni bloquear la carga de la página, solo se pierde la
    detección automática y el sistema cae al siguiente criterio de idioma."""
    if not ip or _es_ip_privada(ip):
        return None
    if ip in _cache:
        return _cache[ip]
    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,countryCode"},
            timeout=timeout,
        )
        data = r.json()
        if data.get("status") != "success":
            return None
        lang = PAIS_A_IDIOMA.get(data.get("countryCode"))
        _cache[ip] = lang
        return lang
    except Exception:
        return None
