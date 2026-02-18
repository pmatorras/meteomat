import xarray as xr
ds = xr.open_dataset('data/era5/sierra_nevada_2023-01-01_2023-12-31.nc')
print(ds)
print(f"\nData variables: {list(ds.data_vars)}")
print(f"Time steps: {len(ds.time)}")
print(f"Lat points: {len(ds.latitude)}")
print(f"Lon points: {len(ds.longitude)}")
