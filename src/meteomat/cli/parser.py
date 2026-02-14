"""Argument parser setup."""
import argparse

def add_common_args(parser):
    """Add arguments common to both training and evaluation."""
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--device', choices=['cpu', 'cuda'], help='Device to use')
    parser.add_argument("-d", "--debug", action="store_true", help="Verbose debug logging")
    parser.add_argument('--model-type', choices=['single', 'multi'], default='multi')
def create_parser():
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog='finsentiment',
        description='Financial sentiment analysis with LLMs'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Evaluate
    euro_map = subparsers.add_parser('map', help='Evaluate a model')
    add_common_args(euro_map)
    return parser