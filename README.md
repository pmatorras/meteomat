# Meteomat

Interactive weather dashboard providing rainfall forecasts with uncertainty quantification across Europe. Meteomat visualizes ECMWF ensemble forecasts to show probability ranges that standard weather apps hide—answering "how confident is this forecast?" instead of single-value predictions.

**Features:**
- Ensemble-based uncertainty (10th/50th/90th percentiles)
- Interactive map for any European location
- Real-time forecasts via Open-Meteo API
- Location search by city name

**Coming soon:** ML-enhanced downscaling for Spain with orographic corrections

## Usage

1. Search for a city or click anywhere on the map
2. View 7-day ensemble forecast with uncertainty bands
3. Explore how forecast confidence varies over time

## Data Sources
- ECMWF IFS Ensemble forecasts via Open-Meteo
- Geocoding via OpenStreetMap Nominatim

This project is part of Phase 1 (Issues #2-4). Phase 2 will add ML downscaling for Spanish regions.
