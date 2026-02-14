# Meteomat

Interactive weather dashboard providing rainfall forecasts with uncertainty quantification across Europe. Meteomat visualizes ECMWF ensemble forecasts to show probability ranges that standard weather apps hide—answering "how confident is this forecast?" instead of single-value predictions.

**Features:**
- Ensemble-based rainfall uncertainty (10th/50th/90th percentiles)
- Interactive maps for any European location
- Real-time forecasts via Copernicus Climate Data Store
- SQL-powered geospatial queries (DuckDB)

**Coming soon:** ML-enhanced downscaling for Spain with orographic corrections

Built with Python, Streamlit, Folium, and deployed on Hugging Face Spaces.


## Data Sources
- ECMWF ensemble forecasts via Copernicus Climate Data Store
- Weather station data from AEMET (Spain)

This project complies with Copernicus open data attribution requirements.
