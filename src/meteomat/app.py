# src/meteomat/app.py
import json
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

# Read URL params: support ?name=ZZ alone, or ?lat=XX&lon=YY&name=ZZ
default_lat = float(query_params["lat"]) if "lat" in query_params else None
default_lon = float(query_params["lon"]) if "lon" in query_params else None
default_name = query_params.get("name", None)


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


@st.cache_data(ttl=3600)
def reverse_geocode(lat, lon):
    """Convert coordinates to a human-readable place name using Nominatim"""
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {'lat': lat, 'lon': lon, 'format': 'json'}
    headers = {'User-Agent': f'Meteomat/{version("meteomat")}'}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.ok and response.json():
            addr = response.json().get('address', {})
            # Prefer the most specific populated place name available
            name = (
                addr.get('city') or
                addr.get('town') or
                addr.get('village') or
                addr.get('hamlet') or
                addr.get('municipality') or
                response.json().get('display_name', '').split(',')[0]
            )
            return name
    except:
        pass
    return None


# If only ?name=ZZ was provided (no lat/lon), resolve coordinates from name
if (default_lat is None or default_lon is None) and default_name:
    _lat, _lon, _ = geocode_location(default_name)
    if _lat and _lon:
        default_lat, default_lon = _lat, _lon
        # Write resolved coords back to URL so bookmarks/shares are complete
        st.query_params["lat"] = str(round(default_lat, 4))
        st.query_params["lon"] = str(round(default_lon, 4))


# helper to notify parent iframe of current state

def notify_parent(lat, lon, lang_code, name=""):
    payload = json.dumps({"lat": lat, "lon": lon, "lang": lang_code, "name": name})
    components.html(f"""
    <script>
    window.top.postMessage({payload}, '*');
    </script>
    """, height=0)


st.set_page_config(page_title="Meteomat", layout="wide")
col1, col2 = st.columns([6, 1])

with col2:
    default_idx = 0 if default_lang == "en" else 1
    lang = st.selectbox("🌐", ["🇬🇧 EN", "🇪🇸 ES"], index=default_idx, label_visibility="collapsed", key="lang_selector")
    lang_code = "en" if "EN" in lang else "es"

# Update URL when language changes
if lang_code != default_lang:
    st.query_params["lang"] = lang_code
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

# Initialize session state and config
if 'last_location' not in st.session_state:
    st.session_state.last_location = (default_lat, default_lon) if default_lat and default_lon else None
if 'forecast_fig' not in st.session_state:
    st.session_state.forecast_fig = None
if 'map_center' not in st.session_state:
    st.session_state.map_center = [default_lat, default_lon] if default_lat and default_lon else [45.0, 0.0]
if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 10 if default_lat else 5
if 'location_name' not in st.session_state:
    st.session_state.location_name = default_name

# If loaded with lat/lon from URL and no forecast yet, fetch it now
if default_lat and default_lon and st.session_state.forecast_fig is None:
    with st.spinner("Fetching forecast..."):
        location = {"Name": default_name or "", "lat": default_lat, "lon": default_lon}
        forecast_data = fetch_ensemble_forecast(location=location)
        location_info = {"name": default_name or f"{default_lat:.2f}°N, {default_lon:.2f}°E"}
        st.session_state.forecast_fig = create_weather_dashboard(forecast_data, location_info, lang=lang_code)

# Create placeholder for forecast at the top
forecast_container = st.container()

# Search bar
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
            st.query_params["lat"] = str(round(lat, 4))
            st.query_params["lon"] = str(round(lon, 4))
            st.query_params["name"] = name.split(',')[0]
            with st.spinner("Fetching forecast..."):
                location = {"Name": search_query, "lat": lat, "lon": lon}
                forecast_data = fetch_ensemble_forecast(location=location)
                location_info = {'name': name.split(',')[0]}
                st.session_state.forecast_fig = create_weather_dashboard(forecast_data, location_info, lang=lang_code)

# Map
st.markdown("---")

m = folium.Map(
    location=st.session_state.map_center,
    zoom_start=st.session_state.map_zoom,
    tiles="OpenStreetMap"
)
if st.session_state.last_location:
    folium.Marker(st.session_state.last_location, icon=folium.Icon(color='red')).add_to(m)

map_data = st_folium(m, width="100%", height=600)

if map_data and map_data.get('last_clicked'):
    lat = map_data['last_clicked']['lat']
    lon = map_data['last_clicked']['lng']
    current_location = (round(lat, 4), round(lon, 4))

    if current_location != st.session_state.last_location:
        st.session_state.last_location = current_location
        # Reverse geocode to get a name for the clicked point
        place_name = reverse_geocode(lat, lon)
        st.session_state.location_name = place_name

        # Always write lat, lon AND name to URL
        st.query_params["lat"] = str(round(lat, 4))
        st.query_params["lon"] = str(round(lon, 4))
        if place_name:
            st.query_params["name"] = place_name
        elif "name" in st.query_params:
            del st.query_params["name"]

        display_name = place_name or f'{lat:.2f}°N, {lon:.2f}°E'
        with st.spinner("Fetching ensemble forecast..."):
            location = {"Name": place_name or "", "lat": lat, "lon": lon}
            forecast_data = fetch_ensemble_forecast(location=location)
            location_info = {'name': display_name}
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
        html = fig_to_streamlit_html(st.session_state.forecast_fig, lang=lang_code)
        components.html(html, height=1000, scrolling=False)
        st.markdown("---")

# Notify parent iframe of current state (for meteo.matorras.com address bar)
if st.session_state.last_location:
    lat, lon = st.session_state.last_location
    notify_parent(lat, lon, lang_code, st.session_state.location_name or "")