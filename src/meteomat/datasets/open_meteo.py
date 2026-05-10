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



def fetch_hres_forecast(location: dict) -> dict | None:
    """ECMWF IFS HRES deterministic forecast from Open-Meteo (~9 km, up to 7 days)."""
    print("🎯 Fetching ECMWF HRES from Open-Meteo...")

    url = "https://api.open-meteo.com/v1/ecmwf"
    params = {
        "latitude": location['lat'],
        "longitude": location['lon'],
        "hourly": "temperature_2m,precipitation,wind_speed_10m,wind_direction_10m,relative_humidity_2m",
        "forecast_days": 7,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if not response.ok:
            print(f"  ⚠️  HRES API returned {response.status_code} — skipping")
            return None
        data = response.json()
    except Exception as e:
        print(f"  ⚠️  HRES request failed: {e} — skipping")
        return None

    hourly = data['hourly']
    times = pd.to_datetime(hourly['time'])

    def to_array(key):
        return np.array([v if v is not None else float('nan') for v in hourly[key]], dtype=float)

    result = {
        'dates':        times,
        'temperature':  to_array('temperature_2m'),
        'precipitation': to_array('precipitation'),
        'wind_speed':   to_array('wind_speed_10m'),
        'wind_dir':     to_array('wind_direction_10m'),
        'humidity':     to_array('relative_humidity_2m'),
    }
    print(f"  ✓ HRES: {len(times)} timesteps")
    return result


def merge_hres_ensemble(ensemble: dict, hres: dict | None) -> dict:
    """Merge HRES into ensemble: shift for continuous vars, asymmetric blend for rain."""
    if hres is None:
        return ensemble

    hres_df = pd.DataFrame({
        'temp':     hres['temperature'],
        'precip':   hres['precipitation'],
        'wind':     hres['wind_speed'],
        'wind_dir': hres['wind_dir'],
        'humidity': hres['humidity'],
    }, index=hres['dates'])

    # Align HRES to ensemble timestamps; gaps become NaN and fall back to ensemble
    aligned = hres_df.reindex(ensemble['dates'])

    def blend(hres_col, ens_median):
        return np.where(~np.isnan(hres_col), hres_col, ens_median)

    def shift(median, ens_median, lo, hi, clip_zero=False):
        offset = median - ens_median
        new_lo = lo + offset
        new_hi = hi + offset
        if clip_zero:
            new_lo = np.maximum(new_lo, 0)
            new_hi = np.maximum(new_hi, 0)
        return new_lo, new_hi

    result = dict(ensemble)

    # --- Continuous variables: full HRES shift ---
    temp_med = blend(aligned['temp'].values,     ensemble['temp_median'])
    wind_med = blend(aligned['wind'].values,     ensemble['wind_median'])
    hum_med  = blend(aligned['humidity'].values, ensemble['humidity_median'])
    wind_dir = blend(aligned['wind_dir'].values, ensemble['wind_direction'])

    result['temp_median'],     result['temp_10th'],     result['temp_90th']     = temp_med, *shift(temp_med, ensemble['temp_median'], ensemble['temp_10th'],     ensemble['temp_90th'])
    result['wind_median'],     result['wind_10th'],     result['wind_90th']     = wind_med, *shift(wind_med, ensemble['wind_median'], ensemble['wind_10th'],     ensemble['wind_90th'], clip_zero=True)
    result['humidity_median'], result['humidity_10th'], result['humidity_90th'] = hum_med,  *shift(hum_med,  ensemble['humidity_median'], ensemble['humidity_10th'], ensemble['humidity_90th'])
    result['wind_direction'] = wind_dir
    result['wind_gusts']     = ensemble['wind_gusts'] + (wind_med - ensemble['wind_median'])

    # --- Rain: asymmetric blend so amount and probability stay consistent ---
    # When HRES says rain:    50% ensemble + 50% HRES  (resolution advantage for detecting rain)
    # When HRES says no rain: 75% ensemble + 25% HRES  (ensemble more reliable for displacement)
    hres_precip   = aligned['precip'].values
    hres_available = ~np.isnan(hres_precip)
    hres_rain     = hres_available & (hres_precip > 0.1)
    hres_no_rain  = hres_available & (hres_precip <= 0.1)

    rain_med = ensemble['rain_median'].copy()
    rain_med = np.where(hres_rain,    0.5  * ensemble['rain_median'] + 0.5  * hres_precip, rain_med)
    rain_med = np.where(hres_no_rain, 0.75 * ensemble['rain_median'],                      rain_med)

    ens_prob = ensemble['rain_probability'] / 100.0
    rain_prob = ensemble['rain_probability'].copy()
    rain_prob = np.where(hres_rain,    (0.5  * ens_prob + 0.5)  * 100, rain_prob)
    rain_prob = np.where(hres_no_rain, (0.75 * ens_prob)        * 100, rain_prob)

    # Lower band: keep ensemble unchanged — naturally touches zero when members predict no rain.
    # Upper band: shift up when HRES detects more rain (resolution advantage raises the ceiling).
    rain_offset = np.maximum(rain_med - ensemble['rain_median'], 0)  # only shift up, never down
    result['rain_median']      = rain_med
    result['rain_10th']        = ensemble['rain_10th']
    result['rain_90th']        = np.maximum(ensemble['rain_90th'] + rain_offset, 0)
    result['rain_probability'] = rain_prob

    coverage = hres_available.sum()
    print(f"  ✓ Merged HRES into ensemble ({coverage}/{len(ensemble['dates'])} hours covered by HRES)")
    return result


def fetch_forecast(location: dict) -> dict:
    """Fetch ECMWF ensemble + HRES and merge into a single forecast dict."""
    ensemble = fetch_ensemble_forecast(location=location)
    hres     = fetch_hres_forecast(location)
    return merge_hres_ensemble(ensemble, hres)


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