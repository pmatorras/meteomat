"""
Download ERA5 daily statistics via CDS API.
One request per (variable, statistic, year) — annual Spain bbox.
~70 total requests for 7 years vs 1680 original.
"""

import cdsapi
import logging
import xarray as xr
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from meteomat.cfg.config import TRAINING_REGIONS, COMMON

logging.getLogger('cdsapi').setLevel(logging.WARNING)

SPAIN_BOX = [43.8, -8.5, 36.8, 3.5]

# Flattened: one variable per request, annual
VAR_STAT_REQUESTS = [
    ('2m_temperature',              'daily_mean'),
    ('2m_dewpoint_temperature',     'daily_mean'),
    ('10m_u_component_of_wind',     'daily_mean'),
    ('10m_v_component_of_wind',     'daily_mean'),
    ('surface_pressure',            'daily_mean'),
    ('2m_temperature',              'daily_minimum'),
    ('2m_temperature',              'daily_maximum'),
    ('10m_u_component_of_wind',     'daily_maximum'),
    ('10m_v_component_of_wind',     'daily_maximum'),
    ('total_precipitation',         'daily_sum'),
]

def var_stat_label(variable: str, statistic: str) -> str:
    """Short label for filenames, e.g. t2m_mean"""
    var_short = {
        '2m_temperature':             't2m',
        '2m_dewpoint_temperature':    'd2m',
        '10m_u_component_of_wind':    'u10',
        '10m_v_component_of_wind':    'v10',
        'surface_pressure':           'sp',
        'total_precipitation':        'tp',
    }
    stat_short = {
        'daily_mean':    'mean',
        'daily_minimum': 'min',
        'daily_maximum': 'max',
        'daily_sum':     'sum',
    }
    return f"{var_short[variable]}_{stat_short[statistic]}"


def download_era5_var_year(
    variable: str,
    statistic: str,
    year: int,
    output_dir: str = "data/era5",
    force_refresh: bool = False,
) -> Path:
    """Download one (variable, statistic, year) Spain-wide file."""
    label = var_stat_label(variable, statistic)
    out_file = Path(output_dir) / f"spain_{year}_{label}.nc"

    if out_file.exists() and not force_refresh:
        return out_file

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    print(f"  📡 spain {year} [{label}]...", end='', flush=True)

    c = cdsapi.Client(quiet=False)
    request = {
        **COMMON,
        'variable':        [variable],
        'daily_statistic': statistic,
        'year':            str(year),
        'month':           [f'{m:02d}' for m in range(1, 13)],
        'day':             [f'{d:02d}' for d in range(1, 32)],
        'area':            SPAIN_BOX,
    }
    try:
        c.retrieve('derived-era5-single-levels-daily-statistics', request, str(out_file))
        print(f" ✅ ({out_file.stat().st_size / 1e6:.1f} MB)")
    except Exception as e:
        print(f" ❌ {e}")
        if out_file.exists():
            out_file.unlink()
        raise
    return out_file


def extract_regions_from_var_year(
    variable, statistic, year, output_dir="data/era5",
    force_refresh=False, delete_spain=True
):
    label = var_stat_label(variable, statistic)
    spain_file = Path(output_dir) / f"spain_{year}_{label}.nc"

    # Determine which regions still need extraction
    regions_to_extract = {
        name: cfg for name, cfg in TRAINING_REGIONS.items()
        if not (Path(output_dir) / f"{name}_{year}_{label}.nc").exists() or force_refresh
    }

    if not regions_to_extract:
        return  # nothing to do, don't even open the Spain file

    ds = xr.open_dataset(spain_file)
    for region_name, region_cfg in regions_to_extract.items():
        out_file = Path(output_dir) / f"{region_name}_{year}_{label}.nc"
        n, w, s, e = region_cfg['area']
        region_ds = ds.sel(latitude=slice(n, s), longitude=slice(w, e))
        region_ds.to_netcdf(out_file)
    ds.close()

    if delete_spain:
        spain_file.unlink()



def download_and_extract(
    variable: str,
    statistic: str,
    year: int,
    output_dir: str = "data/era5",
    force_refresh: bool = False,
):
    label = var_stat_label(variable, statistic)
    out_dir = Path(output_dir)

    # Skip entirely if all region files already exist
    all_regions_done = all(
        (out_dir / f"{region_name}_{year}_{label}.nc").exists()
        for region_name in TRAINING_REGIONS
    )
    if all_regions_done and not force_refresh:
        print(f"   ⏭️  Skipping {year} [{label}] — all regions exist")
        return

    download_era5_var_year(variable, statistic, year, output_dir, force_refresh)
    extract_regions_from_var_year(variable, statistic, year, output_dir, force_refresh)



def download_all_parallel(
    years: List[int],
    output_dir: str = "data/era5",
    max_workers: int = 10,
    force_refresh: bool = False,
):
    tasks = [(var, stat, y) for var, stat in VAR_STAT_REQUESTS for y in years]

    print(f"🚀 CDS Download: {len(tasks)} requests")
    print(f"   {len(VAR_STAT_REQUESTS)} var/stat combos × {len(years)} years (annual Spain bbox)")
    print(f"   Workers: {max_workers}\n")

    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_and_extract, var, stat, y, output_dir, force_refresh): (var, stat, y)
            for var, stat, y in tasks
        }
        for future in as_completed(futures):
            var, stat, y = futures[future]
            try:
                results[(var, stat, y)] = future.result()
            except Exception as e:
                print(f"\n❌ {var_stat_label(var, stat)} {y} failed: {e}")

    print(f"\n{'='*55}")
    print(f"✅ Complete: {len(results)}/{len(tasks)}")
    return results


if __name__ == "__main__":
    # Test one first
    # download_and_extract('2m_temperature', 'daily_minimum', 2020)

    download_all_parallel(
        years=list(range(2015, 2018)),
        max_workers=5,
    )
