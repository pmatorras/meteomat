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
'''
ERA5_VARIABLES = [
    '2m_temperature',
    'total_precipitation',
    '10m_u_component_of_wind',
    '10m_v_component_of_wind',
    'surface_pressure',
    '2m_dewpoint_temperature',
]
'''
ERA5_VARIABLES = {
    'daily_mean': ['2m_temperature', '2m_dewpoint_temperature',
                   '10m_u_component_of_wind', '10m_v_component_of_wind',
                   'surface_pressure'],
    'daily_min':  ['2m_temperature'],
    'daily_max':  ['2m_temperature', '10m_wind_speed'],
    'daily_sum':  ['total_precipitation'],
}
STAT_REQUESTS = {
    'mean': {
        'variable': [
            '2m_temperature',
            '2m_dewpoint_temperature',
            '10m_u_component_of_wind',
            '10m_v_component_of_wind',
            'surface_pressure',
        ],
        'daily_statistic': 'daily_mean',
    },
    'min': {
        'variable': ['2m_temperature'],
        'daily_statistic': 'daily_min',
    },
    'max': {
    'variable': ['2m_temperature', '10m_u_component_of_wind', '10m_v_component_of_wind'],
    'daily_statistic': 'daily_max',
    },
    'sum': {
        'variable': ['total_precipitation'],
        'daily_statistic': 'daily_sum',
    },
}

COMMON = {
    'product_type': 'reanalysis',
    'time_zone':    'utc+01:00',
    'frequency':    '1_hourly',
}

STATIONS_CACHE_FILE = Path("data/aemet_stations_by_region.json")

# At the end of config.py
LANG = {
    "en": {
        "title": "🌦️ Meteomat - European Weather Forecasts",
        "location_search": "Search location",
        "temperature": "Temperature Forecast",
        "rainfall": "Rainfall Forecast",
        "wind": "Wind Speed Forecast (Average, Gusts & Direction)",
        "humidity": "Relative Humidity Forecast",
        "date": "date",
    },
    "es": {
        "title": "🌦️ Meteomat - Pronósticos Meteorológicos Europeos",
        "location_search": "Buscar ubicación",
        "temperature": "Temperatura",
        "rainfall": "Precipitaciones",
        "wind": "Viento / Racha Máxima",
        "humidity": "Humedad Relativa",
        "date": "fecha",
    }
}

