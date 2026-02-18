import os, json
import requests
from meteomat.cfg.config import TRAINING_REGIONS, STATIONS_CACHE_FILE

def load_cached_stations():
    """Load stations from cache if exists"""
    if STATIONS_CACHE_FILE.exists():
        with open(STATIONS_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_stations_cache(regions_aemet):
    """Save stations to cache"""
    STATIONS_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATIONS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(regions_aemet, f, indent=2, ensure_ascii=False)
    print(f"Saved stations cache to {STATIONS_CACHE_FILE}")


def parse_aemet_coords(lat_str, lon_str):
    """Convert AEMET format (394924N, 025309E) to decimal degrees"""
    # Remove direction letter
    lat_dir = lat_str[-1]
    lat_str = lat_str[:-1]
    
    lon_dir = lon_str[-1]
    lon_str = lon_str[:-1]
    
    # Latitude: 394924 = 39°49'24"
    lat_deg = int(lat_str[:2])
    lat_min = int(lat_str[2:4])
    lat_sec = int(lat_str[4:6])
    lat = lat_deg + lat_min/60 + lat_sec/3600
    if lat_dir == 'S':
        lat = -lat
    
    # Longitude: 025309 = 02°53'09"
    lon_deg = int(lon_str[:2])
    lon_min = int(lon_str[2:4])
    lon_sec = int(lon_str[4:6])
    lon = lon_deg + lon_min/60 + lon_sec/3600
    if lon_dir == 'W':
        lon = -lon
    
    return lat, lon


def is_station_in_region(lat, lon, region):
    """Check if station is within region bounds"""
    # region["area"] = [N, W, S, E]
    north, west, south, east = region["area"]
    return south <= lat <= north and west <= lon <= east

def get_all_stations():
    """Fetch all AEMET stations"""
    api_key = os.getenv("AEMET_API_KEY")
    headers = {"api_key": api_key}
    
    endpoint = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"
    response = requests.get(endpoint, headers=headers)
    data = response.json()
    
    if data.get("estado") == 200:
        stations_url = data["datos"]
        return requests.get(stations_url).json()
    else:
        raise Exception(f"Error: {data.get('descripcion')}")

def filter_stations_by_regions(force_refresh=False):
    """Filter stations for each training region"""
    # Try loading from cache first
    if not force_refresh:
        cached = load_cached_stations()
        if cached:
            print("Loaded stations from cache")
            return cached
    print("Fetching stations from AEMET API...")
    stations = get_all_stations()
    
    TRAINING_REGIONS_AEMET = {}
    
    for region_key, region_info in TRAINING_REGIONS.items():
        TRAINING_REGIONS_AEMET[region_key] = []
        
        for station in stations:
            try:
                lat, lon = parse_aemet_coords(station['latitud'], station['longitud'])
                
                if is_station_in_region(lat, lon, region_info):
                    TRAINING_REGIONS_AEMET[region_key].append({
                        'indicativo': station['indicativo'],
                        'nombre': station['nombre'],
                        'provincia': station['provincia'],
                        'lat': lat,
                        'lon': lon,
                        'altitud': station['altitud']
                    })
            except Exception as e:
                continue
        
        print(f"{region_key}: {len(TRAINING_REGIONS_AEMET[region_key])} stations")
        
    save_stations_cache(TRAINING_REGIONS_AEMET)
    return TRAINING_REGIONS_AEMET

