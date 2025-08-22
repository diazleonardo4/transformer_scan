# providers.py
import time
from typing import Dict, Any, List, Optional
import requests

PROVIDERS: Dict[str, Dict[str, Any]] = {
    "afinia": {
        "url": "https://servicios.energiacaribemar.co/Autogeneracion/WFConsulta.aspx/ListaPuntoConexion",
        "headers": {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "https://servicios.energiacaribemar.co",
            "Referer": "https://servicios.energiacaribemar.co/Autogeneracion/",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "area-scan/1.0",
        },
    },
    "aire": {
        "url": "https://servicios.air-e.com/CREG174/WFConsulta.aspx/ListaPuntoConexion",
        "headers": {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "https://servicios.air-e.com",
            "Referer": "https://servicios.air-e.com/CREG174/",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "area-scan/1.0",
        },
    },
}

def get_provider_cfg(provider: str) -> Dict[str, Any]:
    key = provider.strip().lower()
    if key not in PROVIDERS:
        raise ValueError("provider must be 'afinia' or 'aire'")
    return PROVIDERS[key]

def call_provider(lat: float, lon: float, provider: str, session: Optional[requests.Session] = None,
                  retries: int = 2, timeout: int = 12) -> List[Dict[str, Any]]:
    """
    Calls provider endpoint with:
       {"ObjPuntoConexion":{"P_TIPO_CONSULTA":5,"latitud":"...","longitud":"..."}}
    Returns list under 'd' (possibly empty).
    """
    cfg = get_provider_cfg(provider)
    payload = {"ObjPuntoConexion": {"P_TIPO_CONSULTA": 5, "latitud": f"{lat}", "longitud": f"{lon}"}}
    sess = session or requests.Session()

    for attempt in range(retries + 1):
        try:
            r = sess.post(cfg["url"], headers=cfg["headers"], json=payload, timeout=timeout)
            r.raise_for_status()
            j = r.json()
            return j.get("d", []) or []
        except requests.RequestException:
            if attempt < retries:
                time.sleep(0.6 * (2 ** attempt))
                continue
            return []
