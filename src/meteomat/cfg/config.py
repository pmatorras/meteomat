from pathlib import Path
TRAINING_REGIONS = {
    "north_coast": {
        "name": "North Coast (Cantabrian)",
        "area": [43.8, -8.5, 43.0, -1.5],  # N, W, S, E
    },
    "mediterranean_coast": {
        "name": "Mediterranean Coast",
        "area": [42.0, -0.5, 37.5, 3.5],
    },
    "pyrenees": {
        "name": "Pyrenees",
        "area": [43.0, -1.5, 42.3, 3.0],
    },
    "sierra_nevada": {
        "name": "Sierra Nevada",
        "area": [37.3, -3.5, 36.8, -2.8],
    },
    "sistema_central": {
        "name": "Sistema Central",
        "area": [41.0, -6.0, 40.3, -3.5],
    }
}

ERA5_VARIABLES = [
    '2m_temperature',
    'total_precipitation',
    '10m_u_component_of_wind',
    '10m_v_component_of_wind',
    'surface_pressure',
    '2m_dewpoint_temperature',
]

STATIONS_CACHE_FILE = Path("data/aemet_stations_by_region.json")
