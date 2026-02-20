import numpy as np
import pandas as pd
import xarray as xr
import zipfile
from pathlib import Path

# ── Point this at ONE file ────────────────────────────────────────
TEST_FILE   = Path(r"C:\Users\pablo\Documents\Github\meteomat\data\era5\sistema_central_2025_12.nc")
STATION_LAT = 40.958
STATION_LON = 0.871

# ── Auto-unzip if needed ──────────────────────────────────────────
def detect_format(path):
    with open(path, "rb") as f:
        header = f.read(4)
    if header == b"PK\x03\x04": return "zip"
    if header == b"GRIB":        return "grib"
    if header == b"\x89HDF":     return "netcdf4"
    if header[:3] == b"CDF":     return "netcdf3"
    return "unknown"

fmt = detect_format(TEST_FILE)
if fmt == "zip":
    with zipfile.ZipFile(TEST_FILE) as z:
        inner_name = z.namelist()[0]
        z.extract(inner_name, TEST_FILE.parent)
        TEST_FILE = TEST_FILE.parent / inner_name
        fmt = detect_format(TEST_FILE)

engine = {"grib": "cfgrib", "netcdf3": "scipy"}.get(fmt, "netcdf4")
ds = xr.open_dataset(TEST_FILE, engine=engine)

print(f"Format : {fmt} | Engine: {engine}")
print(f"Vars   : {list(ds.data_vars)}")
print(f"Coords : {list(ds.coords)}")
print(f"Dims   : {dict(ds.sizes)}\n")

# ── TEST 1: Precipitation type ────────────────────────────────────
tp_var = next((v for v in ds.data_vars if "tp" in v or "precip" in v.lower()), None)
if tp_var:
    tp = ds[tp_var].values.ravel()
    tp = tp[~np.isnan(tp)]
    n_neg = (np.diff(tp) < -1e-6).sum()
    print(f"[T1] Precip — negatives after diff: {n_neg}",
          "→ accumulated, use .diff().clip(0)" if n_neg else "→ hourly rates, sum directly")
else:
    print(f"[T1] No precip variable found. Vars: {list(ds.data_vars)}")

# ── TEST 2: Timezone ──────────────────────────────────────────────
times = pd.to_datetime(ds["valid_time"].values[:3])
print(f"[T2] First timestamps: {list(times)}")
print("     ⚠ No tz — assumed UTC, shift +1h for CET" if times.tz is None else f"     ✓ tz={times.tz}")

# ── TEST 3: Grid cell distance ────────────────────────────────────
lat_name = "latitude" if "latitude" in ds.coords else "lat"
lon_name = "longitude" if "longitude" in ds.coords else "lon"
nlat = ds[lat_name].values[np.argmin(np.abs(ds[lat_name].values - STATION_LAT))]
nlon = ds[lon_name].values[np.argmin(np.abs(ds[lon_name].values - STATION_LON))]
dist = np.sqrt(((nlat - STATION_LAT) * 111)**2 +
               ((nlon - STATION_LON) * 111 * np.cos(np.radians(STATION_LAT)))**2)
print(f"[T3] Nearest cell: ({nlat:.3f}, {nlon:.3f}) — {dist:.1f} km away",
      "✓" if dist < 30 else "⚠ >30km")
