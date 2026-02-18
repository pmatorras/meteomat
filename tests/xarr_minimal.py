import xarray as xr

# Minimal config
region = {
    "lat": (36.8, 37.3),
    "lon": (-3.5, -2.8)
}

# Convert lon to 0-360
lon_min = region['lon'][0] + 360
lon_max = region['lon'][1] + 360

# Open dataset
print("Opening dataset...")
ds = xr.open_dataset(
    "https://storage.googleapis.com/gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3",
    engine='zarr',
    chunks=None  # No Dask
)

# Select
print("Selecting region...")
ds_subset = ds.sel(
    latitude=slice(37.3, 36.8),
    longitude=slice(lon_min, lon_max),
    time=slice("2023-01-01", "2023-01-31")  # Just January
)

# Get one variable
print("Loading temperature...")
temp = ds_subset['2m_temperature']
print(f"Shape: {temp.shape}")

# Save
print("Saving...")
temp.to_netcdf("test.nc")
print("Done!")
