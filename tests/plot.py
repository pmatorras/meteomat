from meteomat.data.fetch import fetch_ensemble_forecast
from meteomat.viz.charts import create_weather_dashboard



LOCATION = {'name': 'Santander', 'lat': 43.46, 'lon': 3.82}


if __name__ == '__main__':
    print(f"🌦️  Meteomat Prototype - {LOCATION['name']}\n")
    
    try:
        data = fetch_ensemble_forecast(LOCATION)
        dashboard = create_weather_dashboard(data, location=LOCATION)
        print(f"\n✅ SUCCESS! Open {dashboard} in your browser")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
