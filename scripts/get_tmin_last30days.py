"""
get_tmin_last30days.py
Fetches minimum temperature (tmin) for the last 30 days for a given AEMET station.

Usage:
    python get_tmin_last30days.py <station_id>
    python get_tmin_last30days.py 3195
"""
import sys
import os
import requests
from datetime import datetime, timedelta


def fetch_tmin(station_id: str) -> list[dict]:
    api_key = os.getenv("AEMET_API_KEY")
    if not api_key:
        raise ValueError("AEMET_API_KEY environment variable not set")

    end = datetime.today()
    start = end - timedelta(days=30)

    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    endpoint = (
        f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos"
        f"/fechaini/{start_str}T00:00:00UTC"
        f"/fechafin/{end_str}T23:59:59UTC"
        f"/estacion/{station_id}"
    )

    headers = {"api_key": api_key}
    response = requests.get(endpoint, headers=headers, timeout=15)
    response.raise_for_status()

    meta = response.json()
    if meta.get("estado") != 200:
        raise RuntimeError(f"AEMET error: {meta.get('descripcion', meta)}")

    data_response = requests.get(meta["datos"], timeout=15)
    data_response.raise_for_status()

    records = data_response.json()
    return [
        {"fecha": r["fecha"], "tmin": r.get("tmin")}
        for r in records
    ]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_tmin_last30days.py <station_id>")
        sys.exit(1)

    station_id = sys.argv[1]
    print(f"Station: {station_id} — last 30 days minimum temperature\n")

    results = fetch_tmin(station_id)
    print(f"{'Date':<12}  {'Tmin (°C)':>10}")
    print("-" * 26)
    for row in results:
        tmin = row["tmin"] if row["tmin"] is not None else "N/A"
        print(f"{row['fecha']:<12}  {str(tmin):>10}")
