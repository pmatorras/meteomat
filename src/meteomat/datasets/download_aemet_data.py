"""
download_aemet_historical.py
Downloads daily AEMET data for all stations in aemet_stations_by_region.json
"""
import requests
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
STATIONS_FILE = Path("data/aemet_stations_by_region.json")
#STATIONS_FILE = Path("data/mediterranean.json")
OUTPUT_DIR = Path("data/aemet_daily")
START_DATE = "2010-01-01"  # Adjust as needed
END_DATE = "2025-12-31"
MAX_DAYS_PER_REQUEST = 66  # AEMET limitation

def download_daily_data(indicativo, start_date, end_date, retry=0):
    """Download daily data for a station between dates"""
    api_key = os.getenv("AEMET_API_KEY")
    if not api_key:
        raise ValueError("AEMET_API_KEY not set!")

    headers = {"api_key": api_key}
    endpoint = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{start_date}T00:00:00UTC/fechafin/{end_date}T23:59:59UTC/estacion/{indicativo}"

    try:
        response = requests.get(endpoint, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()

        if data.get("estado") == 429:
            print(f"    Rate limited! Waiting 15s...")
            time.sleep(15)
            if retry < 3:
                return download_daily_data(indicativo, start_date, end_date, retry + 1)
            return None

        if data.get("estado") == 404:
            return None

        if data.get("estado") == 200:
            data_url = data["datos"]
            time.sleep(15)  # 15s between each API call

            # Retry fetching data URL up to 3 times
            for attempt in range(3):
                try:
                    weather_response = requests.get(data_url, timeout=30)
                    weather_response.raise_for_status()
                    return weather_response.json()
                except Exception as e:
                    if attempt < 2:
                        print(f"    Retry {attempt + 1}/3 fetching data URL: {e}")
                        time.sleep(10)
            return None
        else:
            return None

    except Exception as e:
        print(f"    Error fetching data for {indicativo} ({start_date} to {end_date}): {e}")
        return None
    
    

def download_station_all_years(station_id, start_date_str, end_date_str):
    """Download all data for a station"""
    all_data = []
    
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    end = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    current = start
    chunk_num = 0
    total_chunks = (end - start).days // MAX_DAYS_PER_REQUEST + 1
    
    print(f"    Downloading {total_chunks} chunks ({MAX_DAYS_PER_REQUEST} days each)...")
    
    while current < end:
        chunk_end = min(current + timedelta(days=MAX_DAYS_PER_REQUEST), end)
        chunk_num += 1
        
        print(f"    [{chunk_num}/{total_chunks}] {current.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}...", end=" ", flush=True)
        
        data = download_daily_data(
            station_id,
            current.strftime("%Y-%m-%d"),
            chunk_end.strftime("%Y-%m-%d")
        )
        
        if data:
            all_data.extend(data)
            print(f"✓ {len(data)} records (total: {len(all_data)})")
        else:
            print("✗ no data")
        
        current = chunk_end + timedelta(days=1)
    
    return all_data



def download_aemet(sel_regions='all', force_refresh=False):
    # Load stations
    with open(STATIONS_FILE, 'r', encoding='utf-8') as f:
        all_regions = json.load(f)
    
    # Filter regions based on selection
    if sel_regions == 'all':
        regions = all_regions
    else:
        # Handle both single string and list
        if isinstance(sel_regions, str):
            sel_regions = [sel_regions]
        
        regions = {}
        for region_key in sel_regions:
            if region_key in all_regions:
                regions[region_key] = all_regions[region_key]
            else:
                print(f"Warning: Region '{region_key}' not found in stations file")
                print(f"Available regions: {list(all_regions.keys())}")
        
        if not regions:
            raise ValueError("No valid regions selected!")
    
    # Count total stations
    total_stations = sum(len(stations) for stations in regions.values())
    print(f"Selected regions: {list(regions.keys())}")
    print(f"Starting download for {total_stations} stations")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Output: {OUTPUT_DIR}")
    print()
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    station_count = 0
    failed = []
    
    for region_name, stations in regions.items():
        print(f"\n{'='*60}")
        print(f"REGION: {region_name.upper()} ({len(stations)} stations)")
        print(f"{'='*60}")
        
        region_dir = OUTPUT_DIR / region_name
        region_dir.mkdir(exist_ok=True)
        
        for station in stations:
            station_count += 1
            station_id = station['indicativo']
            station_name = station['nombre']
            
            output_file = region_dir / f"{station_id}.json"
            
            # Skip if already downloaded
            if output_file.exists() and force_refresh is False:
                print(f"[{station_count}/{total_stations}] {station_id} ({station_name}): SKIPPED (already exists)")
                continue
            
            print(f"[{station_count}/{total_stations}] {station_id} ({station_name})")
            
            try:
                data = download_station_all_years(station_id, START_DATE, END_DATE)
                
                if data:
                    # Save data with metadata
                    output = {
                        'metadata': station,
                        'start_date': START_DATE,
                        'end_date': END_DATE,
                        'records_count': len(data),
                        'data': data
                    }
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(output, f, ensure_ascii=False, indent=2)
                    
                    print(f"  ✓ Saved {len(data)} records")
                else:
                    print(f"  ✗ No data available")
                    failed.append((station_id, station_name))
                    
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                failed.append((station_id, station_name))
            
            time.sleep(5)  # Be respectful to AEMET
    
    # Summary
    print(f"\n{'='*60}")
    print("DOWNLOAD COMPLETE")
    print(f"{'='*60}")
    print(f"Total stations: {total_stations}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed stations:")
        for sid, sname in failed:
            print(f"  - {sid}: {sname}")

if __name__ == "__main__":
    download_aemet()
