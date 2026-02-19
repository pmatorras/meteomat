import requests
import os
from datetime import datetime, timedelta
import time
import json

def download_daily_data(indicativo, start_date, end_date):
    """Download daily climatological data for a station"""
    api_key = os.getenv("AEMET_API_KEY")
    headers = {"api_key": api_key}
    
    endpoint = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{start_date}T00:00:00UTC/fechafin/{end_date}T23:59:59UTC/estacion/{indicativo}"
    
    print(f"Requesting: {start_date} to {end_date}")
    response = requests.get(endpoint, headers=headers)
    data = response.json()
    
    if data.get("estado") == 200:
        data_url = data["datos"]
        time.sleep(1)
        weather_data = requests.get(data_url).json()
        return weather_data
    else:
        print(f"  Error: {data.get('descripcion')}")
        return None

# Test with one station from mediterranean coast
station = "B013X"  # ESCORCA, LLUC (Mallorca)

# Test recent period first (last 10 days)
end = datetime.now()
start = end - timedelta(days=10)

print(f"Testing station {station}")
print(f"\n1. Recent data ({start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}):")
data = download_daily_data(station, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))

if data:
    print(f"   Records: {len(data)}")
    print(f"   Available fields: {list(data[0].keys())}")
    print(f"   Sample record:\n{json.dumps(data[0], indent=2, ensure_ascii=False)}")

# Now test how far back we can go
print(f"\n2. Testing historical availability:")
for years in [1, 5, 10, 20, 30]:
    test_start = datetime(2024, 1, 1) - timedelta(days=years*365)
    test_end = test_start + timedelta(days=5)
    
    test_data = download_daily_data(station, test_start.strftime("%Y-%m-%d"), test_end.strftime("%Y-%m-%d"))
    if test_data:
        print(f"   ✓ Data available {years} years ago ({test_start.year})")
    else:
        print(f"   ✗ No data {years} years ago ({test_start.year})")
        break
