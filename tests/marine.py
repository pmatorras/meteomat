"""Quick visual test for the marine forecast fetch + chart."""
import sys
import webbrowser
import tempfile, os

sys.path.insert(0, "src")

from meteomat.datasets.open_meteo import fetch_marine_forecast, fetch_ensemble_forecast
from meteomat.viz.charts import create_marine_dashboard, fig_to_streamlit_html

COASTAL = {"Name": "Santander", "lat": 43.46, "lon": -3.80}
INLAND  = {"Name": "Madrid",    "lat": 40.42, "lon": -3.70}

def test(location):
    print(f"\n--- {location['Name']} ---")
    marine_data = fetch_marine_forecast(location)
    if marine_data is None:
        print("  → No marine data (expected for inland locations)")
        return
    weather_data = fetch_ensemble_forecast(location=location)
    fig = create_marine_dashboard(marine_data, weather_data, location)
    html = fig_to_streamlit_html(fig)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        path = f.name
    print(f"  → Chart saved to {path}")
    webbrowser.open(f"file://{path}")

test(COASTAL)
test(INLAND)
