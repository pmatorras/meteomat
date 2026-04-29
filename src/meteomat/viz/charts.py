import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from importlib import resources
from functools import lru_cache
import plotly.io as pio

@lru_cache
def smart_ticks_js() -> str:
    return (resources.files("meteomat.viz.assets") / "smart_ticks.js").read_text(encoding="utf-8")  # [web:76]

def fig_to_streamlit_html(fig, lang="en") -> str:
    fig.update_xaxes(hoverformat="%b %d, %H:%M", matches="x")
    
    # Generate HTML
    html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
    
    # Extract plot div ID from generated HTML
    import re
    match = re.search(r'id="([^"]+)"', html)
    plot_id = match.group(1) if match else "plotly-div"
    
    # Get smart_ticks.js and replace placeholders
    smart_ticks = smart_ticks_js()
    smart_ticks = smart_ticks.replace("{plot_id}", plot_id)
    smart_ticks = smart_ticks.replace("{lang}", lang)
    
    # Inject script at the end
    return html + f"<script>{smart_ticks}</script>"

def direction_to_cardinal(deg):
    """Convert degrees to cardinal direction (N, NE, E, etc.)"""
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    idx = int(((deg + 22.5) % 360) / 45)
    return directions[idx]


def direction_to_arrow(deg):
    """Convert degrees to arrow symbol"""
    arrows = ['↓', '↙', '←', '↖', '↑', '↗', '→', '↘']
    idx = int(((deg + 22.5) % 360) / 45)
    return arrows[idx]


def create_marine_dashboard(data: dict, weather_data: dict, location: dict | None = None, lang: str = "en") -> go.Figure:
    """3-panel marine chart: wave height (+ direction arrows), wave period, wind."""
    from meteomat.cfg.config import LANG
    t = LANG[lang]

    dates = data["dates"]
    wdates = weather_data["dates"]

    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(t["wave_height"], t["wave_period"], t["wind"]),
        vertical_spacing=0.12,
        row_heights=[0.38, 0.28, 0.34],
    )

    # === WAVE HEIGHT ===
    fig.add_trace(go.Scatter(
        x=dates, y=data["wave_height"],
        line=dict(width=3, color="rgb(0, 119, 190)"),
        showlegend=False, name="Total",
        hovertemplate="<b>Total:</b> %{y:.2f} m<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=data["swell_wave_height"],
        line=dict(width=2, color="rgb(0, 180, 216)"),
        showlegend=False, name="Swell",
        hovertemplate="<b>Swell:</b> %{y:.2f} m<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=data["wind_wave_height"],
        line=dict(width=2, color="rgba(144, 224, 239, 0.85)"),
        showlegend=False, name="Wind wave",
        hovertemplate="<b>Wind wave:</b> %{y:.2f} m<extra></extra>",
    ), row=1, col=1)

    # Wave direction: invisible hover trace + arrows pinned to top of row 1
    fig.add_trace(go.Scatter(
        x=dates,
        y=data["wave_height"],
        mode="markers",
        marker=dict(opacity=0, size=1),
        showlegend=False,
        text=[
            f"{direction_to_cardinal(d)} ({d:.0f}°)" if not np.isnan(d) else "N/A"
            for d in data["wave_direction"]
        ],
        hovertemplate="<b>Wave dir:</b> %{text}<extra></extra>",
        name="",
    ), row=1, col=1)

    arrow_interval = max(1, len(dates) // 12)
    for i in range(0, len(dates), arrow_interval):
        if np.isnan(data["wave_direction"][i]):
            continue
        fig.add_annotation(
            x=dates[i], y=0.97,
            text=direction_to_arrow(data["wave_direction"][i]),
            showarrow=False,
            font=dict(size=16, color="rgb(0, 80, 140)"),
            xref="x", yref="y domain",
            xanchor="center", yanchor="top",
        )

    # === WAVE PERIOD ===
    fig.add_trace(go.Scatter(
        x=dates, y=data["wave_period"],
        line=dict(width=2, color="rgb(72, 149, 239)"),
        showlegend=False, name="Period",
        hovertemplate="<b>Period:</b> %{y:.1f} s<extra></extra>",
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=data["swell_wave_period"],
        line=dict(width=2, color="rgb(144, 190, 109)", dash="dot"),
        showlegend=False, name="Swell period",
        hovertemplate="<b>Swell period:</b> %{y:.1f} s<extra></extra>",
    ), row=2, col=1)

    # === WIND (from weather_data) ===
    fig.add_trace(go.Scatter(
        x=wdates, y=weather_data["wind_90th"],
        fill=None, line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=wdates, y=weather_data["wind_10th"],
        fill="tonexty", fillcolor="rgba(0, 204, 150, 0.15)",
        line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ), row=3, col=1)

    wind_hover = [
        f"{direction_to_cardinal(d)} ({d:.0f}°)" for d in weather_data["wind_direction"]
    ]
    fig.add_trace(go.Scatter(
        x=wdates, y=weather_data["wind_median"],
        line=dict(width=2, color="rgb(0, 204, 150)"),
        showlegend=False, name="Wind",
        text=wind_hover,
        hovertemplate="<b>Wind:</b> %{y:.0f} km/h (%{text})<extra></extra>",
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=wdates, y=weather_data["wind_gusts"],
        line=dict(width=2, color="rgb(0, 150, 100)", dash="dot"),
        showlegend=False, name="Gusts",
        text=wind_hover,
        hovertemplate="<b>Gusts:</b> %{y:.0f} km/h (%{text})<extra></extra>",
    ), row=3, col=1)

    wind_arrow_interval = max(1, len(wdates) // 12)
    for i in range(0, len(wdates), wind_arrow_interval):
        fig.add_annotation(
            x=wdates[i], y=0.97,
            text=direction_to_arrow(weather_data["wind_direction"][i]),
            showarrow=False,
            font=dict(size=16, color="rgb(0, 120, 90)"),
            xref="x3", yref="y3 domain",
            xanchor="center", yanchor="top",
        )

    # Axes
    tick_stops = [
        dict(dtickrange=[None, 86400000], value="%H:%M"),
        dict(dtickrange=[86400000, 604800000], value="%b %d %H:%M"),
        dict(dtickrange=[604800000, None], value="%b %d"),
    ]
    fig.update_xaxes(
        hoverformat="%b %d, %H:%M",
        matches="x",
        range=[dates[0], dates[-1]],
        tickformatstops=tick_stops,
        tickformat="%b %d",
    )
    fig.update_yaxes(title_text="m", row=1, col=1, autorange=True, autorangeoptions=dict(minallowed=0))
    fig.update_yaxes(title_text="s", row=2, col=1, autorange=True, autorangeoptions=dict(minallowed=0))
    fig.update_yaxes(title_text="km/h", row=3, col=1, autorange=True, autorangeoptions=dict(minallowed=0))

    fig.update_layout(
        height=750,
        showlegend=False,
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50, r=20, t=40, b=65),
    )
    return fig


def create_weather_dashboard(data, location=None, add_title=None, lang = "en"):
    """Create visualization with improved rainfall scale"""
    print("\n📊 Creating weather dashboard...")
    from meteomat.cfg.config import LANG
    t = LANG[lang]

    
    dates = data['dates']
    
    # Custom hover text
    wind_hover_text = []
    rain_hover_text = []
    for i in range(len(dates)):
        cardinal = direction_to_cardinal(data['wind_direction'][i])
        deg = data['wind_direction'][i]
        wind_hover_text.append(f"{cardinal} ({deg:.0f}°)")
        rain_hover_text.append(f"{data['rain_probability'][i]:.0f}%")
    
    # RAINFALL TRANSFORMATION: Square root scale for better visibility
    rain_10th_sqrt = np.sqrt(data['rain_10th'])
    rain_median_sqrt = np.sqrt(data['rain_median'])
    rain_90th_sqrt = np.sqrt(data['rain_90th'])
    
    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=(
            t['temperature'],
            t['rainfall'],
            t['wind'],
            t['humidity']
        ),
        vertical_spacing=0.10,
        row_heights=[0.25, 0.25, 0.25, 0.25]
    )
    
    # === TEMPERATURE ===
    fig.add_trace(go.Scatter(
        x=dates, y=data['temp_90th'],
        fill=None, line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=dates, y=data['temp_10th'],
        fill='tonexty', fillcolor='rgba(239, 85, 59, 0.2)',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=dates, y=data['temp_median'],
        line=dict(width=2, color='rgb(239, 85, 59)'),
        showlegend=False,
        name='Temperature',
        hovertemplate='<b>Temp:</b> %{y:.1f}°C<extra></extra>'
    ), row=1, col=1)
    
    # === RAINFALL (Square root scale with raised baseline) ===
    fig.add_trace(go.Scatter(
        x=dates, y=rain_90th_sqrt,
        fill=None, 
        line=dict(width=0, shape='hv'),
        showlegend=False,
        hoverinfo='skip',
        connectgaps=False
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=dates, y=rain_10th_sqrt,
        fill='tonexty', 
        fillcolor='rgba(99, 110, 250, 0.2)',
        line=dict(width=0, shape ='hv'),
        showlegend=False,
        hoverinfo='skip',
        connectgaps=False
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=dates, y=rain_median_sqrt,
        line=dict(width=2, color='rgb(99, 110, 250)', shape='hv'),  # shape='hv' makes it stepped!
        showlegend=False,
        name='Rainfall',
        customdata=data['rain_median'],
        text=rain_hover_text,
        hovertemplate='<b>Rain:</b> %{customdata:.2f} mm (Prob: %{text})<extra></extra>',
        connectgaps=False,
        mode='lines'
    ), row=2, col=1)
    
    # === WIND ===
    fig.add_trace(go.Scatter(
        x=dates, y=data['wind_90th'],
        fill=None, line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ), row=3, col=1)
    
    fig.add_trace(go.Scatter(
        x=dates, y=data['wind_10th'],
        fill='tonexty', fillcolor='rgba(0, 204, 150, 0.15)',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ), row=3, col=1)
    
    fig.add_trace(go.Scatter(
        x=dates, y=data['wind_median'],
        line=dict(width=2, color='rgb(0, 204, 150)'),
        showlegend=False,
        name='Wind',
        text=wind_hover_text,
        hovertemplate='<b>Wind:</b> %{y:.0f} km/h (%{text})<extra></extra>'
    ), row=3, col=1)
    
    fig.add_trace(go.Scatter(
        x=dates, y=data['wind_gusts'],
        line=dict(width=2, color='rgb(0, 150, 100)', dash='dot'),
        showlegend=False,
        name='Gusts',
        text=wind_hover_text,
        hovertemplate='<b>Gusts:</b> %{y:.0f} km/h (%{text})<extra></extra>'
    ), row=3, col=1)
    
    # Wind direction arrows — anchored to the top of the wind subplot (domain coords)
    # so they never inflate the y-axis autorange
    arrow_interval = max(1, len(dates) // 12)
    for i in range(0, len(dates), arrow_interval):
        arrow = direction_to_arrow(data['wind_direction'][i])
        fig.add_annotation(
            x=dates[i], y=0.97, text=arrow, showarrow=False,
            font=dict(size=16, color='rgb(0, 120, 90)'),
            xref='x3', yref='y3 domain', xanchor='center', yanchor='top'
        )
    
    # === HUMIDITY ===
    fig.add_trace(go.Scatter(
        x=dates, y=data['humidity_90th'],
        fill=None, line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ), row=4, col=1)
    
    fig.add_trace(go.Scatter(
        x=dates, y=data['humidity_10th'],
        fill='tonexty', fillcolor='rgba(171, 99, 250, 0.2)',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ), row=4, col=1)
    
    fig.add_trace(go.Scatter(
        x=dates, y=data['humidity_median'],
        line=dict(width=2, color='rgb(171, 99, 250)'),
        showlegend=False,
        name='Humidity',
        hovertemplate='<b>Humidity:</b> %{y:.0f}%<extra></extra>'
    ), row=4, col=1)
    
    # Axis labels
    fig.update_xaxes(
        hoverformat="%b %d, %H:%M",  # Show hours in hover
        matches='x', 
        range=[dates[0], dates[-1]],
        # Dynamic tick formatting based on zoom level
        tickformatstops=[
            dict(dtickrange=[None, 86400000], value="%H:%M"),  # < 1 day apart: show only time
            dict(dtickrange=[86400000, 604800000], value="%b %d %H:%M"),  # 1-7 days: show date + time
            dict(dtickrange=[604800000, None], value="%b %d")  # > 7 days: show only date
        ],
        tickformat="%b %d"  # Default format for full view
    )
    fig.update_xaxes(title_text="", row=1, col=1)
    fig.update_xaxes(title_text="", row=2, col=1)
    fig.update_xaxes(title_text="", row=3, col=1)
    fig.update_xaxes(title_text="", row=4, col=1)
    
    fig.update_yaxes(title_text="°C", row=1, col=1)
    
    # Rainfall: Square root scale with raised minimum (0.05 mm)
    rain_tick_values = [0, 0.1, 0.5, 1, 2, 5, 10, 20]
    fig.update_yaxes(
        title_text="mm/h",
        row=2, col=1,
        tickmode='array',
        tickvals=np.sqrt(rain_tick_values),
        ticktext=['0' if v == 0 else (str(v) if v >= 1 else f'{v:.1f}') for v in rain_tick_values],
        autorange=True,
        autorangeoptions=dict(minallowed=0),
    )
    
    fig.update_yaxes(
        title_text="km/h",
        row=3,
        col=1,
        autorange=True,
        autorangeoptions=dict(minallowed=0),
    )
    fig.update_yaxes(title_text="%", row=4, col=1)
    
    # Link all x-axes for synchronized hover
    fig.update_xaxes(matches='x')
    if add_title:
        fig.update_layout(title=f"Weather Station - {location['name']} (ECMWF Ensemble Forecast)")
    fig.update_layout(
        height=1000,
        showlegend=False,
        hovermode='x unified'
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50, r=20, t=40, b=65)
    )
    return fig
