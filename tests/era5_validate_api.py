"""
CDS API field validator — finds which request fields cause 400 errors.
"""
import cdsapi, logging
from pathlib import Path

logging.getLogger('cdsapi').setLevel(logging.WARNING)
c = cdsapi.Client(quiet=True)

DATASET = 'derived-era5-single-levels-daily-statistics'
OUT     = Path("cds_test.nc")

BASE = {
    'product_type':    'reanalysis',
    'variable':        ['2m_temperature'],
    'year':            '2023',
    'month':           '01',
    'day':             ['01', '02'],
    'daily_statistic': 'daily_mean',
    'time_zone':       'utc+00:00',   # ← add back, use UTC as neutral
    'frequency':       '1_hourly',    # ← add back
    'area':            [42, 1, 41, 3],
    'data_format':     'netcdf',
}


def try_request(label, request):
    if OUT.exists(): OUT.unlink()
    try:
        c.retrieve(DATASET, request, str(OUT))
        print(f"  ✅ {label}")
        return True
    except Exception as e:
        print(f"  ❌ {label}")
        return False

print("[1] Base (no timezone, no frequency)")
base_ok = try_request("base", BASE)
if not base_ok:
    print("    Base itself fails — credentials or area issue"); exit(1)

print("\n[2] time_zone variants")
for tz in ["UTC+01:00", "UTC+1:00", "UTC+1", "utc+01:00", "Europe/Madrid"]:
    try_request(tz, {**BASE, 'time_zone': tz})

print("\n[3] frequency field")
for freq in ["1_hourly", "6_hourly"]:
    try_request(freq, {**BASE, 'frequency': freq})

print("\n[4] daily_statistic values")
for stat in ['daily_mean', 'daily_min', 'daily_max', 'daily_sum']:
    try_request(stat, {**BASE, 'daily_statistic': stat})

print("\n[5] total_precipitation + daily_sum")
try_request("tp + daily_sum", {**BASE,
    'variable': ['total_precipitation'],
    'daily_statistic': 'daily_sum',
})

print("\n[6] tp + daily_mean (mixed stat)")
try_request("tp + daily_mean", {**BASE,
    'variable': ['total_precipitation'],
    'daily_statistic': 'daily_mean',
})

if OUT.exists(): OUT.unlink()
