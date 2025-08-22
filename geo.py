# geo.py
import math
from typing import List, Tuple

EARTH_R_M = 6371000.0

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p = math.pi / 180.0
    a = 0.5 - math.cos((lat2 - lat1) * p)/2 + math.cos(lat1*p)*math.cos(lat2*p)*(1 - math.cos((lon2 - lon1)*p))/2
    return 2 * EARTH_R_M * math.asin(math.sqrt(a))

def m2deg_lat(m: float) -> float:
    return (m / EARTH_R_M) * (180.0 / math.pi)

def m2deg_lon(m: float, at_lat_deg: float) -> float:
    return (m / (EARTH_R_M * math.cos(math.radians(at_lat_deg)))) * (180.0 / math.pi)

def circle_bbox(lat0: float, lon0: float, r_m: float) -> Tuple[float, float, float, float]:
    return (
        lat0 - m2deg_lat(r_m),
        lat0 + m2deg_lat(r_m),
        lon0 - m2deg_lon(r_m, lat0),
        lon0 + m2deg_lon(r_m, lat0),
    )

def hex_points_in_circle(lat0: float, lon0: float, radius_m: float, step_m: float) -> List[Tuple[float, float]]:
    """
    Generate hex-grid probe points within a circle of radius_m.
    Row spacing: step * sqrt(3)/2; odd rows offset by half-step in longitude.
    """
    pts: List[Tuple[float, float]] = []
    row_dlat = m2deg_lat(step_m * math.sqrt(3) / 2)
    min_lat, max_lat, min_lon, max_lon = circle_bbox(lat0, lon0, radius_m)

    rlat = min_lat
    row = 0
    while rlat <= max_lat:
        dlon_step = m2deg_lon(step_m, rlat if abs(rlat) < 89.9 else lat0)
        offset = 0.5 * dlon_step if (row % 2 == 1) else 0.0
        rlon = min_lon + offset
        while rlon <= max_lon:
            if haversine_m(lat0, lon0, rlat, rlon) <= radius_m:
                pts.append((rlat, rlon))
            rlon += dlon_step
        rlat += row_dlat
        row += 1
    return pts