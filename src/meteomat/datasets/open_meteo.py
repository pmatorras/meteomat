import requests
import pandas as pd
import numpy as np


def fetch_marine_forecast(location: dict) -> dict | None:
    """Open-Meteo Marine API — deterministic 7-day hourly sea forecast."""
    print("🌊 Fetching marine forecast from Open-Meteo Marine API...")

    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": location["lat"],
        "longitude": location["lon"],
        "hourly": (
            "wave_height,wave_direction,wave_period,"
            "swell_wave_height,swell_wave_direction,swell_wave_period,"
            "wind_wave_height,wind_wave_direction,wind_wave_period,"
            "sea_surface_temperature"
        ),
        "forecast_days": 7,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if not response.ok:
            print(f"  ⚠️  Marine API returned {response.status_code} — no data for this location")
            return None
        data = response.json()
    except Exception as e:
        print(f"  ⚠️  Marine API request failed: {e}")
        return None

    hourly = data["hourly"]
    times = pd.to_datetime(hourly["time"])

    def to_array(key):
        return np.array([v if v is not None else float("nan") for v in hourly[key]], dtype=float)

    keys = [
        "wave_height", "wave_direction", "wave_period",
        "swell_wave_height", "swell_wave_direction", "swell_wave_period",
        "wind_wave_height", "wind_wave_direction", "wind_wave_period",
        "sea_surface_temperature",
    ]
    result = {"dates": times}
    for k in keys:
        result[k] = to_array(k)

    print(f"  ✓ {len(times)} timesteps, wave height range: {np.nanmin(result['wave_height']):.2f}–{np.nanmax(result['wave_height']):.2f} m")
    return result



def fetch_ensemble_forecast(location=None):
    """
    Open-Meteo: ECMWF ensemble via API
    """
    print("📡 Fetching ECMWF ensemble from Open-Meteo API...")
    
    url = "https://ensemble-api.open-meteo.com/v1/ensemble"
    params = {
        "latitude": location['lat'],
        "longitude": location['lon'],
        "hourly": "temperature_2m,precipitation,wind_speed_10m,wind_direction_10m,relative_humidity_2m",
        "models": "ecmwf_ifs025",
        "forecast_days": 7
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    hourly = data['hourly']
    times = pd.to_datetime(hourly['time'])
    
    # Collect ensemble members
    temp_members = []
    precip_members = []
    wind_members = []
    humidity_members = []
    
    for key in hourly.keys():
        if key.startswith('temperature_2m_member'):
            temp_members.append(hourly[key])
        elif key.startswith('precipitation_member'):
            precip_members.append(hourly[key])
        elif key.startswith('wind_speed_10m_member'):
            wind_members.append(hourly[key])
        elif key.startswith('relative_humidity_2m_member'):
            humidity_members.append(hourly[key])
    
    # Convert to arrays and compute percentiles
    temp_array = np.array(temp_members)
    precip_array = np.array(precip_members)
    wind_array = np.array(wind_members)
    humidity_array = np.array(humidity_members) if humidity_members else None
    
    print(f"  → Found {len(temp_members)} ensemble members")
    print(f"  → {len(times)} timesteps")
    
    # Wind direction
    wind_dir = np.array(hourly.get('wind_direction_10m', [0] * len(times)))
    
    # Calculate probability of rain (% of members with precip > 0.1 mm)
    rain_probability = (np.sum(precip_array > 0.0, axis=0) / precip_array.shape[0]) * 100
    
    results = {
        'dates': times,
        'temp_10th': np.percentile(temp_array, 10, axis=0),
        'temp_median': np.percentile(temp_array, 50, axis=0),
        'temp_90th': np.percentile(temp_array, 90, axis=0),
        'rain_10th': np.percentile(precip_array, 10, axis=0),
        'rain_median': np.percentile(precip_array, 50, axis=0),
        'rain_90th': np.percentile(precip_array, 90, axis=0),
        'rain_probability': rain_probability,
        'wind_10th': np.percentile(wind_array, 10, axis=0),
        'wind_median': np.percentile(wind_array, 50, axis=0),
        'wind_90th': np.percentile(wind_array, 90, axis=0),
        'wind_gusts': np.percentile(wind_array, 90, axis=0) * 1.3,
        'wind_direction': wind_dir,
    }
    
    # Humidity
    if humidity_array is not None:
        results['humidity_10th'] = np.percentile(humidity_array, 10, axis=0)
        results['humidity_median'] = np.percentile(humidity_array, 50, axis=0)
        results['humidity_90th'] = np.percentile(humidity_array, 90, axis=0)
        print(f"  ✓ Using real humidity ensemble data")
    else:
        results['humidity_10th'] = np.full(len(times), 50.0)
        results['humidity_median'] = np.full(len(times), 65.0)
        results['humidity_90th'] = np.full(len(times), 80.0)
        print(f"  ⚠️  No humidity data available, using placeholders")
    
    print(f"  ✓ Computed percentiles and rain probability")
    return results