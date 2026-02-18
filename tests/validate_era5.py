"""
Validate merged ERA5 data has correct structure and reasonable values
"""
import xarray as xr
from pathlib import Path

def validate_file(filepath: Path):
    """Check if ERA5 file has valid data."""
    
    print(f"\n{'='*60}")
    print(f"Validating: {filepath.name}")
    print(f"Size: {filepath.stat().st_size / 1e6:.1f} MB")
    
    try:
        ds = xr.open_dataset(filepath)
        
        # Check dimensions
        print(f"\n📊 Dimensions:")
        for dim, size in ds.sizes.items():
            print(f"   {dim}: {size}")
        
        # Check time coverage
        if 'valid_time' in ds.dims:
            times = ds.valid_time.values
            print(f"\n📅 Time range:")
            print(f"   Start: {times[0]}")
            print(f"   End: {times[-1]}")
            print(f"   Total hours: {len(times)}")
            expected_hours = 365 * 24  # For full year
            if len(times) < expected_hours * 0.95:
                print(f"   ⚠️  Expected ~{expected_hours}, got {len(times)}")
        
        # Check spatial extent
        if 'latitude' in ds.dims and 'longitude' in ds.dims:
            print(f"\n🗺️  Spatial extent:")
            print(f"   Lat: {ds.latitude.min().values:.2f} to {ds.latitude.max().values:.2f}")
            print(f"   Lon: {ds.longitude.min().values:.2f} to {ds.longitude.max().values:.2f}")
            print(f"   Grid points: {len(ds.latitude)} × {len(ds.longitude)}")
        
        # Check variables and sample values
        print(f"\n📈 Variables:")
        for var in ds.data_vars:
            data = ds[var]
            values = data.values
            
            # Get non-NaN stats
            import numpy as np
            valid_values = values[~np.isnan(values)]
            
            if len(valid_values) == 0:
                print(f"   ❌ {var}: ALL NaN!")
                continue
            
            print(f"   {var}:")
            print(f"      Shape: {data.shape}")
            print(f"      Range: {valid_values.min():.2f} to {valid_values.max():.2f}")
            print(f"      Mean: {valid_values.mean():.2f}")
            print(f"      NaN%: {(np.isnan(values).sum() / values.size * 100):.1f}%")
            
            # Sanity checks
            if var == 't2m' or 'temperature' in var:
                if valid_values.min() < 200 or valid_values.max() > 350:
                    print(f"      ⚠️  Temperature out of range (expect 200-350 K)")
            
            if var == 'tp' or 'precipitation' in var:
                if valid_values.min() < 0:
                    print(f"      ⚠️  Negative precipitation!")
        
        ds.close()
        print(f"\n✅ Validation passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return False

if __name__ == "__main__":
    # Validate all 2023 merged files
    data_dir = Path("data/era5")
    
    files = sorted(data_dir.glob("*_2023.nc"))
    
    if not files:
        print("❌ No merged files found!")
        print("Expected files like: region_2023.nc")
    else:
        print(f"Found {len(files)} files to validate\n")
        
        results = {}
        for f in files:
            results[f.name] = validate_file(f)
        
        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        for name, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"{status} {name}")
