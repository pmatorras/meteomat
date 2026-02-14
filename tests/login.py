import cdsapi

# This will check if your .cdsapirc is found and valid
client = cdsapi.Client()

print("✓ Credentials loaded successfully")

# Small test retrieve (just 1 day, 1 variable, 1 time point)
client.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'variable': '2m_temperature',
        'year': '2024',
        'month': '01',
        'day': '01',
        'time': '12:00',
        'area': [44, -10, 36, 4],  # Spain only
        'format': 'grib',
    },
    'data/test_download.grib'
)

print("✓ Download successful! API is working.")
