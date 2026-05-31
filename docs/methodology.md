# Forecast Methodology

<!-- BEGIN:description -->
Meteomat shows probabilistic weather forecasts anywhere in the world. Instead of a single number, it shows a range of likely outcomes so you can see not just what is most likely, but how confident the forecast is.
<!-- END:description -->

It is powered by ECMWF, the European Centre for Medium-Range Weather Forecasts, which produces what is widely considered the world's best operational weather model.

---

## How to read the charts

Each chart shows a **central line** (the best estimate) surrounded by a **shaded band**. The band spans the 10th to 90th percentile of the forecast ensemble — meaning there is an 80% chance the true value falls within it. A narrow band means a confident forecast; a wide band means high uncertainty.

- **Rainfall** uses a square-root y-axis so that small amounts (drizzle) remain visible without large amounts dominating the chart.
- **Wind and wave direction** is shown as arrows anchored to the top of each panel.
- **All panels share the same time axis** — zoom or pan one and the rest follow.

---

## Data Sources

Weather forecasts combine two ECMWF land products, while a third is used for the wave and sea surface temperature data. They are both accessed via the [Open-Meteo](https://open-meteo.com) API at native resolution:

<!-- BEGIN:sources -->
| Product | Resolution | Members | Horizon |
|---|---|---|---|
| **ECMWF IFS Ensemble (EPS)** | ~18 km | 51 perturbed runs | 7 days |
| **ECMWF IFS HRES** | ~9 km | 1 deterministic run | 7 days |
| **ECMWF Wave Model** | ~28 km | — | 7 days |
<!-- END:sources -->

Both IFS products share the same model physics and initial conditions. The ensemble samples uncertainty by perturbing the initial atmospheric state 51 times; HRES is the single highest-resolution deterministic run from the same system. ECMF Wave model is only shown for coastal locations.

---

## Weather Variables

### Uncertainty bands (10th–90th percentile)
For each variable, the shaded area represents the range between the 10th and 90th percentile across the 51 ensemble members. This means there is an 80% probability that the true value falls within the shaded band.

### Temperature
- **Best estimate (line)**: ECMWF HRES value, shifted from the ensemble median.
- **Uncertainty bands**: Ensemble 10th/90th percentiles, shifted by the same offset as the median, so the best estimate always sits at the same relative position within the band.

### Wind speed & gusts
- **Best estimate (line)**: ECMWF HRES value, shifted from the ensemble median.
- **Uncertainty bands**: Ensemble 10th/90th percentiles, shifted by the same offset.
- **Gusts**: Ensemble 90th percentile shifted by the same HRES offset, representing the upper range of expected wind speed.

### Humidity
- **Best estimate (line)**: ECMWF HRES value, shifted from the ensemble median.
- **Uncertainty bands**: Ensemble 10th/90th percentiles, shifted by the same offset.

---

## Rainfall

Rainfall is treated differently from other variables because its distribution is non-Gaussian (many ensemble members predict zero), and because HRES has a meaningful resolution advantage for detecting localised precipitation features (orographic, coastal, convective).

### Best estimate (line)
An asymmetric blend of the ensemble median and HRES, depending on whether HRES detects rain:

- **When HRES detects rain (> 0.1 mm/h)**: 50% ensemble median + 50% HRES.  
  HRES gets equal weight because its higher resolution makes it more likely to be resolving a real precipitation feature.
- **When HRES detects no rain (≤ 0.1 mm/h)**: 75% ensemble median + 25% HRES.  
  The ensemble leads, but HRES pulls the estimate down — a displacement effect (where the ensemble places rain just over the location) is common, so no-rain from HRES is informative but not conclusive.

### Lower uncertainty band (10th percentile)
Taken directly from the ensemble, unchanged. This correctly reaches zero when a significant fraction of ensemble members predict no rain, giving an honest picture of the chance of dry conditions.

### Upper uncertainty band (90th percentile)
Taken from the ensemble, but raised when HRES predicts more rain than the ensemble median. The rationale: HRES's resolution advantage primarily helps detect precipitation-producing features that coarser ensemble members miss, so it should be able to raise the ceiling of possible rainfall. The upper band is never lowered by HRES.

### Probability of rain
The probability that rainfall exceeds 0.1 mm/h, blended using the same asymmetric weights as the best estimate:

- **When HRES detects rain**: 50% × ensemble probability + 50% × 100%
- **When HRES detects no rain**: 75% × ensemble probability + 25% × 0%

This keeps the displayed probability internally consistent with the displayed amount.

Rainfall amounts are rounded to the nearest 0.1 mm, which reflects the true resolution of the forecast.

---

## Marine Variables

### Wave height, period, and direction
Sourced directly from the Open-Meteo Marine API. Total wave height is the combination of swell and wind-wave components. No post-processing is applied.

### Sea surface temperature (SST)
Sourced from the Open-Meteo Marine API. A 3-hour centred rolling average is applied for visual smoothness. Note that SST reflects the model's boundary condition (typically derived from satellite composites) and may not capture short-lived phenomena such as coastal upwelling, which can cause real surface temperatures to differ by 1–3°C from the forecast.

---

## Limitations

<!-- BEGIN:limitations -->
- **Spatial resolution**: HRES at ~9 km and the ensemble at ~18 km cannot resolve sub-grid features such as valley-scale orography, urban heat islands, or small coastal inlets. Two nearby locations within the same grid cell will receive nearly identical forecasts.
- **Ensemble calibration**: The ECMWF ensemble is one of the best-calibrated probabilistic forecast systems in the world, but calibration is not perfect. Stated probabilities are skill estimates, not guarantees.
- **Rainfall uncertainty**: Precipitation is the hardest variable to forecast deterministically. The blending methodology is a pragmatic combination of two imperfect sources and should be interpreted with appropriate caution.
- **SST and upwelling**: The marine SST forecast does not account for wind-driven upwelling events, which are common along the Cantabrian coast of Spain and can cause surface temperatures significantly colder than the model suggests.
<!-- END:limitations -->
