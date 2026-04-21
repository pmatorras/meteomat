
# Meteomat
[![Live Dashboard](https://img.shields.io/badge/🌦️_Dashboard-meteo.matorras.com-0ea5e9?style=for-the-badge)](https://meteo.matorras.com)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-2CA5E0?style=for-the-badge&logo=telegram)](https://t.me/meteomat_bot)\
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.54-FF4B4B.svg)
![Plotly](https://img.shields.io/badge/Plotly-6.5-3F4F75.svg)
[![Hugging Face](https://img.shields.io/badge/🤗%20Spaces-pmatorras/meteomat-yellow.svg)](https://huggingface.co/spaces/pmatorras/meteomat)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Live Dashboard:** [meteo.matorras.com](https://meteo.matorras.com) | **Telegram Bot:** [@meteomat_bot](https://t.me/meteomat_bot)

Interactive weather dashboard providing probabilistic forecasts with ensemble uncertainty quantification across Europe. Meteomat visualizes ECMWF ensemble forecasts to show confidence ranges that standard weather apps hide—answering "how confident is this forecast?" instead of single-value predictions.

## Features

- **Ensemble uncertainty visualization**: 10th/50th/90th percentile bands for all forecast variables
- **Multi-variable forecasts**: Temperature, rainfall, wind speed/direction, and humidity
- **Interactive European map**: Click any location or search by city name
- **7-day forecast horizon**: Full week outlook with hourly resolution
- **Real-time data**: ECMWF IFS Ensemble forecasts via Open-Meteo API
- **Telegram bot**: Send a city name or drop a pin to [@meteomat_bot](https://t.me/meteomat_bot) and get a forecast chart instantly

## Usage

**Web:**
1. Visit [meteo.matorras.com](https://meteo.matorras.com)
2. Search for a city or click anywhere on the map
3. View ensemble forecast with uncertainty bands
4. Explore how forecast confidence varies over time and location

**Telegram:**
1. Open [@meteomat_bot](https://t.me/meteomat_bot)
2. Send a city name or drop a location pin
3. Receive a 7-day forecast chart with uncertainty bands

## Installation

```bash
# Clone the repository
git clone https://github.com/pmatorras/meteomat.git
cd meteomat

# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run src/meteomat/app.py
```
## Deployment Architecture

The dashboard is hosted on [Hugging Face Spaces](https://huggingface.co/spaces/pmatorras/meteomat) and served through [meteo.matorras.com](https://meteo.matorras.com) with Cloudflare routing. The page includes an automatic fallback mechanism to ensure availability.

## Tech Stack

- **Frontend**: Streamlit with custom Plotly visualizations and JavaScript theming
- **Data**: ECMWF IFS Ensemble via Open-Meteo API
- **Geocoding**: OpenStreetMap Nominatim
- **Deployment**: Hugging Face Spaces with Docker
- **Telegram bot**: python-telegram-bot v20

## Project Status

### Phase 1: Europe Ensemble Visualization ✅ Complete

- ✅ Repository foundation (#1)
- ✅ ECMWF ensemble data pipeline (#2)
- ✅ Uncertainty visualization with percentile bands (#3)
- ✅ Interactive map interface (#4)
- ✅ API setup (#11)
- ✅ Axes constraints (#20)
- ✅ HF Space Docker deployment (#5)

### Phase 2: ML-Enhanced Downscaling 🚧 In Progress

Spain-focused station-based corrections using AEMET observations:
- Download historical training data (#6)
- Train regional downscaling models (#7)
- Deploy models to Hugging Face Hub (#8)
- Integrate corrections into dashboard (#9)

Target regions: North Coast (Asturias, Cantabria, Basque Country), Mediterranean Coast (Catalonia, Valencia), Pyrenees, Sierra Nevada, Sistema Central

### Future Enhancements

- Native web app to replace HF Space iframe (#18)
- Extension to other European countries

## Data Sources

- ECMWF IFS Ensemble forecasts via [Open-Meteo API](https://open-meteo.com)
- Geocoding via [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org)
- Historical station observations from AEMET (Spain) for Phase 2

## License

MIT License - see [LICENSE](LICENSE) for details.

## Attribution

This project uses ECMWF forecast data accessed through the Open-Meteo API.


