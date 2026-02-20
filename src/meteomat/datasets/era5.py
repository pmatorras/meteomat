"""
Download ERA5 daily statistics via CDS API with monthly chunking.
4 requests per month (mean, min, max, sum) — one per statistic group.
"""

import cdsapi, logging
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from meteomat.cfg.config import TRAINING_REGIONS, STAT_REQUESTS, COMMON

logging.getLogger('cdsapi').setLevel(logging.WARNING)

def download_era5_month(
    region_name:   str,
    year:          int,
    month:         int,
    output_dir:    str = "data/era5",
    force_refresh: bool = False,
) -> List[Path]:
    """Download one month of ERA5 daily statistics for a region (4 files)."""
    region      = TRAINING_REGIONS[region_name]
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    c = cdsapi.Client(quiet=False)
    downloaded = []

    for stat, stat_cfg in STAT_REQUESTS.items():
        out_file = output_path / f"{region_name}_{year}_{month:02d}_{stat}.nc"

        if out_file.exists() and not force_refresh:
            downloaded.append(out_file)
            continue

        print(f"  📡 {region_name} {year}-{month:02d} [{stat}]...", end='', flush=True)

        request = {
            **COMMON,
            **stat_cfg,
            'year':  str(year),
            'month': [f'{month:02d}'],
            'day':   [f'{d:02d}' for d in range(1, 32)],
            'area':  region['area'],
        }

        try:
            c.retrieve('derived-era5-single-levels-daily-statistics', request, str(out_file))
            print(f" ✅ ({out_file.stat().st_size / 1e6:.1f} MB)")
            downloaded.append(out_file)
        except Exception as e:
            print(f" ❌ {e}")
            if out_file.exists():
                out_file.unlink()
            raise

    return downloaded


def download_era5_region_year(
    region_name:   str,
    year:          int,
    output_dir:    str = "data/era5",
    force_refresh: bool = False,
) -> List[Path]:
    """Download full year for one region (12 months x 4 stats = 48 files)."""
    print(f"\n📥 {TRAINING_REGIONS[region_name]['name']} - {year}")
    files = []
    for month in range(1, 13):
        files += download_era5_month(region_name, year, month, output_dir, force_refresh)
    print(f"  ✅ {len(files)} files downloaded")
    return files


def download_all_regions_parallel(
    year:          int = 2023,
    regions:       Optional[List[str]] = None,
    output_dir:    str = "data/era5",
    max_workers:   int = 5,
    force_refresh: bool = False,
) -> dict:
    """Download all regions in parallel."""
    regions = regions or list(TRAINING_REGIONS.keys())
    n_files = len(regions) * 12 * len(STAT_REQUESTS)
    print(f"🚀 CDS Download: {len(regions)} regions x {year}")
    print(f"   Requests: {n_files} total ({len(STAT_REQUESTS)} stats x 12 months x {len(regions)} regions)")
    print(f"   Workers : {max_workers}\n")

    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_region = {
            executor.submit(
                download_era5_region_year, region, year, output_dir, force_refresh
            ): region
            for region in regions
        }
        for future in as_completed(future_to_region):
            region = future_to_region[future]
            try:
                results[region] = future.result()
            except Exception as e:
                print(f"\n❌ {region} failed: {e}")

    print(f"\n{'='*55}")
    print(f"✅ Complete: {len(results)}/{len(regions)} regions")
    return results


if __name__ == "__main__":
    download_all_regions_parallel(year=2023, max_workers=5)
