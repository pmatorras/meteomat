"""
Download ERA5 data via CDS API with monthly chunking
Slow but reliable
"""
import cdsapi, logging
from pathlib import Path
from typing import List, Optional
import xarray as xr
from concurrent.futures import ThreadPoolExecutor, as_completed
from meteomat.cfg.config import TRAINING_REGIONS,ERA5_VARIABLES

def download_era5_month(
    region_name: str,
    year: int,
    month: int,
    output_dir: str = "data/era5"
) -> Path:
    """Download one month of ERA5 data for a region."""
    
    region = TRAINING_REGIONS[region_name]
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    month_file = output_path / f"{region_name}_{year}_{month:02d}.nc"
    
    if month_file.exists():
        return month_file
    
    print(f"  📡 {region_name} {year}-{month:02d}...", end='', flush=True)
    logging.getLogger('cdsapi').setLevel(logging.WARNING)
    c = cdsapi.Client(quiet=True)  # Add quiet parameter
    
    request = {
        'product_type': 'reanalysis',
        'format': 'netcdf',
        'variable': ERA5_VARIABLES,
        'year': str(year),
        'month': f'{month:02d}',
        'day': [f'{d:02d}' for d in range(1, 32)],
        'time': '00:00',  # Single time point
        'area': region['area'],
        'data_format': 'netcdf',
        'download_format': 'unarchived',
        'product_type': ['reanalysis'],
    }

    # Then use c.retrieve with daily mean dataset
    c.retrieve('reanalysis-era5-single-levels-monthly-means', request, str(month_file))

    
    try:
        c.retrieve('reanalysis-era5-single-levels', request, str(month_file))
        print(f" ✅ ({month_file.stat().st_size / 1e6:.1f} MB)")
        return month_file
    except Exception as e:
        print(f" ❌ {e}")
        if month_file.exists():
            month_file.unlink()
        raise


def download_era5_region_year(
    region_name: str,
    year: int,
    output_dir: str = "data/era5"
) -> List[Path]:
    """Download full year for one region (12 monthly files)."""
    
    print(f"\n📥 {TRAINING_REGIONS[region_name]['name']} - {year}")
    
    # Download all months
    month_files = []
    for month in range(1, 13):
        month_file = download_era5_month(region_name, year, month, output_dir)
        month_files.append(month_file)
    
    print(f"  ✅ All 12 months downloaded")
    return month_files


def download_all_regions_parallel(
    year: int = 2023,
    regions: Optional[List[str]] = None,
    output_dir: str = "data/era5",
    max_workers: int = 5
):
    """Download all regions in parallel."""
    
    regions = regions or list(TRAINING_REGIONS.keys())
    
    print(f"🚀 CDS Download: {len(regions)} regions × {year}")
    print(f"   Parallel workers: {max_workers}")
    print(f"   Estimated time: ~50 minutes\n")
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_region = {
            executor.submit(download_era5_region_year, region, year, output_dir): region
            for region in regions
        }
        
        for future in as_completed(future_to_region):
            region = future_to_region[future]
            try:
                file_path = future.result()
                results[region] = file_path
            except Exception as e:
                print(f"\n❌ {region} failed: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ Complete: {len(results)}/{len(regions)} regions")
    return results


if __name__ == "__main__":
    # Download all regions for 2023 in parallel
    download_all_regions_parallel(year=2023, max_workers=5)
