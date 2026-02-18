from meteomat.cli.parser import create_parser
from meteomat.cli import download #, train, evaluate #to implement
def main():
    """Parse arguments and route to command handlers."""
    parser = create_parser()
    args = parser.parse_args()
    print("args", args)
    if args.command == 'download':
        download.execute(args)
    else:
        parser.print_help()
    print("works")


if __name__ == '__main__':
    main()