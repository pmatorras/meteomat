from meteomat.cli.parser import create_parser
from meteomat.cli import download #, train, evaluate #to implement
def main():
    """Parse arguments and route to command handlers."""
    parser = create_parser()
    args = parser.parse_args()
    if args.verbose: print("Running code with args:", args)
    if args.command == 'download':
        download.execute(args)
    else:
        parser.print_help()
    print("The code finished running.")
