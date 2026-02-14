from meteomat.cli.parser import create_parser

def main():
    """Parse arguments and route to command handlers."""
    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()
    
    print("works")


if __name__ == '__main__':
    main()