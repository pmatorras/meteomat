"""
ERA5 distribution validator
Checks variable ranges, units, and physical consistency on a real downloaded file.
"""

import zipfile, io
import numpy as np
import xarray as xr
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────
ERA5_DIR  = Path("data/era5")
STAT_FILE = {
    'mean': ERA5_DIR / "mediterranean_coast_2023_01_mean.nc",
    'min':  ERA5_DIR / "mediterranean_coast_2023_01_min.nc",
    'max':  ERA5_DIR / "mediterranean_coast_2023_01_max.nc",
    'sum':  ERA5_DIR / "mediterranean_coast_2023_01_sum.nc",
}

# Expected ranges for Tarragona / Mediterranean coast in January
EXPECTED = {
    't2m':  (-10,  30),   # °C after K→C conversion
    'd2m':  (-10, 20),   # °C, must always be <= t2m
    'u10':  (-20, 20),   # m/s, signed component
    'v10':  (-20, 20),   # m/s, signed component
    'sp':   (85000, 105000),  # Pa
    'tp':   (0, 0.1),    # metres (ERA5 native), ~0–100mm
}

def open_nc(path: Path) -> xr.Dataset:
    with open(path, "rb") as f:
        magic = f.read(4)
    if magic == b"PK\x03\x04":
        with zipfile.ZipFile(path) as z:
            datasets = []
            for name in z.namelist():
                with z.open(name) as f:
                    datasets.append(xr.open_dataset(io.BytesIO(f.read()), engine="h5netcdf"))
            ds = xr.merge(datasets, compat='no_conflicts')  # merge all variables from the ZIP
    else:
        ds = xr.open_dataset(path, engine="netcdf4")
    if 'valid_time' in ds.coords:
        ds = ds.rename({'valid_time': 'time'})
    return ds


def check_var(ds, var, lo, hi, transform=None, label=None):
    if var not in ds:
        print(f"  ⚠  '{var}' not in dataset")
        return
    data = ds[var].values.ravel()
    data = data[~np.isnan(data)]
    if transform:
        data = transform(data)
    vmin, vmax, vmean = data.min(), data.max(), data.mean()
    ok = lo <= vmin and vmax <= hi
    flag = "✅" if ok else "❌"
    label = label or var
    print(f"  {flag} {label:12s}  min={vmin:.3f}  mean={vmean:.3f}  max={vmax:.3f}  "
          f"(expected [{lo}, {hi}])")

print("=" * 60)
print("ERA5 DISTRIBUTION VALIDATOR")
print("=" * 60)

# ── Mean file ─────────────────────────────────────────────────────
print("\n📂 [mean] Variables")
if STAT_FILE['mean'].exists():
    ds_mean = open_nc(STAT_FILE['mean'])
    print(f"   Dims     : {dict(ds_mean.sizes)}")
    print(f"   Variables: {list(ds_mean.data_vars)}")
    time_coord = 'valid_time' if 'valid_time' in ds_mean.coords else 'time'
    ds_mean = ds_mean.rename({time_coord: 'time'})  # normalize for the rest of the script
    print(f"   Time     : {ds_mean.time.values[0]} → {ds_mean.time.values[-1]}\n")
    check_var(ds_mean, 't2m',  -5,  25,      transform=lambda x: x - 273.15, label="t2m (°C)")
    check_var(ds_mean, 'd2m',  -10, 20,      transform=lambda x: x - 273.15, label="d2m (°C)")
    check_var(ds_mean, 'u10',  -20, 20,      label="u10 (m/s)")
    check_var(ds_mean, 'v10',  -20, 20,      label="v10 (m/s)")
    check_var(ds_mean, 'sp',   95000, 103000, label="sp (Pa)")

    # Physical check: dewpoint must always be <= temperature
    if 't2m' in ds_mean and 'd2m' in ds_mean:
        t = ds_mean['t2m'].values.ravel()
        d = ds_mean['d2m'].values.ravel()
        violations = (d > t).sum()
        print(f"\n  {'✅' if violations == 0 else '❌'} dewpoint <= temperature  "
              f"({'no violations' if violations == 0 else f'{violations} violations!'})")
else:
    print("  ⚠  File not found yet — still downloading?")

# ── Min/Max files ─────────────────────────────────────────────────
print(f"\n📂 [min] Variables")
if STAT_FILE['min'].exists():
    ds = open_nc(STAT_FILE['min'])
    print(f"   Variables: {list(ds.data_vars)}")
    check_var(ds, 't2m', -5, 25, transform=lambda x: x - 273.15, label="t2m (°C)")
else:
    print("  ⚠  File not found yet")

# ── Sum file (precipitation) ──────────────────────────────────────
print("\n📂 [sum] Precipitation")
if STAT_FILE['sum'].exists():
    ds_sum = open_nc(STAT_FILE['sum'])
    print(f"   Variables: {list(ds_sum.data_vars)}")
    check_var(ds_sum, 'tp', 0, 0.1, label="tp (m)")

    # Show mm equivalent for intuition
    if 'tp' in ds_sum:
        tp_mm = ds_sum['tp'].values.ravel() * 1000
        print(f"   tp in mm : min={tp_mm.min():.2f}  mean={tp_mm.mean():.2f}  max={tp_mm.max():.2f}")
        zero_days = (tp_mm < 0.1).sum()
        print(f"   Dry days : {zero_days}/{len(tp_mm)} ({100*zero_days/len(tp_mm):.0f}%)"
              f"  {'✅ plausible for Jan' if zero_days > 10 else '⚠ suspiciously wet'}")
else:
    print("  ⚠  File not found yet")

# ── Max file (temperature + wind) ────────────────────────────────
print(f"\n📂 [max] Variables")
if STAT_FILE['max'].exists():
    ds = open_nc(STAT_FILE['max'])
    print(f"   Variables: {list(ds.data_vars)}")
    check_var(ds, 't2m', -10, 30, transform=lambda x: x - 273.15, label="t2m (°C)")
    
    # ── Wind max check ────────────────────────────────────────────
    if 'u10' in ds.data_vars and 'v10' in ds.data_vars:
        u_max = ds['u10'].values.ravel()
        v_max = ds['v10'].values.ravel()
        wspd_max = np.sqrt(u_max**2 + v_max**2)
        wspd_max = wspd_max[~np.isnan(wspd_max)]
        
        print(f"\n  🌬  Wind from u_max/v_max components:")
        print(f"     wspd_max  : min={wspd_max.min():.2f}  mean={wspd_max.mean():.2f}  max={wspd_max.max():.2f} m/s")
        
        # Sanity check: max wind > 50 m/s inland Spain in Jan = suspicious
        if wspd_max.max() > 50:
            print(f"     ❌ Max wind {wspd_max.max():.1f} m/s suspiciously high")
            print(f"        → u_max and v_max likely from different hours")
        elif wspd_max.max() > 35:
            print(f"     ⚠  Max wind {wspd_max.max():.1f} m/s is high but possible (storm)")
        else:
            print(f"     ✅ Max wind range looks plausible for Jan")
            
        # Compare to mean wind if available
        if STAT_FILE['mean'].exists():
            ds_mean = open_nc(STAT_FILE['mean'])
            if 'u10' in ds_mean and 'v10' in ds_mean:
                wspd_mean = np.sqrt(ds_mean['u10']**2 + ds_mean['v10']**2).values.ravel()
                wspd_mean = wspd_mean[~np.isnan(wspd_mean)]
                ratio = wspd_max.mean() / wspd_mean.mean()
                print(f"     Ratio max/mean: {ratio:.2f} (expect 1.5-2.5 for typical days)")
                if ratio > 3:
                    print(f"        ⚠ Ratio > 3 suggests u_max/v_max desync")
else:
    print("  ⚠  File not found yet")

print("\n" + "=" * 60)
