# src/meteomat/app.py
import streamlit as st
import folium
from streamlit_folium import st_folium
from meteomat.datasets.fetch import fetch_ensemble_forecast
from meteomat.viz.charts import create_weather_dashboard

st.set_page_config(page_title="Meteomat", layout="wide")

st.title("🌦️ Meteomat - European Weather Forecasts")

# Initialize session state
if 'last_location' not in st.session_state:
    st.session_state.last_location = None
if 'forecast_fig' not in st.session_state:
    st.session_state.forecast_fig = None

# Create placeholder for forecast at the top
forecast_container = st.container()

# Map goes below
st.markdown("### 🗺️ Select Location")
st.markdown("Click anywhere on the map to see the 7-day ensemble forecast")

m = folium.Map(
    location=[50.0, 10.0],
    zoom_start=4,
    tiles="OpenStreetMap"
)

map_data = st_folium(m, width=1400, height=500)

# Check if location actually changed
if map_data and map_data.get('last_clicked'):
    lat = map_data['last_clicked']['lat']
    lon = map_data['last_clicked']['lng']
    current_location = (round(lat, 4), round(lon, 4))
    
    # Only fetch and create chart if location changed
    if current_location != st.session_state.last_location:
        st.session_state.last_location = current_location
        
        with st.spinner("Fetching ensemble forecast..."):
            location = {"Name": "", "lat": lat, "lon": lon}
            forecast_data = fetch_ensemble_forecast(location=location)
            location_info = {'name': f'{lat:.2f}°N, {lon:.2f}°E'}
            
            # Create and cache the figure
            st.session_state.forecast_fig = create_weather_dashboard(
                forecast_data, 
                location_info
            )

# Display cached forecast
if st.session_state.forecast_fig is not None:
    with forecast_container:
        lat, lon = st.session_state.last_location
        st.markdown(f"## 📍 Forecast for: {lat:.2f}°N, {lon:.2f}°E")
        
        # Display cached figure (no recreation)
        st.plotly_chart(st.session_state.forecast_fig, width='stretch', theme="streamlit")
        st.markdown("---")
else:
    with forecast_container:
        st.info("👇 Click anywhere on the map below to see the forecast")
