# src/meteomat/app.py
import streamlit as st
import folium, requests
import streamlit.components.v1 as components
from importlib.metadata import version
from streamlit_folium import st_folium
from meteomat.datasets.open_meteo import fetch_ensemble_forecast
from meteomat.viz.charts import create_weather_dashboard, fig_to_streamlit_html  
from meteomat.cfg.config import LANG


query_params = st.query_params
default_lang = query_params.get("lang", "en")
if default_lang not in ["en", "es"]:
    default_lang = "en"

@st.cache_data(ttl=3600)
def geocode_location(query):
    """Convert location name to coordinates using Nominatim"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': query, 'format': 'json', 'limit': 1}
    headers = {'User-Agent': f'Meteomat/{version("meteomat")}'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.ok and response.json():
            result = response.json()[0]
            return float(result['lat']), float(result['lon']), result['display_name']
    except:
        pass
    return None, None, None
st.set_page_config(page_title="Meteomat", layout="wide")
col1, col2 = st.columns([6, 1])

with col2:
    default_idx = 0 if default_lang == "en" else 1
    lang = st.selectbox("🌐", ["🇬🇧 EN", "🇪🇸 ES"], index=default_idx, label_visibility="collapsed", key="lang_selector")
    lang_code = "en" if "EN" in lang else "es"

# Update URL when language changes
if lang_code != default_lang:
    st.query_params["lang"] = lang_code
    # Regenerate chart with new language if location exists
    if st.session_state.last_location and st.session_state.forecast_fig:
        lat, lon = st.session_state.last_location
        location = {"Name": st.session_state.location_name or "", "lat": lat, "lon": lon}
        forecast_data = fetch_ensemble_forecast(location=location)
        location_info = {"name": st.session_state.location_name or f"{lat:.2f}°N, {lon:.2f}°E"}
        st.session_state.forecast_fig = create_weather_dashboard(forecast_data, location_info, lang=lang_code)
    st.rerun()


t = LANG[lang_code]
with col1:
    st.title(t["title"])

# Initialize session state
if 'last_location' not in st.session_state:
    st.session_state.last_location = None
if 'forecast_fig' not in st.session_state:
    st.session_state.forecast_fig = None
if 'map_center' not in st.session_state:
    st.session_state.map_center = [45.0, 00.0]
if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 5
if 'location_name' not in st.session_state:
    st.session_state.location_name = None

# Create placeholder for forecast at the top
forecast_container = st.container()

#Search bar
st.markdown(f'### 🔍 {t["location_search"]}')
search_query = st.text_input(
    "Search location", 
    placeholder="e.g., Madrid, Tokyo, Paris...",
    label_visibility="collapsed"
)
if search_query and len(search_query) > 2:
    lat, lon, name = geocode_location(search_query)
    if lat and lon:
        current_location = (round(lat, 4), round(lon, 4))
        if current_location != st.session_state.last_location:
            st.session_state.last_location = current_location
            st.session_state.location_name = name.split(',')[0]
            st.session_state.map_center = [lat, lon]
            st.session_state.map_zoom = 10
            with st.spinner("Fetching forecast..."):
                location = {"Name": search_query, "lat": lat, "lon": lon}
                forecast_data = fetch_ensemble_forecast(location=location)
                location_info = {'name': name.split(',')[0]}
                st.session_state.forecast_fig = create_weather_dashboard(forecast_data, location_info, lang=lang_code)

# Map goes below
st.markdown("---")

m = folium.Map(
    location=st.session_state.map_center,
    zoom_start=st.session_state.map_zoom,
    tiles="OpenStreetMap"
)
if st.session_state.last_location:
    folium.Marker(st.session_state.last_location, icon=folium.Icon(color='red')).add_to(m)

map_data = st_folium(m, width="100%", height=600)

# Check if location actually changed
if map_data and map_data.get('last_clicked'):
    lat = map_data['last_clicked']['lat']
    lon = map_data['last_clicked']['lng']
    current_location = (round(lat, 4), round(lon, 4))

    # Only fetch and create chart if location changed
    if current_location != st.session_state.last_location:
        st.session_state.last_location = current_location
        st.session_state.location_name = None  # No name for map clicks

        with st.spinner("Fetching ensemble forecast..."):
            location = {"Name": "", "lat": lat, "lon": lon}
            forecast_data = fetch_ensemble_forecast(location=location)
            location_info = {'name': f'{lat:.2f}°N, {lon:.2f}°E'}
            
            # Create and cache the figure
            st.session_state.forecast_fig = create_weather_dashboard(
                forecast_data, 
                location_info,
                lang=lang_code
            )

# Display cached forecast
if st.session_state.forecast_fig is not None:
    with forecast_container:
        lat, lon = st.session_state.last_location
        if st.session_state.location_name:
            st.markdown(f"## 📍 {st.session_state.location_name} ({lat:.2f}°N, {lon:.2f}°E)")
        else:
            st.markdown(f"## 📍 {lat:.2f}°N, {lon:.2f}°E")        
        # Display cached figure (no recreation)
        html = fig_to_streamlit_html(st.session_state.forecast_fig, lang=lang_code)
        components.html(html, height=1000, scrolling=False)
        #st.plotly_chart(st.session_state.forecast_fig, width='stretch', theme="streamlit")
        st.markdown("---")
