"""Argument parser setup."""
import argparse
from meteomat.cfg.config import TRAINING_REGIONS

valid_regions = list(TRAINING_REGIONS.keys()) + ['all']

def add_common_args(parser):
    """Add arguments common to both training and evaluation."""
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument("-d", "--debug", action="store_true", help="Verbose debug logging")
    parser.add_argument('-r', '--regions', type=str, help='Pick subregions', default='all', choices = valid_regions)

def create_parser():
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog='meteomat',
        description='Meteomat: Weather prediction with uncertainties'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Download
    download = subparsers.add_parser('download', help='Download data')
    download.add_argument('--era5', action='store_true', help='Copernicus ERA5 data')
    download.add_argument('--aemet', action='store_true', help='Download AEMET station data')
    download.add_argument('-f', '--force-refresh', action='store_true', help='Force refresh data')
    download.add_argument('--year', type=int, help='Year (e.g., 2024)', default='2023')
    add_common_args(download)
    return parser