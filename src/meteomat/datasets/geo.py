import json
import logging
import urllib.request
from functools import lru_cache

from shapely.geometry import Point, shape
from shapely.ops import unary_union

logger = logging.getLogger(__name__)

_LAND_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector"
    "/master/geojson/ne_50m_land.geojson"
)


@lru_cache(maxsize=1)
def _land_geometry():
    """Download Natural Earth 110m land polygons once and cache in memory."""
    try:
        with urllib.request.urlopen(_LAND_URL, timeout=10) as r:
            fc = json.loads(r.read())
        geoms = [shape(f["geometry"]) for f in fc["features"]]
        return unary_union(geoms)
    except Exception as e:
        logger.warning(f"Could not load coastline data: {e}")
        return None


def is_coastal(lat: float, lon: float, threshold_km: float = 10.0) -> bool:
    """Return True if location is within threshold_km of the coastline.

    Fails open: returns True (show marine tab) if coastline data cannot be loaded,
    so a network hiccup never silently hides sea data for coastal cities.
    """
    land = _land_geometry()
    if land is None:
        print("  ⚠️  Coastline data unavailable — defaulting to coastal")
        return True

    point = Point(lon, lat)
    dist_deg = point.distance(land.boundary)
    dist_km = dist_deg * 111.0
    print(f"  🌍 Distance to coast: {dist_km:.1f} km → {'coastal' if dist_km < threshold_km else 'inland'}")
    return dist_km < threshold_km
