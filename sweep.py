# sweep.py
from typing import Dict, Any, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from geo import haversine_m, hex_points_in_circle
from providers import call_provider

def _parse_potencia(p) -> Optional[float]:
    if p is None: return None
    try: return float(str(p).replace(",", "."))
    except Exception: return None

def _key(it: Dict[str, Any]) -> Tuple[str, str]:
    return (str(it.get("codigo") or ""), str(it.get("matricula") or ""))

def sweep_area(
    *,
    provider: str,
    center_lat: float,
    center_lon: float,
    radius_m: int,
    step_m: int = 150,
    max_workers: int = 12,
) -> List[Dict[str, Any]]:
    """
    Hex-grid probe sweep. Empty responses are normal. Dedupe by (codigo, matricula).
    Returns sorted list by _dist_m_center and includes normalized _potencia_nominal_kVA.
    """
    probes = hex_points_in_circle(center_lat, center_lon, radius_m, step_m)
    results_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def task(plat: float, plon: float) -> List[Dict[str, Any]]:
        items = call_provider(plat, plon, provider)
        out: List[Dict[str, Any]] = []
        for it in items:
            try:
                ilat = float(it.get("latitud")); ilon = float(it.get("longitud"))
            except (TypeError, ValueError):
                continue
            dist = haversine_m(center_lat, center_lon, ilat, ilon)
            if dist <= radius_m:
                it = dict(it)
                it["_dist_m_center"] = round(dist, 2)
                it["_potencia_nominal_kVA"] = _parse_potencia(it.get("potencia_nominal"))
                out.append(it)
        return out

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for f in as_completed([ex.submit(task, lat, lon) for (lat, lon) in probes]):
            for it in f.result():
                k = _key(it)
                # keep closest duplicate
                if k in results_map:
                    if it["_dist_m_center"] < results_map[k]["_dist_m_center"]:
                        results_map[k] = it
                else:
                    results_map[k] = it

    results = list(results_map.values())
    results.sort(key=lambda x: x["_dist_m_center"])
    return results
