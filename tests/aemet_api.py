import os
import requests

# Load environment variable
api_key = os.getenv("AEMET_API_KEY")

if not api_key:
    raise ValueError("AEMET_API_KEY not found!")

headers = {"api_key": api_key}

# Step 1: Get data URL from a real endpoint
# This gets data from all conventional observation stations
endpoint = "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"

response = requests.get(endpoint, headers=headers)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 200:
    data = response.json()
    
    # Step 2: Get the actual data from the URL AEMET provides
    if data.get("estado") == 200:
        data_url = data["datos"]
        print(f"\nData URL: {data_url}")
        
        # Download the actual weather data
        weather_data = requests.get(data_url)
        print(f"\nWeather Data (first 500 chars):\n{weather_data.text[:500]}")
    else:
        print(f"Error: {data.get('descripcion')}")
else:
    print(f"Error: {response.text}")
