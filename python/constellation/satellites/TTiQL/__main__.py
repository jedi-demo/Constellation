from constellation.core.logging import setup_cli_logging
from constellation.core.satellite import SatelliteArgumentParser
from .TTiQLSatellite import TTiQLSatellite

def main(args=None):
    parser = SatelliteArgumentParser(description="TTi QL Series II Satellite")
    args = vars(parser.parse_args(args))
    setup_cli_logging(args.pop("level"))

    s = TTiQLSatellite(**args)
    s.run_satellite()

if __name__ == "__main__":
    main()
