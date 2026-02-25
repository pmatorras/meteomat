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
    

    print(f"DEBUG: lang parameter = {lang}")
    print(f"DEBUG: LANG in JS = {smart_ticks[smart_ticks.find('const LANG'):smart_ticks.find('const LANG')+50]}")
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
        vertical_spacing=0.08,
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
    
    # Wind direction arrows
    arrow_interval = max(1, len(dates) // 12)
    for i in range(0, len(dates), arrow_interval):
        arrow = direction_to_arrow(data['wind_direction'][i])
        y_pos = data['wind_gusts'][i]+16
        fig.add_annotation(
            x=dates[i], y=y_pos, text=arrow, showarrow=False,
            font=dict(size=16, color='rgb(0, 120, 90)'),
            xref='x3', yref='y3', xanchor='center', yanchor='middle'
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
    fig.update_xaxes(title_text=t["date"], row=4, col=1)
    
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
        rangemode='nonnegative',  # Keeps it above 0 but no tick at 0
        range=[0.01, None] 
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
    )
    return fig
