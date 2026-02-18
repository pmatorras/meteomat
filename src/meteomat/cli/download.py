def execute(args):
    """
    Execute evaluate command.
    
    Args:
        args: Parsed command-line arguments with:
            - model_type: 'single' or 'multi'
            - checkpoint: Path to model checkpoint
    """
    year=int(args.year)
    if args.era5:
        from meteomat.datasets.era5 import download_all_regions_parallel
        print(f"\n🧪 Test ERA download ({year})")
        download_all_regions_parallel(year=year, max_workers=5)
    if args.aemet:
        print("Downloading AEMET data")
        from meteomat.datasets.fetch_stations import filter_stations_by_regions
        regions_aemet = filter_stations_by_regions()
        
        # Show examples
        for region, stations in regions_aemet.items():
            print(f"\n{region.upper()}:")
            for station in stations[:3]:  # First 3 stations
                print(f"  - {station['nombre']} ({station['indicativo']}): {station['lat']:.3f}, {station['lon']:.3f}")
     