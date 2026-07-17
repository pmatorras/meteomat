#!/usr/bin/env python
"""
Santander minimum temperature anomaly plot.
Compares trailing-30-day min temps vs 2010-2025 historical baseline.
Outputs interactive HTML and LinkedIn-ready PNG.
"""
import json
import os
import requests
import time
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def parse_temp(temp_str):
    """Parse Spanish comma-decimal temperature string to float. Return None if missing."""
    if not temp_str or (isinstance(temp_str, str) and temp_str.strip() == ""):
        return None
    try:
        return float(str(temp_str).replace(",", "."))
    except (ValueError, AttributeError):
        return None


def load_historical_baseline(station_id="1111X"):
    """Load and parse historical tmin data from cached AEMET station."""
    history_file = Path(f"data/aemet_daily/north_coast/{station_id}.json")

    if not history_file.exists():
        raise FileNotFoundError(f"Historical data not found: {history_file}")

    with open(history_file, "r", encoding="utf-8") as f:
        cached = json.load(f)

    metadata = cached.get("metadata", {})

    # Group by (month, day) across all years
    baseline_by_md = defaultdict(list)  # (month, day) -> [tmin, tmin, ...]

    for record in cached.get("data", []):
        fecha = record.get("fecha")
        tmin = parse_temp(record.get("tmin"))

        if not fecha or tmin is None:
            continue

        # Parse YYYY-MM-DD
        try:
            dt = pd.to_datetime(fecha)
            md = (dt.month, dt.day)
            baseline_by_md[md].append(tmin)
        except Exception:
            continue

    # Compute percentiles (10th, 50th/median, 90th) for each day
    baseline = {}
    for md, temps in baseline_by_md.items():
        if temps:
            baseline[md] = {
                "p10": np.percentile(temps, 10),
                "p50": np.percentile(temps, 50),
                "p90": np.percentile(temps, 90),
            }

    return baseline, metadata


def fetch_recent_data(station_id="1111", retry=0):
    """Fetch trailing-30-day min temp data via AEMET API."""
    api_key = os.getenv("AEMET_API_KEY")
    if not api_key:
        raise ValueError("AEMET_API_KEY environment variable not set")

    yesterday = date.today() - timedelta(days=1)
    start = yesterday - timedelta(days=29)

    print(f"Fetching AEMET data for station {station_id}...")
    print(f"  Date range: {start} to {yesterday}")

    start_str = start.strftime("%Y-%m-%d")
    end_str = yesterday.strftime("%Y-%m-%d")

    endpoint = (
        f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos"
        f"/fechaini/{start_str}T00:00:00UTC"
        f"/fechafin/{end_str}T23:59:59UTC"
        f"/estacion/{station_id}"
    )

    headers = {"api_key": api_key}

    try:
        response = requests.get(endpoint, headers=headers, timeout=15)

        if response.status_code == 429:
            if retry < 3:
                wait_time = 15 * (retry + 1)
                print(f"  Rate limited! Waiting {wait_time}s...")
                time.sleep(wait_time)
                return fetch_recent_data(station_id, retry + 1)
            raise RuntimeError("Max retries exceeded for rate limit")

        response.raise_for_status()

        meta = response.json()
        if meta.get("estado") != 200:
            raise RuntimeError(f"AEMET error: {meta.get('descripcion', meta)}")

        data_response = requests.get(meta["datos"], timeout=15)
        data_response.raise_for_status()

        records = []
        for record in data_response.json():
            fecha = record.get("fecha")
            tmin = parse_temp(record.get("tmin"))

            if not fecha or tmin is None:
                continue

            try:
                dt = pd.to_datetime(fecha)
                records.append({"date": dt, "tmin": tmin})
            except Exception:
                continue

        if not records:
            raise ValueError("No valid tmin records found in AEMET response")

        df = pd.DataFrame(records).sort_values("date").reset_index(drop=True)
        return df

    except requests.exceptions.RequestException as e:
        if retry < 3 and "429" in str(e):
            wait_time = 15 * (retry + 1)
            print(f"  Rate limited! Waiting {wait_time}s...")
            time.sleep(wait_time)
            return fetch_recent_data(station_id, retry + 1)
        raise


def build_plot_data(recent_df, baseline):
    """Combine recent data and historical baseline for plotting."""
    plot_data = []

    for _, row in recent_df.iterrows():
        dt = row["date"]
        md = (dt.month, dt.day)
        recent_tmin = row["tmin"]
        hist = baseline.get(md)

        if hist is None:
            continue

        plot_data.append({
            "date": dt,
            "actual": recent_tmin,
            "p10": hist["p10"],
            "p50": hist["p50"],
            "p90": hist["p90"],
        })

    df = pd.DataFrame(plot_data)

    # Smooth the historical baseline with 7-day rolling average
    df["p10"] = df["p10"].rolling(window=7, center=True, min_periods=1).mean()
    df["p50"] = df["p50"].rolling(window=7, center=True, min_periods=1).mean()
    df["p90"] = df["p90"].rolling(window=7, center=True, min_periods=1).mean()

    return df


def create_figure(plot_df, station_name="Station"):
    """Create Plotly figure with actual temps vs historical range."""
    fig = go.Figure()

    # Historical 10th-90th percentile band (upper bound - invisible)
    fig.add_trace(go.Scatter(
        x=plot_df["date"],
        y=plot_df["p90"],
        fill=None,
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))

    # Historical 10th-90th percentile band (lower bound - creates filled area)
    fig.add_trace(go.Scatter(
        x=plot_df["date"],
        y=plot_df["p10"],
        fill="tonexty",
        fillcolor="rgba(99, 110, 250, 0.2)",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))

    # Historical median (50th percentile)
    fig.add_trace(go.Scatter(
        x=plot_df["date"],
        y=plot_df["p50"],
        mode="lines",
        name="2010-2025 Range (10-90%)",
        line=dict(color="rgb(72, 90, 240)", width=2, dash="dash"),
        hovertemplate="<b>%{x|%a, %b %d}</b><br>Baseline: %{y:.1f}°C<extra></extra>",
    ))

    # Actual recent temperatures
    fig.add_trace(go.Scatter(
        x=plot_df["date"],
        y=plot_df["actual"],
        mode="lines",
        name="2026 Actual",
        line=dict(color="rgb(214, 39, 40)", width=3),
        hovertemplate="<b>%{x|%a, %b %d}</b><br>Actual: %{y:.1f}°C<extra></extra>",
    ))

    # Update layout
    fig.update_layout(
        title={
            "text": f"{station_name} Daily Minimum Temperature",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 18},
        },
        xaxis_title="Date",
        yaxis_title="Temperature (°C)",
        hovermode="x unified",
        template="plotly_white",
        width=1200,
        height=600,
        font=dict(size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgb(180, 70, 60)",
            borderwidth=1,
        ),
        margin=dict(l=50, r=20, t=40, b=65),
    )

    # Format x-axis
    fig.update_xaxes(
        tickformat="%a\n%b %d",
        tickangle=0,
        hoverformat="%b %d",
    )

    return fig


def main(station_id="1111X"):
    """Main entry point."""
    # Check API key
    if not os.getenv("AEMET_API_KEY"):
        raise ValueError("AEMET_API_KEY environment variable not set")

    # Create output directory
    output_dir = Path("plot")
    output_dir.mkdir(exist_ok=True)

    # Fetch and process data
    print(f"Loading historical baseline for station {station_id}...")
    baseline, metadata = load_historical_baseline(station_id)
    station_name = metadata.get("nombre", "Station")

    print(f"Fetched {len(baseline)} unique (month, day) baseline averages")

    recent_df = fetch_recent_data(station_id)
    print(f"Retrieved {len(recent_df)} recent temperature records")

    plot_df = build_plot_data(recent_df, baseline)
    print(f"Plotting {len(plot_df)} days with both actual and baseline data")

    # Create and export figure
    fig = create_figure(plot_df, station_name)

    suffix = station_id.lower()
    html_path = output_dir / f"santander_temp_anomaly_{suffix}.html"
    png_path = output_dir / f"santander_temp_anomaly_{suffix}.png"

    print(f"Exporting to {html_path} and {png_path}...")
    fig.write_html(str(html_path))
    fig.write_image(str(png_path), width=1200, height=675, scale=2)

    print(f"✓ Done!")
    print(f"  HTML (interactive): {html_path}")
    print(f"  PNG (LinkedIn-ready): {png_path}")


if __name__ == "__main__":
    import sys
    station_id = sys.argv[1] if len(sys.argv) > 1 else "1111X"
    main(station_id)
