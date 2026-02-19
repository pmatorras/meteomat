import requests
import os
import time

api_key = os.getenv("AEMET_API_KEY")
headers = {"api_key": api_key}

station = "1152C"

# Check a period where it showed "no data" (2010)
print("Testing 2010 (should be no data):")
endpoint1 = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/2010-01-01T00:00:00UTC/fechafin/2010-01-10T23:59:59UTC/estacion/{station}"
r1 = requests.get(endpoint1, headers=headers)
print(f"Status: {r1.status_code}")
print(f"Response: {r1.json()}")

time.sleep(30)

# Check a period where it showed data (2014)
print("\nTesting 2014 (should have data):")
endpoint2 = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/2014-03-22T00:00:00UTC/fechafin/2014-05-27T23:59:59UTC/estacion/{station}"
r2 = requests.get(endpoint2, headers=headers)
data2 = r2.json()
print(f"Status: {r2.status_code}")
print(f"Response estado: {data2.get('estado')}")
if data2.get('estado') == 200:
    data_url = data2['datos']
    time.sleep(5)
    actual_data = requests.get(data_url).json()
    print(f"Records returned: {len(actual_data)}")
    print(f"First record date: {actual_data[0].get('fecha')}")
    print(f"Last record date: {actual_data[-1].get('fecha')}")
