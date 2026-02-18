from meteomat.datasets.open_meteo import fetch_ensemble_forecast
from meteomat.viz.charts import create_weather_dashboard, smart_ticks_js
from pathlib import Path



LOCATION = {'name': 'Santander', 'lat': 43.46, 'lon': 3.82}


if __name__ == '__main__':
    print(f"🌦️  Meteomat Prototype - {LOCATION['name']}\n")
    
    try:
        data = fetch_ensemble_forecast(LOCATION)
        fig = create_weather_dashboard(data, location=LOCATION, add_title=True)
        output_file = 'plot/weather_prototype.html'
        fig.write_html(
            output_file,
            include_plotlyjs="cdn",
            post_script=smart_ticks_js(),
            full_html=True,
        )
        print(f"  ✓ Saved to {output_file}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
