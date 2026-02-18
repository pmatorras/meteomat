"""
Merge ERA5 monthly files into yearly files
Run this after all downloads complete
"""
import zipfile
import xarray as xr
from pathlib import Path
from typing import List

def extract_if_zipped(nc_file: Path) -> Path:
    """Extract NetCDF from zip if needed."""
    try:
        with zipfile.ZipFile(nc_file, 'r') as z:
            # Extract both files (instant and accum)
            temp_dir = nc_file.parent / 'temp'
            temp_dir.mkdir(exist_ok=True)
            
            for name in z.namelist():
                z.extract(name, temp_dir)
            
            # Use the instant file (main data)
            extracted = temp_dir / 'data_stream-oper_stepType-instant.nc'
            if extracted.exists():
                return extracted
            
            # Fallback to first file
            return temp_dir / z.namelist()[0]
            
    except zipfile.BadZipFile:
        # Already extracted NetCDF
        return nc_file

def merge_region_year(region_name: str, year: int, data_dir: str = "data/era5"):
    """Merge 12 monthly files into one yearly file."""
    
    data_path = Path(data_dir)
    monthly_files = sorted(data_path.glob(f"{region_name}_{year}_*.nc"))
    
    if len(monthly_files) != 12:
        print(f"⚠️  {region_name} {year}: Only found {len(monthly_files)}/12 months")
        return None
    
    print(f"📦 Merging {region_name} {year}...")
    
    # Extract all zipped files
    extracted_files = []
    for f in monthly_files:
        extracted = extract_if_zipped(f)
        extracted_files.append(extracted)
    
    # DEBUG - check first file
    test = xr.open_dataset(extracted_files[0], engine='netcdf4')
    print(f"   Dimensions: {list(test.dims)}")
    print(f"   Coords: {list(test.coords)}")
    test.close()
    
    # Merge with explicit concat_dim
    try:
        ds = xr.open_mfdataset(
            extracted_files,
            combine='nested',
            concat_dim='valid_time',  # Try this coordinate
            engine='netcdf4'
        )
        
        output_file = data_path / f"{region_name}_{year}.nc"
        ds.to_netcdf(output_file)
        ds.close()
        
        print(f"✅ {output_file.name} ({output_file.stat().st_size / 1e9:.2f} GB)")
        
        # Cleanup
        temp_dir = data_path / 'temp'
        if temp_dir.exists():
            for f in temp_dir.glob('*'):
                f.unlink()
            temp_dir.rmdir()
        
        return output_file
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

def merge_all(years: List[int] = [2023], regions: List[str] = None):
    """Merge all region-year combinations."""
    
    from meteomat.cfg.config import TRAINING_REGIONS
    
    regions = regions or list(TRAINING_REGIONS.keys())
    
    print(f"🔀 Merging {len(regions)} regions × {len(years)} years\n")
    
    results = {}
    for year in years:
        results[year] = {}
        for region in regions:
            file = merge_region_year(region, year)
            results[year][region] = file
    
    print(f"\n{'='*60}")
    successful = sum(1 for y in results.values() for f in y.values() if f)
    total = len(regions) * len(years)
    print(f"✅ Complete: {successful}/{total} region-years merged")

if __name__ == "__main__":
    # Merge 2023 data
    merge_all(years=[2023])
    
    # When you have more years:
    # merge_all(years=[2020, 2021, 2022, 2023])
