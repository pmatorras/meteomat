# Plan: Marine/Sea Tab

## Context
Extend meteomat with coastal sea conditions from the Open-Meteo Marine API, displayed as a second tab alongside the existing weather chart. The app currently has no tabs — single vertical layout, one Plotly figure (4 subplots) in a Streamlit container.

## Phased Approach

### Phase 1 — Data + chart (validate first)
1. Add translation keys to `config.py`
2. Add `fetch_marine_forecast()` to `open_meteo.py`
3. Add `create_marine_dashboard()` to `charts.py`
4. Write `tests/marine.py` to fetch real data and render the chart as HTML — review before integrating

### Phase 2 — App integration (after Phase 1 approved)
5. Add tabs + session state + fetch helper to `app.py`

---

## Files to Modify

| File | Change |
|------|--------|
| `src/meteomat/cfg/config.py` | Add marine translation keys to `LANG` |
| `src/meteomat/datasets/open_meteo.py` | Add `fetch_marine_forecast()` |
| `src/meteomat/viz/charts.py` | Add `create_marine_dashboard()` |
| `src/meteomat/app.py` | Add tabs, session state key, shared fetch helper |

---

## Step 1 — `config.py`: Marine translation keys

Add to both `"en"` and `"es"` dicts in `LANG`:

```python
"tab_weather":    "🌤️ Weather"   / "🌤️ Tiempo"
"tab_sea":        "🌊 Sea"       / "🌊 Mar"
"wave_height":    "Wave Height"  / "Altura de Ola"
"wave_period":    "Wave Period"  / "Período de Ola"
"wave_direction": "Wave Direction" / "Dirección de Ola"
"no_sea_data":    "No sea data available for this location. The marine forecast only covers coastal and offshore areas."
                / "No hay datos marítimos disponibles para esta ubicación. El pronóstico marino solo cubre zonas costeras y mar abierto."
```

---

## Step 2 — `open_meteo.py`: `fetch_marine_forecast()`

```python
def fetch_marine_forecast(location: dict) -> dict | None:
```

- **Endpoint:** `https://marine-api.open-meteo.com/v1/marine`
- **Params:** `latitude`, `longitude`, `forecast_days=7`,
  `hourly="wave_height,wave_direction,wave_period,swell_wave_height,swell_wave_direction,swell_wave_period,wind_wave_height,wind_wave_direction,wind_wave_period"`
- **Returns `None`** for inland locations (API returns HTTP 400) or on any exception.
- Convert API `null` values → `np.nan` before building arrays.

**Return dict on success:**
```python
{
  "dates":                pd.DatetimeIndex,
  "wave_height":          np.ndarray,  # m
  "wave_period":          np.ndarray,  # s
  "wave_direction":       np.ndarray,  # °
  "swell_wave_height":    np.ndarray,  # m
  "swell_wave_period":    np.ndarray,  # s
  "swell_wave_direction": np.ndarray,  # °
  "wind_wave_height":     np.ndarray,  # m
  "wind_wave_period":     np.ndarray,  # s
  "wind_wave_direction":  np.ndarray,  # °
}
```

---

## Step 3 — `charts.py`: `create_marine_dashboard()`

```python
def create_marine_dashboard(data: dict, weather_data: dict, location: dict | None = None, lang: str = "en") -> go.Figure:
```

`weather_data` is the existing ensemble forecast dict — reused to show wind without an extra API call.

**Layout:** `make_subplots(rows=3, cols=1, row_heights=[0.38, 0.28, 0.34], vertical_spacing=0.12)`

### Row 1 — Wave Height (m) + Wave Direction arrows overlaid
| Trace | Color | Width |
|-------|-------|-------|
| Total | `rgb(0, 119, 190)` | 3 solid |
| Swell | `rgb(0, 180, 216)` | 2 solid |
| Wind wave | `rgba(144, 224, 239, 0.85)` | 2 solid |

Wave direction arrows pinned to top of panel: `xref="x1"`, `yref="y1 domain"`, `y=0.97` — same pattern as wind direction in the weather chart. Color `rgb(0, 80, 140)`.

Add one invisible scatter trace (opacity=0) for unified hover: `hovertemplate="<b>Dir:</b> %{text}<extra></extra>"`.

Y-axis: `"m"`, `autorangeoptions=dict(minallowed=0)`

### Row 2 — Wave Period (s)
| Trace | Color | Style |
|-------|-------|-------|
| Total period | `rgb(72, 149, 239)` | solid |
| Swell period | `rgb(144, 190, 109)` | dotted |

Y-axis: `"s"`, `autorangeoptions=dict(minallowed=0)`

### Row 3 — Wind (km/h) + Wind Direction arrows overlaid
Uses `weather_data["wind_median"]`, `weather_data["wind_gusts"]`, `weather_data["wind_direction"]`.
Dates from `weather_data["dates"]` — trim or interpolate to match marine date range if needed.

| Trace | Color | Style |
|-------|-------|-------|
| Wind median | `rgb(0, 204, 150)` | 2 solid |
| Wind gusts | `rgb(0, 150, 100)` | 2 dotted |

Wind direction arrows: `xref="x3"`, `yref="y3 domain"`, `y=0.97`, color `rgb(0, 120, 90)` — identical to weather chart.

Y-axis: `"km/h"`, `autorangeoptions=dict(minallowed=0)`

**Figure settings:** `height=750`, transparent bg, `hovermode="x unified"`, same x-axis `tickformatstops` as weather chart.

---

## Step 4 — `app.py`: Tabs and session state

### 4a — Imports
```python
from meteomat.datasets.open_meteo import fetch_ensemble_forecast, fetch_marine_forecast
from meteomat.viz.charts import create_weather_dashboard, create_marine_dashboard, fig_to_streamlit_html
```

### 4b — Session state
```python
if "marine_fig" not in st.session_state:
    st.session_state.marine_fig = None
```

### 4c — Shared fetch helper
```python
def _fetch_both(location, location_info, lang):
    forecast_data = fetch_ensemble_forecast(location=location)
    st.session_state.forecast_fig = create_weather_dashboard(forecast_data, location_info, lang=lang)
    marine_data = fetch_marine_forecast(location=location)
    st.session_state.marine_fig = (
        create_marine_dashboard(marine_data, forecast_data, location_info, lang=lang) if marine_data else None
    )
```

### 4d — Replace the 4 fetch call sites
Replace all occurrences of `fetch_ensemble_forecast` + `create_weather_dashboard` with `_fetch_both()`:
1. URL param load on startup (lines ~125–130)
2. Search bar (lines ~154–158)
3. Map click (lines ~193–201)
4. Language-change re-render block (lines ~100–106)

### 4e — Wrap `forecast_container` in tabs
```python
tab_weather, tab_sea = st.tabs([t["tab_weather"], t["tab_sea"]])
with tab_weather:
    st.iframe(fig_to_streamlit_html(st.session_state.forecast_fig, lang=lang_code), height=1000)
with tab_sea:
    if st.session_state.marine_fig:
        st.iframe(fig_to_streamlit_html(st.session_state.marine_fig, lang=lang_code), height=800)
    else:
        st.info(t["no_sea_data"])
```

---

## Verification

**Phase 1:** `python tests/marine.py` → opens chart in browser.
- Coastal location (e.g. Santander `lat=43.46, lon=-3.80`) → renders chart.
- Inland location (e.g. Madrid) → prints "No data" and exits gracefully.

**Phase 2:** `streamlit run src/meteomat/app.py`
- Coastal search → Sea tab renders.
- Inland search → Sea tab shows info message.
- Language toggle → both tabs re-render.
- Telegram bot unaffected (only uses `fetch_ensemble_forecast` + `create_weather_dashboard`).
