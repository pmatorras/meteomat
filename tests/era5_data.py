"""
Standalone test for ERA5 daily statistics
"""
import cdsapi
from pathlib import Path

def test_era5_daily():
    """Download one month of daily data for a small test region."""
    
    # Small test area (Barcelona region)
    test_area = [42, 1, 41, 3]  # [North, West, South, East]
    
    output_file = Path("test_era5_daily.nc")
    
    print("🧪 Testing ERA5 daily statistics download...")
    print(f"   Region: Barcelona area")
    print(f"   Period: January 2023")
    print(f"   Variables: 2m temperature, total precipitation")
    print(f"   Output: {output_file}\n")
    
    c = cdsapi.Client()
    
    request = {
        'product_type': 'reanalysis',
        'variable': [
            '2m_temperature',
            'total_precipitation',
        ],
        'year': '2023',
        'month': '01',
        'day': [f'{d:02d}' for d in range(1, 32)],
        'area': test_area,
        'time_zone': 'utc+00:00',
        'frequency': '1_hourly',
        'daily_statistic': 'daily_mean',
        'format': 'netcdf'
    }
    
    try:
        print("📡 Requesting data from CDS...")
        c.retrieve('derived-era5-single-levels-daily-statistics', request, str(output_file))
        
        print(f"\n✅ Download complete!")
        print(f"   File size: {output_file.stat().st_size / 1e6:.2f} MB")
        
        # Quick check of the data
        import xarray as xr
        ds = xr.open_dataset(output_file)
        print(f"\n📊 Data summary:")
        print(f"   Time points: {len(ds.time)} (should be ~31 days)")
        print(f"   Variables: {list(ds.data_vars)}")
        print(f"   Time range: {ds.time.values[0]} to {ds.time.values[-1]}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_era5_daily()
